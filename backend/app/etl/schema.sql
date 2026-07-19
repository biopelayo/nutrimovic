-- NutriMovic — esquema SQLite canónico
-- ---------------------------------------------------------------------------
-- Coherente con backend/app/core/models.py (Food, NutrientValue, NutrientDef)
-- y con el catálogo de backend/app/core/nutrients.py.
--
-- Reglas del contrato que el esquema respeta:
--   * Todo valor nutricional es por 100 g de parte comestible.
--   * El estado de medición (measured | trace | not_determined) nunca se
--     confunde con 0. La ausencia de fila en nutrient_values equivale a
--     not_determined; un 0 explícito con status='measured' es un 0 real.
--   * source referencia la tabla sources (bedca | usda | ciqual | seed_provisional).
--
-- El esquema es idempotente: CREATE TABLE IF NOT EXISTS. El orquestador
-- (build_db.py) vacía e inserta dentro de una transacción para reconstruir.

PRAGMA foreign_keys = ON;

-- Reconstrucción total: se eliminan las tablas antes de recrearlas para que el
-- esquema evolucione sin trabas (añadir columnas como subgroup/image_name). El
-- orden respeta las dependencias: primero los hijos, luego los padres.
DROP TABLE IF EXISTS nutrient_values;
DROP TABLE IF EXISTS foods;
DROP TABLE IF EXISTS nutrient_defs;
DROP TABLE IF EXISTS sources;

-- Fuentes de datos y su prioridad de fusión (menor número = mayor prioridad).
CREATE TABLE IF NOT EXISTS sources (
    id            TEXT PRIMARY KEY,       -- 'bedca' | 'usda' | 'ciqual' | 'seed_provisional'
    name_es       TEXT NOT NULL,
    priority      INTEGER NOT NULL,       -- 0 = máxima prioridad
    license_note  TEXT
);

-- Catálogo canónico de nutrientes (espejo de nutrients.py para consultas SQL).
CREATE TABLE IF NOT EXISTS nutrient_defs (
    id        TEXT PRIMARY KEY,           -- nutrient_id snake_case estable
    name_es   TEXT NOT NULL,
    unit      TEXT NOT NULL,
    category  TEXT NOT NULL               -- energy | macro | fat_detail | carb_detail | vitamin | mineral
);

-- Alimentos. Un registro por 100 g de parte comestible.
CREATE TABLE IF NOT EXISTS foods (
    id                     TEXT PRIMARY KEY,
    name_es                TEXT NOT NULL,
    food_group             TEXT NOT NULL,      -- FoodGroup: dairy, starchy, ...
    source                 TEXT NOT NULL REFERENCES sources(id),
    source_ref             TEXT,               -- id del alimento en la fuente original
    state                  TEXT NOT NULL DEFAULT 'raw',   -- raw | cooked
    edible_portion_factor  REAL NOT NULL DEFAULT 1.0,
    verified               INTEGER NOT NULL DEFAULT 0,    -- 0/1; 1 solo si fuente oficial validada
    subgroup               TEXT,               -- clasificación fina dentro del grupo (opcional)
    image_name             TEXT                -- nombre de ingrediente en TheMealDB para la foto (opcional)
);

-- Valores nutricionales por alimento. Clave compuesta (food_id, nutrient_id).
CREATE TABLE IF NOT EXISTS nutrient_values (
    food_id      TEXT NOT NULL REFERENCES foods(id) ON DELETE CASCADE,
    nutrient_id  TEXT NOT NULL REFERENCES nutrient_defs(id),
    amount       REAL,                    -- NULL admitido; el status manda
    status       TEXT NOT NULL DEFAULT 'not_determined',  -- measured | trace | not_determined
    PRIMARY KEY (food_id, nutrient_id)
);

CREATE INDEX IF NOT EXISTS idx_foods_group  ON foods(food_group);
CREATE INDEX IF NOT EXISTS idx_foods_source ON foods(source);
CREATE INDEX IF NOT EXISTS idx_nv_nutrient  ON nutrient_values(nutrient_id);
