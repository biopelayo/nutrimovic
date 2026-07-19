"""Orquestador de extremo a extremo del ETL de NutriMovic.

Cosecha USDA (API real con FDC_API_KEY), carga CIQUAL (XLS oficial descargado),
añade el seed como respaldo, fusiona por prioridad de fuente y escribe la SQLite
canónica en ``data/nutrimovic.sqlite``.

Es idempotente y resiliente: si USDA falla por rate limit, se usa lo ya cacheado
y se sigue con CIQUAL y seed (el ETL no se queda sin construir la base).

Uso:
    python -m app.etl.run_etl                    # USDA (Foundation) + CIQUAL + seed
    python -m app.etl.run_etl --no-usda          # solo CIQUAL + seed
    python -m app.etl.run_etl --usda-limit 40    # prueba rápida
    python -m app.etl.run_etl --no-images        # omite fotos TheMealDB (más rápido)
"""
from __future__ import annotations

import argparse

from app.core.config import CIQUAL_XLS_PATH, USDA_DATA_TYPES, load_env
from app.core.models import Food
from app.etl import build_db, ciqual_loader, harvest_usda
from app.etl.usda_client import UsdaApiError


def collect_sources(*, use_usda: bool = True, usda_limit: int | None = None,
                    resolve_images: bool = True) -> dict[str, list[Food]]:
    """Reúne los alimentos de cada fuente en un dict listo para build_database."""
    load_env()
    foods_by_source: dict[str, list[Food]] = {}

    # USDA (prioritario). Ante fallo de red/rate limit, se usa lo cacheado.
    if use_usda:
        try:
            usda_foods = harvest_usda.harvest(
                USDA_DATA_TYPES, limit=usda_limit, resolve_images=resolve_images
            )
            foods_by_source["usda"] = usda_foods
            print(f"USDA: {len(usda_foods)} alimentos reales", flush=True)
        except UsdaApiError as exc:
            print(f"AVISO USDA: {exc}", flush=True)
            cache = harvest_usda._load_cache()
            if cache:
                raws = list(cache.values())
                foods_by_source["usda"] = harvest_usda.build_usda_foods(
                    raws, resolve_images=resolve_images
                )
                print(f"USDA (desde caché): {len(foods_by_source['usda'])} alimentos", flush=True)

    # CIQUAL (refuerzo). Si no está el fichero, se avisa y se continúa.
    try:
        ciqual_foods = ciqual_loader.load_ciqual_xls(CIQUAL_XLS_PATH)
        foods_by_source["ciqual"] = ciqual_foods
        print(f"CIQUAL: {len(ciqual_foods)} alimentos reales", flush=True)
    except ciqual_loader.CiqualFileNotFoundError as exc:
        print(f"AVISO CIQUAL: {exc}", flush=True)

    # Seed provisional como respaldo (última prioridad).
    seed_foods = build_db.load_seed_foods()
    if seed_foods:
        foods_by_source["seed_provisional"] = seed_foods
        print(f"Seed: {len(seed_foods)} alimentos", flush=True)

    return foods_by_source


def run(*, use_usda: bool = True, usda_limit: int | None = None,
        resolve_images: bool = True) -> build_db.BuildReport:
    foods_by_source = collect_sources(
        use_usda=use_usda, usda_limit=usda_limit, resolve_images=resolve_images
    )
    report = build_db.build_database(foods_by_source=foods_by_source)
    print("---")
    print(f"BD construida en: {report.db_path}")
    print(f"Alimentos totales: {report.foods_written}")
    print(f"Valores nutricionales: {report.values_written}")
    print(f"Por fuente: {report.by_source}")
    return report


def _main() -> None:
    parser = argparse.ArgumentParser(description="ETL de datos reales de NutriMovic.")
    parser.add_argument("--no-usda", action="store_true", help="No cosechar USDA.")
    parser.add_argument("--usda-limit", type=int, default=None, help="Máximo de fdcId USDA.")
    parser.add_argument("--no-images", action="store_true", help="No buscar fotos en TheMealDB.")
    args = parser.parse_args()
    run(use_usda=not args.no_usda, usda_limit=args.usda_limit,
        resolve_images=not args.no_images)


if __name__ == "__main__":
    _main()
