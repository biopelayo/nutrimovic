"""Resolución de imágenes de alimento contra TheMealDB.

TheMealDB publica imágenes de ingredientes en
``https://www.themealdb.com/images/ingredients/{Nombre}.png``. Este módulo
intenta emparejar el nombre en inglés de un alimento USDA con un ingrediente
conocido de TheMealDB y verifica que la imagen exista (HTTP 200). Si no hay
coincidencia o la red falla, devuelve ``None``: nunca inventa una imagen.

El nombre guardado (``image_name``) es el nombre canónico del ingrediente en
TheMealDB (por ejemplo «Chicken Breast»), que el frontend usa para componer la
URL de la foto.
"""
from __future__ import annotations

import unicodedata

import requests

INGREDIENTS_LIST_URL = "https://www.themealdb.com/api/json/v1/1/list.php?i=list"
IMAGE_URL_TEMPLATE = "https://www.themealdb.com/images/ingredients/{name}.png"


def _norm(text: str) -> str:
    s = unicodedata.normalize("NFKD", str(text))
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return " ".join("".join(ch if ch.isalnum() else " " for ch in s).split())


def _singular(norm: str) -> str:
    """Singular ingenuo: quita una 's' final ("apples" → "apple")."""
    return norm[:-1] if len(norm) > 3 and norm.endswith("s") else norm


class MealDbResolver:
    """Empareja descripciones USDA con ingredientes de TheMealDB (con caché)."""

    def __init__(self, session: requests.Session | None = None, timeout: int = 20,
                 verify_images: bool = True):
        self._session = session or requests.Session()
        self._timeout = timeout
        self._verify = verify_images
        # normalizado (y su singular) -> nombre canónico del ingrediente.
        self._index: dict[str, str] = {}
        self._image_ok: dict[str, bool] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        try:
            resp = self._session.get(INGREDIENTS_LIST_URL, timeout=self._timeout)
            resp.raise_for_status()
            meals = resp.json().get("meals") or []
        except (requests.RequestException, ValueError):
            return  # sin lista → no habrá imágenes; se devuelve None siempre
        for m in meals:
            canonical = (m.get("strIngredient") or "").strip()
            if not canonical:
                continue
            n = _norm(canonical)
            self._index.setdefault(n, canonical)
            self._index.setdefault(_singular(n), canonical)

    def _image_exists(self, canonical: str) -> bool:
        if not self._verify:
            return True
        if canonical in self._image_ok:
            return self._image_ok[canonical]
        url = IMAGE_URL_TEMPLATE.format(name=canonical.replace(" ", "%20"))
        try:
            resp = self._session.head(url, timeout=self._timeout, allow_redirects=True)
            ok = resp.status_code == 200 and "image" in resp.headers.get("Content-Type", "")
        except requests.RequestException:
            ok = False
        self._image_ok[canonical] = ok
        return ok

    def _candidates(self, description: str) -> list[str]:
        """Genera candidatos de nombre a partir de una descripción USDA."""
        cands: list[str] = []
        segments = [seg.strip() for seg in description.split(",") if seg.strip()]
        for seg in segments[:2]:  # los primeros segmentos son los más específicos
            n = _norm(seg)
            if n:
                cands.append(n)
                cands.append(_singular(n))
                words = n.split()
                if words:
                    cands.append(words[0])
                    cands.append(_singular(words[0]))
                    if len(words) >= 2:
                        cands.append(" ".join(words[:2]))
        # dedup preservando orden
        seen: set[str] = set()
        out: list[str] = []
        for c in cands:
            if c and c not in seen:
                seen.add(c)
                out.append(c)
        return out

    def resolve(self, description: str) -> str | None:
        """Devuelve el nombre de ingrediente TheMealDB con imagen 200, o None."""
        self._ensure_loaded()
        if not self._index:
            return None
        for cand in self._candidates(description):
            canonical = self._index.get(cand)
            if canonical and self._image_exists(canonical):
                return canonical
        return None
