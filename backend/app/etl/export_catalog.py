"""Exporta el catálogo canónico (SQLite) a un JSON estático para el build web.

Genera `frontend/public/catalog.json` con todos los alimentos y su composición,
en el formato que consume el frontend (lib/catalog.ts). Ejecutar tras cambios en
la base:  python -m app.etl.export_catalog
"""
from __future__ import annotations

import json
import os
import sqlite3

DB = r"D:/Antigravity/nutricalc/data/nutrimovic.sqlite"
OUT = r"D:/Antigravity/nutricalc/frontend/public/catalog.json"


def main() -> None:
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    vals: dict[str, dict] = {}
    for r in c.execute("SELECT food_id, nutrient_id, amount, status FROM nutrient_values"):
        vals.setdefault(r["food_id"], {})[r["nutrient_id"]] = {
            "nutrient_id": r["nutrient_id"],
            "amount": r["amount"],
            "status": r["status"],
        }
    foods = []
    for r in c.execute("SELECT * FROM foods"):
        k = r.keys()
        foods.append(
            {
                "id": r["id"],
                "name_es": r["name_es"],
                "group": r["food_group"],
                "source": r["source"],
                "source_ref": r["source_ref"] if "source_ref" in k else None,
                "state": r["state"],
                "edible_portion_factor": r["edible_portion_factor"],
                "verified": bool(r["verified"]),
                "subgroup": r["subgroup"] if "subgroup" in k else None,
                "image_name": r["image_name"] if "image_name" in k else None,
                "allergens": json.loads(r["allergens"]) if "allergens" in k and r["allergens"] else [],
                "household_measure": r["household_measure"] if "household_measure" in k else None,
                "nutrients": vals.get(r["id"], {}),
            }
        )
    c.close()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(foods, f, ensure_ascii=False, separators=(",", ":"))
    print(f"catalog.json: {len(foods)} alimentos, {round(os.path.getsize(OUT) / 1e6, 2)} MB")


if __name__ == "__main__":
    main()
