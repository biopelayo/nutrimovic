"""Cliente de la API de USDA FoodData Central (FDC) y mapeador a nuestro modelo.

Guía de la API: https://fdc.nal.usda.gov/api-guide

La API key se lee de la variable de entorno ``FDC_API_KEY``. Si no está
definida, el cliente falla con un mensaje claro: nunca inventa datos.

Endpoints usados:
    - Búsqueda:  POST {BASE}/foods/search
    - Detalle:   GET  {BASE}/food/{fdcId}

Mapeo de nutrientes
-------------------
El catálogo canónico (``app.core.nutrients``) guarda en ``usda_ids`` los
identificadores de nutriente de FDC (campo ``nutrient.id`` de cada entrada
``foodNutrients``; p. ej. 1008 = energía kcal, 1003 = proteína). El mapeador
invierte ese catálogo para traducir la respuesta USDA a nuestros ``nutrient_id``.

Estado de medición: si FDC reporta un valor para un nutriente, se marca
``measured`` (incluido un 0 explícito, que es un 0 real medido). Un nutriente
ausente en la respuesta no se añade: quien consulte lo verá como
``not_determined`` por el modelo, nunca como 0.
"""
from __future__ import annotations

import os
import time
from typing import Any

import requests

from app.core.models import DataSource, Food, FoodGroup, FoodState, MeasurementStatus, NutrientValue
from app.core.nutrients import NUTRIENTS

FDC_BASE_URL = "https://api.nal.usda.gov/fdc/v1"
FDC_API_KEY_ENV = "FDC_API_KEY"
DEFAULT_TIMEOUT = 60

# Energía en FDC: 1008 = "Energy" (kcal, factores generales). Muchos alimentos
# Foundation no reportan 1008 y en su lugar dan la energía en kcal calculada con
# factores de Atwater: 2048 = "Energy (Atwater Specific Factors)", 2047 =
# "Energy (Atwater General Factors)". Ambas son energía REAL en kcal publicada
# por USDA (no un dato inventado), solo con otro método de cálculo. Se usan como
# respaldo de energy_kcal cuando 1008 falta, priorizando la específica.
ENERGY_KCAL_FALLBACK_IDS: tuple[int, ...] = (2048, 2047)


import re as _re


def _scrub_key(text: str) -> str:
    """Elimina cualquier ``api_key=...`` de un texto para no filtrar la clave.

    Las excepciones de ``requests``/``urllib3`` incluyen la URL completa, con la
    api_key en la query. Se enmascara antes de propagarla a mensajes o logs.
    """
    return _re.sub(r"(api_key=)[^&\s]+", r"\1***", text)


class MissingApiKeyError(RuntimeError):
    """Se lanza cuando no hay FDC_API_KEY en el entorno."""


class UsdaApiError(RuntimeError):
    """Error de comunicación o respuesta inválida de la API FDC."""


# usda_id (int, nutrient.id de FDC) -> nutrient_id canónico.
def _build_usda_index() -> dict[int, str]:
    index: dict[int, str] = {}
    for ndef in NUTRIENTS:
        for usda_id in ndef.usda_ids:
            index[usda_id] = ndef.id
    return index


USDA_ID_TO_NUTRIENT: dict[int, str] = _build_usda_index()


def get_api_key() -> str:
    """Devuelve la API key o falla con un mensaje accionable."""
    key = os.environ.get(FDC_API_KEY_ENV, "").strip()
    if not key:
        raise MissingApiKeyError(
            f"No hay API key de FoodData Central. Define la variable de entorno "
            f"{FDC_API_KEY_ENV} (solicítala gratis en https://fdc.nal.usda.gov/api-key-signup.html). "
            f"Sin ella no se descargan datos y no se inventa nada."
        )
    return key


class UsdaClient:
    """Cliente ligero de FoodData Central."""

    def __init__(self, api_key: str | None = None, base_url: str = FDC_BASE_URL,
                 session: requests.Session | None = None, timeout: int = DEFAULT_TIMEOUT):
        self._api_key = api_key or get_api_key()
        self._base_url = base_url.rstrip("/")
        self._session = session or requests.Session()
        self._timeout = timeout

    def search(self, query: str, page_size: int = 25, page_number: int = 1,
               data_types: list[str] | None = None) -> dict[str, Any]:
        """Busca alimentos por texto. Devuelve el JSON crudo de FDC."""
        url = f"{self._base_url}/foods/search"
        payload: dict[str, Any] = {
            "query": query,
            "pageSize": page_size,
            "pageNumber": page_number,
        }
        if data_types:
            payload["dataType"] = data_types
        try:
            resp = self._session.post(
                url, params={"api_key": self._api_key}, json=payload, timeout=self._timeout
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:  # pragma: no cover - red real
            raise UsdaApiError(f"Fallo al buscar «{query}» en FDC: {exc}") from exc

    def get_food(self, fdc_id: int | str, fmt: str = "full") -> dict[str, Any]:
        """Trae un alimento por su fdcId. Devuelve el JSON crudo de FDC."""
        url = f"{self._base_url}/food/{fdc_id}"
        try:
            resp = self._session.get(
                url, params={"api_key": self._api_key, "format": fmt}, timeout=self._timeout
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:  # pragma: no cover - red real
            raise UsdaApiError(f"Fallo al traer fdcId={fdc_id} de FDC: {exc}") from exc

    def list_food_ids(self, data_types: list[str], page_size: int = 200,
                      max_pages: int = 50, pause: float = 0.4) -> list[int]:
        """Devuelve los fdcId de un conjunto de tipos de dato paginando /foods/list.

        Se usa para enumerar, por ejemplo, todos los alimentos ``Foundation`` y
        ``SR Legacy`` (los de mejor calidad analítica) sin descargar aún el detalle.
        Respeta el rate limit con una pausa entre páginas.
        """
        url = f"{self._base_url}/foods/list"
        ids: list[int] = []
        for page in range(1, max_pages + 1):
            payload = {"dataType": data_types, "pageSize": page_size, "pageNumber": page}
            data = self._request_with_retry("post", url, json=payload)
            if not data:
                break
            for item in data:
                fdc_id = item.get("fdcId")
                if fdc_id is not None:
                    ids.append(int(fdc_id))
            if len(data) < page_size:
                break  # última página
            time.sleep(pause)
        return ids

    def get_foods_batch(self, fdc_ids: list[int | str], fmt: str = "full") -> list[dict[str, Any]]:
        """Trae el detalle de varios alimentos en una sola llamada (endpoint /foods).

        FDC admite hasta 20 fdcId por petición; conviene usar lotes pequeños
        (5-10) con ``format=full`` porque cada alimento trae ~100 nutrientes y la
        respuesta se vuelve pesada.
        """
        url = f"{self._base_url}/foods"
        payload = {"fdcIds": [str(i) for i in fdc_ids], "format": fmt}
        data = self._request_with_retry("post", url, json=payload)
        return data or []

    def _request_with_retry(self, method: str, url: str, *, json: dict | None = None,
                            max_retries: int = 4) -> Any:
        """Petición con reintentos ante 429 (rate limit) y timeouts.

        Ante un 429 respeta la cabecera ``Retry-After`` si viene; si no, espera
        de forma creciente. Ante timeout reintenta con backoff. Tras agotar los
        reintentos lanza ``UsdaApiError`` para que el llamador guarde lo ya
        conseguido y no pierda el trabajo.
        """
        params = {"api_key": self._api_key}
        backoff = 3.0
        for attempt in range(1, max_retries + 1):
            try:
                resp = self._session.request(
                    method, url, params=params, json=json, timeout=self._timeout
                )
                if resp.status_code == 429:
                    retry_after = resp.headers.get("Retry-After")
                    wait = float(retry_after) if retry_after and retry_after.isdigit() else backoff
                    if attempt == max_retries:
                        raise UsdaApiError(
                            "Rate limit (429) de FDC persistente tras varios reintentos. "
                            "Guarda lo conseguido y reanuda más tarde."
                        )
                    time.sleep(wait)
                    backoff *= 2
                    continue
                resp.raise_for_status()
                return resp.json()
            except requests.Timeout:
                if attempt == max_retries:
                    raise UsdaApiError(f"Timeout persistente en {url}.")
                time.sleep(backoff)
                backoff *= 2
            except requests.RequestException as exc:  # pragma: no cover - red real
                raise UsdaApiError(f"Fallo de red en {url}: {_scrub_key(str(exc))}") from exc
        return None  # inalcanzable


def _extract_nutrient_id(entry: dict[str, Any]) -> int | None:
    """Saca el nutrient.id (int) de una entrada foodNutrients de FDC.

    FDC tiene dos formas de respuesta:
      - Detalle (format=full): entry['nutrient']['id'].
      - Búsqueda (abreviada):  entry['nutrientId'].
    """
    nutrient = entry.get("nutrient")
    if isinstance(nutrient, dict) and "id" in nutrient:
        try:
            return int(nutrient["id"])
        except (TypeError, ValueError):
            return None
    if "nutrientId" in entry:
        try:
            return int(entry["nutrientId"])
        except (TypeError, ValueError):
            return None
    return None


def _extract_amount(entry: dict[str, Any]) -> float | None:
    """Saca el valor numérico (por 100 g) de una entrada foodNutrients."""
    for key in ("amount", "value"):
        if key in entry and entry[key] is not None:
            try:
                return float(entry[key])
            except (TypeError, ValueError):
                return None
    return None


def map_usda_food(raw: dict[str, Any], *, group: FoodGroup = FoodGroup.OTHER,
                  state: FoodState = FoodState.RAW, verified: bool = True,
                  subgroup: str | None = None, image_name: str | None = None) -> Food:
    """Convierte una respuesta de alimento FDC (detalle) a nuestro modelo Food.

    El grupo SEEN/SED no viene en FDC; se pasa como parámetro (clasificación
    manual o heurística posterior). Por defecto FoodGroup.OTHER.

    Solo se añaden nutrientes presentes en la respuesta y con valor numérico.
    Los ausentes quedan fuera del dict → not_determined por el modelo.

    Energía: si el alimento no trae 1008 (kcal, factores generales) pero sí la
    energía en kcal calculada por factores de Atwater (2048/2047), se usa esa
    como energy_kcal. Es energía real publicada por USDA, no un dato inventado.
    """
    fdc_id = raw.get("fdcId")
    name = raw.get("description") or raw.get("lowercaseDescription") or f"FDC {fdc_id}"

    nutrients: dict[str, NutrientValue] = {}
    raw_amount_by_id: dict[int, float] = {}
    for entry in raw.get("foodNutrients", []) or []:
        usda_id = _extract_nutrient_id(entry)
        if usda_id is None:
            continue
        amount = _extract_amount(entry)
        if amount is not None:
            raw_amount_by_id[usda_id] = amount
        nutrient_id = USDA_ID_TO_NUTRIENT.get(usda_id)
        if nutrient_id is None:
            continue  # nutriente FDC fuera de nuestro catálogo
        if amount is None:
            continue  # sin valor numérico → no se registra (not_determined)
        # FDC no marca trazas de forma estructurada; un valor reportado es measured.
        nutrients[nutrient_id] = NutrientValue(
            nutrient_id=nutrient_id, amount=amount, status=MeasurementStatus.MEASURED
        )

    # Respaldo de energía en kcal por factores de Atwater si falta 1008.
    if "energy_kcal" not in nutrients:
        for fallback_id in ENERGY_KCAL_FALLBACK_IDS:
            if fallback_id in raw_amount_by_id:
                nutrients["energy_kcal"] = NutrientValue(
                    nutrient_id="energy_kcal", amount=raw_amount_by_id[fallback_id],
                    status=MeasurementStatus.MEASURED,
                )
                break

    return Food(
        id=f"usda_{fdc_id}",
        name_es=str(name),
        group=group,
        source=DataSource.USDA,
        source_ref=str(fdc_id) if fdc_id is not None else None,
        state=state,
        edible_portion_factor=1.0,
        nutrients=nutrients,
        verified=verified,
        subgroup=subgroup,
        image_name=image_name,
    )


# ---------------------------------------------------------------------------
# Clasificación heurística USDA foodCategory -> FoodGroup SEEN/SED.
# La categoría de FDC llega como dict {'description': ...} (endpoint /foods) o
# como cadena (endpoint /foods/search). Se mapea por palabras clave. El subgrupo
# fino se conserva como la propia descripción de categoría USDA (en inglés).
# ---------------------------------------------------------------------------
def _category_text(raw: dict[str, Any]) -> str:
    cat = raw.get("foodCategory")
    if isinstance(cat, dict):
        return str(cat.get("description") or "")
    if isinstance(cat, str):
        return cat
    return ""


# (subcadena en minúsculas de la categoría) -> FoodGroup. Orden = prioridad.
_CATEGORY_RULES: list[tuple[str, FoodGroup]] = [
    ("legume", FoodGroup.LEGUME),
    ("nut and seed", FoodGroup.NUTS),
    ("fats and oils", FoodGroup.FAT),
    ("beverage", FoodGroup.BEVERAGE),
    ("fruit", FoodGroup.FRUIT),
    ("vegetable", FoodGroup.VEGETABLE),
    ("dairy", FoodGroup.DAIRY),  # "Dairy and Egg Products"; huevo se ajusta por nombre
    ("cereal grains", FoodGroup.STARCHY),
    ("pasta", FoodGroup.STARCHY),
    ("baked", FoodGroup.STARCHY),
    ("breakfast cereal", FoodGroup.STARCHY),
    ("beef", FoodGroup.PROTEIN),
    ("pork", FoodGroup.PROTEIN),
    ("poultry", FoodGroup.PROTEIN),
    ("lamb", FoodGroup.PROTEIN),
    ("veal", FoodGroup.PROTEIN),
    ("game", FoodGroup.PROTEIN),
    ("sausage", FoodGroup.PROTEIN),
    ("luncheon meat", FoodGroup.PROTEIN),
    ("finfish", FoodGroup.PROTEIN),
    ("shellfish", FoodGroup.PROTEIN),
    ("sweets", FoodGroup.SWEETS),
    ("soups, sauces", FoodGroup.SAUCES),
    ("spices and herbs", FoodGroup.SAUCES),
    ("snacks", FoodGroup.PREPARED),
    ("fast foods", FoodGroup.PREPARED),
    ("meals, entrees", FoodGroup.PREPARED),
    ("restaurant foods", FoodGroup.PREPARED),
    ("baby foods", FoodGroup.PREPARED),
]


def classify_usda_food(raw: dict[str, Any]) -> tuple[FoodGroup, str | None]:
    """Deduce (FoodGroup, subgrupo) de un alimento USDA por su categoría y nombre.

    Devuelve el grupo SEEN/SED más plausible y, como subgrupo, la descripción de
    categoría USDA original (en inglés) cuando existe. Heurística conservadora:
    ante la duda, FoodGroup.OTHER.
    """
    category = _category_text(raw).strip()
    cat_low = category.lower()
    name_low = str(raw.get("description") or "").lower()

    # El huevo cae en "Dairy and Egg Products" pero es proteína.
    if "egg" in name_low and "eggplant" not in name_low:
        return FoodGroup.PROTEIN, category or None

    for needle, group in _CATEGORY_RULES:
        if needle in cat_low:
            return group, category or None

    return FoodGroup.OTHER, category or None
