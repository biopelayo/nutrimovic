# NutriMovic — Contratos compartidos

> Este documento es el **contrato único** del que dependen todos los módulos.
> Cualquier agente que trabaje en el proyecto debe respetarlo. Si algo cambia aquí, cambia para todos.

---

## 1. Contrato de datos

### 1.1. Catálogo de nutrientes
La lista canónica de nutrientes vive en código en `backend/app/core/nutrients.py` (fuente de verdad).
Cada nutriente tiene: `id` (snake_case estable), `name_es`, `unit`, `category`, y códigos de mapeo a USDA/BEDCA/CIQUAL.

Categorías: `energy`, `macro`, `fat_detail`, `carb_detail`, `vitamin`, `mineral`.

### 1.2. Estado de medición (regla de oro)
Cada valor nutricional lleva un **estado**. Nunca se confunde 0 con ausencia de dato.
- `measured` — valor real medido.
- `trace` — por debajo del límite de cuantificación (se trata como ~0 pero se marca).
- `not_determined` — la fuente no reporta el nutriente. **No es 0.**

Si un valor base es `not_determined`, el resultado de cualquier cálculo sobre él también lo es (se propaga, no se rellena con 0).

### 1.3. Modelo `Food` (por 100 g de parte comestible)
```
Food:
  id: str                       # id canónico estable
  name_es: str
  group: FoodGroup              # grupo SEEN/SED u otro
  source: DataSource            # bedca | usda | ciqual | seed_provisional
  source_ref: str | None        # id del alimento en la fuente original
  state: FoodState              # raw | cooked
  edible_portion_factor: float  # 1.0 = todo comestible; 0.68 = 68% aprovechable
  nutrients: dict[str, NutrientValue]   # clave = nutrient_id; valores por 100 g
  verified: bool                # True solo si viene de fuente oficial validada
```

### 1.4. Unidades fijadas (no negociable)
- Energía: `energy_kcal` (kcal) y `energy_kj` (kJ).
- Vitamina A: **µg RAE**. Vitamina D: **µg**. Vitamina E: **mg α-tocoferol**. Vitamina K: **µg**.
- Niacina (B3): **mg NE**. Folato (B9): **µg DFE**. B12: **µg**. Biotina (B7): **µg**.
- Minerales mayores en mg; oligoelementos (Se, I, Cr, Mo) en µg.

---

## 2. Contrato de API (FastAPI)

Base URL en desarrollo: `http://127.0.0.1:8000`

| Método | Ruta | Cuerpo / Query | Devuelve |
|--------|------|----------------|----------|
| GET | `/health` | — | `{status, version, foods_loaded}` |
| GET | `/foods/search` | `?q=&group=&limit=` | lista de `FoodSummary` |
| GET | `/foods/{food_id}` | — | `Food` completo (por 100 g) |
| POST | `/calculate` | `{food_id, grams, use_edible_portion}` | `PortionResult` |
| POST | `/plate` | `{items:[{food_id, grams}]}` | `PlateResult` (suma + por ítem) |
| GET | `/exchanges/food/{food_id}` | `?grams=` | `ExchangeResult` (intercambios que aporta) |
| GET | `/exchanges/table` | `?group=` | tabla directa: g por 1 intercambio |
| POST | `/reference/coverage` | `{profile, nutrients_totals}` | % VRN/EFSA por nutriente |

### 2.1. `PortionResult` (respuesta de la calculadora estrella)
```
PortionResult:
  food_id: str
  name_es: str
  grams: float
  grams_edible: float                 # tras aplicar parte comestible
  nutrients: dict[str, ResultValue]   # {amount, unit, status} para ese gramaje
```

`ResultValue.status` propaga `measured | trace | not_determined`.

### 2.2. Regla de cálculo por gramaje
```
amount(nutrient, grams) = value_per_100g × (grams_edible / 100)
grams_edible = grams × edible_portion_factor   (si use_edible_portion)
```

---

## 3. Contrato de intercambios SEEN/SED

- 1 ración de intercambio = **10 g del macronutriente principal** del grupo.
- Grupos y macro de referencia:
  - `dairy` (lácteos) → HC
  - `starchy` (farináceos/harinas) → HC
  - `fruit` (frutas) → HC
  - `vegetable` (verduras) → HC
  - `protein` (carnes/pescados/huevos) → proteína
  - `fat` (grasas) → grasa
- Función directa: gramos de alimento = 10 g del macro / (macro_por_100g / 100).
- Función inversa (la principal): intercambios = (macro_en_gramaje) / 10.

---

## 4. Grupos de alimentos (`FoodGroup`)
Grupos SEEN/SED + auxiliares para cobertura completa:
`dairy`, `starchy`, `fruit`, `vegetable`, `protein`, `fat`,
`legume`, `nuts`, `beverage`, `sweets`, `sauces`, `prepared`, `other`.

---

## 5. Reglas de trabajo para agentes
1. Respetar este contrato y los tipos de `backend/app/core/models.py`.
2. No fabricar datos nutricionales. Huecos = `not_determined`.
3. Tests obligatorios en cada módulo (pytest para Python).
4. Estética del frontend: Sistema Visual Pelamovic (Botanical Green `#2D6A4F`, blanco puro, sans-serif).
5. Trabajar solo dentro de la carpeta asignada para evitar colisiones.
