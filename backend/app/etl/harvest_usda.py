"""Cosecha de alimentos reales de USDA FoodData Central hacia el modelo Food.

Estrategia (datos analíticos de calidad):
  1. Enumera los fdcId de los tipos ``Foundation`` (y opcionalmente ``SR Legacy``)
     con ``/foods/list`` — los conjuntos con datos analíticos.
  2. Descarga el detalle en lotes pequeños con ``/foods`` (format=full), que trae
     el ``nutrient.id`` que espera ``map_usda_food`` y la categoría del alimento.
  3. Clasifica grupo/subgrupo con ``classify_usda_food`` y busca una foto en
     TheMealDB por el nombre en inglés (verificando HTTP 200).

Resiliencia ante rate limit (1000 req/h con clave real): entre lotes hay pausas
y, si aparece un 429 persistente o un timeout, se GUARDA lo ya conseguido en la
caché JSON (``data/raw/usda_harvest_cache.json``) y se relanza el error. Una
nueva ejecución reutiliza la caché y solo pide lo que falta: el trabajo no se
pierde.

No fabrica datos: cada valor procede de la respuesta real de FDC.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from app.core.config import DATA_DIR
from app.core.models import Food
from app.etl.themealdb import MealDbResolver
from app.etl.usda_client import UsdaApiError, UsdaClient, classify_usda_food, map_usda_food

CACHE_PATH = DATA_DIR / "raw" / "usda_harvest_cache.json"


def _load_cache() -> dict[str, dict]:
    """Detalles crudos ya descargados, indexados por fdcId (str)."""
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return {}
    return {}


def _save_cache(cache: dict[str, dict]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")


def fetch_raw_foods(client: UsdaClient, fdc_ids: list[int], *, batch_size: int = 6,
                    pause: float = 0.5, cache: dict[str, dict] | None = None,
                    progress: bool = True) -> dict[str, dict]:
    """Descarga (o reutiliza de caché) el detalle crudo de una lista de fdcId.

    Guarda la caché tras cada lote. Si un lote falla por rate limit/timeout,
    persiste lo conseguido y relanza para que el llamador decida.
    """
    cache = cache if cache is not None else _load_cache()
    pending = [i for i in fdc_ids if str(i) not in cache]
    total = len(pending)
    done = 0
    try:
        for start in range(0, total, batch_size):
            chunk = pending[start:start + batch_size]
            raws = client.get_foods_batch(chunk, fmt="full")
            for raw in raws:
                fdc_id = raw.get("fdcId")
                if fdc_id is not None:
                    cache[str(fdc_id)] = raw
            _save_cache(cache)
            done += len(chunk)
            if progress:
                print(f"  USDA detalle: {done}/{total} descargados", flush=True)
            time.sleep(pause)
    except UsdaApiError:
        _save_cache(cache)
        raise
    return cache


def build_usda_foods(raws: list[dict], *, resolve_images: bool = True) -> list[Food]:
    """Convierte detalles crudos FDC en Food clasificados y con foto (si hay)."""
    resolver = MealDbResolver() if resolve_images else None
    foods: list[Food] = []
    for raw in raws:
        group, subgroup = classify_usda_food(raw)
        image_name = None
        if resolver is not None:
            description = str(raw.get("description") or "")
            try:
                image_name = resolver.resolve(description)
            except Exception:  # noqa: BLE001 - la foto es opcional, nunca rompe el ETL
                image_name = None
        foods.append(
            map_usda_food(raw, group=group, subgroup=subgroup, image_name=image_name)
        )
    return foods


def harvest(data_types: list[str] | None = None, *, limit: int | None = None,
            resolve_images: bool = True, client: UsdaClient | None = None) -> list[Food]:
    """Cosecha completa: enumera, descarga, clasifica y devuelve Food de USDA.

    ``data_types`` por defecto es ``["Foundation"]`` (datos analíticos, ~400
    alimentos). Añade ``"SR Legacy"`` para ampliar. ``limit`` recorta el número
    de fdcId a procesar (útil en pruebas).
    """
    data_types = data_types or ["Foundation"]
    client = client or UsdaClient()

    print(f"Enumerando fdcId de USDA para: {data_types} ...", flush=True)
    fdc_ids = client.list_food_ids(data_types)
    if limit is not None:
        fdc_ids = fdc_ids[:limit]
    print(f"  {len(fdc_ids)} fdcId a procesar", flush=True)

    cache = fetch_raw_foods(client, fdc_ids)
    raws = [cache[str(i)] for i in fdc_ids if str(i) in cache]
    print(f"Construyendo Food desde {len(raws)} detalles ...", flush=True)
    return build_usda_foods(raws, resolve_images=resolve_images)
