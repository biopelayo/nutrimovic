"""Unifica subgrupos equivalentes a un conjunto canónico por grupo.

Las tres fuentes (seed español, CIQUAL francés, USDA inglés) traían subgrupos con
nombres distintos para lo mismo («Leche»/«Leches»/«Lácteos frescos»). Este script
los normaliza por reglas de palabra clave. Ejecutar:  python -m app.etl.normalize_subgroups
"""
from __future__ import annotations

import sqlite3
import unicodedata

DB = r"D:/Antigravity/nutricalc/data/nutrimovic.sqlite"


def strip(s: str) -> str:
    s = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def has(s: str, *ks: str) -> bool:
    return any(k in s for k in ks)


def canonical(group: str, subgroup: str | None) -> str:
    s = strip(subgroup or "")
    if group == "dairy":
        if has(s, "infantil"):
            return "Lácteos infantiles"
        if has(s, "yogur"):
            return "Yogur"
        if has(s, "queso"):
            return "Queso"
        if has(s, "nata", "crema", "mantequilla"):
            return "Nata, crema y mantequilla"
        if has(s, "leche"):
            return "Leche"
        return "Otros lácteos"
    if group == "starchy":
        if has(s, "pan"):
            return "Pan"
        if has(s, "tuber", "patata", "boniato"):
            return "Tubérculos"
        if has(s, "desayuno"):
            return "Cereales de desayuno"
        if has(s, "panaderia", "bolleria", "galleta", "pastel", "bizcocho", "viennois"):
            return "Bollería"
        return "Cereales, pasta y arroz"
    if group == "fruit":
        if has(s, "deseca", "pasa", "orejon", "datil"):
            return "Fruta desecada"
        if has(s, "rojo", "baya"):
            return "Frutos rojos"
        if has(s, "zumo"):
            return "Zumos"
        return "Fruta fresca"
    if group == "vegetable":
        if has(s, "hoja"):
            return "Verdura de hoja"
        if has(s, "ensalada", "crudite"):
            return "Ensaladas"
        if has(s, "alga"):
            return "Algas"
        if has(s, "seta", "champin", "hongo"):
            return "Setas"
        return "Hortalizas"
    if group == "protein":
        if has(s, "molusco", "crustaceo", "marisco"):
            return "Marisco"
        if has(s, "pescado", "pez", " mar", "del mar"):
            return "Pescado"
        if has(s, "ave", "pollo", "pavo"):
            return "Aves"
        if has(s, "huevo"):
            return "Huevos"
        if has(s, "embutido", "charcuteria", "fiambre", "procesad", "otros producto"):
            return "Embutidos y procesados"
        if has(s, "cordero", "caza"):
            return "Cordero y caza"
        if has(s, "cerdo"):
            return "Cerdo"
        if has(s, "vacuno", "ternera", "buey", "carne roja", "res"):
            return "Vacuno y carne roja"
        if has(s, "carne"):
            return "Carne"
        return "Otras carnes"
    if group == "fat":
        if has(s, "aceite"):
            return "Aceites"
        if has(s, "mantequilla", "margarina", "lactea", "untar"):
            return "Grasas para untar"
        return "Otras grasas"
    if group == "legume":
        return "Legumbres"
    if group == "nuts":
        if has(s, "semilla", "pipa"):
            return "Semillas"
        return "Frutos secos"
    if group == "beverage":
        if has(s, "agua"):
            return "Aguas"
        if has(s, "zumo"):
            return "Zumos"
        if has(s, "alcohol"):
            return "Bebidas alcohólicas"
        if has(s, "refresco", "gaseosa", "cola"):
            return "Refrescos"
        return "Otras bebidas"
    if group == "sweets":
        if has(s, "chocolate", "cacao"):
            return "Chocolate"
        if has(s, "azucar", "miel"):
            return "Azúcar y miel"
        if has(s, "galleta", "bolleria", "pastel", "bizcocho", "viennois", "barra"):
            return "Bollería y galletas"
        if has(s, "helado", "sorbete", "glace"):
            return "Helados"
        if has(s, "mermelada", "confitura"):
            return "Mermeladas"
        if has(s, "golosina", "confiteria"):
            return "Golosinas"
        return "Dulces"
    if group == "sauces":
        if has(s, "especia", "hierba"):
            return "Especias y hierbas"
        if s.strip() in ("sal", "sales"):
            return "Sales"
        return "Salsas y condimentos"
    return subgroup or "Otros"


def main() -> None:
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    n = 0
    for r in c.execute("SELECT id, food_group, subgroup FROM foods"):
        canon = canonical(r["food_group"], r["subgroup"])
        if canon != r["subgroup"]:
            c.execute("UPDATE foods SET subgroup=? WHERE id=?", (canon, r["id"]))
            n += 1
    c.commit()
    distinct = c.execute(
        "SELECT food_group, COUNT(DISTINCT subgroup) d FROM foods GROUP BY food_group ORDER BY food_group"
    ).fetchall()
    c.close()
    print("subgrupos reasignados:", n)
    for r in distinct:
        print(f"  {r['food_group']}: {r['d']} subgrupos")


if __name__ == "__main__":
    main()
