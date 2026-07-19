# NutriMovic — Plan Maestro

> Calculadora nutricional por gramaje personalizado + tabla de intercambios SEEN/SED.
> Sede del proyecto: `D:\Antigravity\nutricalc\`
> Fecha de arranque: 2026-07-18 · Sistema Pelamovic

---

## 1. Objetivo

Herramienta fiable que, dado **un alimento conocido y su peso en gramos**, devuelve su valor nutricional completo (macronutrientes y micronutrientes) para **ese gramaje exacto**, no por 100 g. El usuario introduce el peso y la herramienta resuelve al instante. El fin último es diseñar dietas personalizadas.

Tres funcionalidades núcleo:

1. **Calculadora por gramaje.** Alimento + gramos → macros y micros de ese peso.
2. **Cobertura de todos los grupos de alimentos.** Base de datos amplia y bien clasificada.
3. **Tabla de intercambios de alimentos** (sistema español SEEN/SED), con equivalencias y función inversa.

---

## 2. Decisiones fijadas (2026-07-18)

| Decisión | Elección | Consecuencia |
|----------|----------|--------------|
| Fuente de datos | Híbrido **BEDCA + USDA FoodData Central + CIQUAL** | Micros exhaustivos + alimentos españoles + amplitud |
| Formato | **Motor Python + frontend web, empaquetado como PWA** | Misma app en PC y móvil, portable, sin reinstalar |
| Ámbito | **Personal ahora, clínico después** | Núcleo reutilizable con arquitectura lista para perfiles/pacientes |
| Intercambios | **SEEN/SED (español)** | Ración = 10 g del macronutriente principal, 6 grupos |

---

## 3. Modelo de datos nutricional (el corazón del sistema)

El reto técnico central no es el cálculo (es una regla de tres), sino **unificar tres bases con códigos, unidades y criterios distintos** en un esquema canónico único. Todo lo demás cuelga de esto.

### 3.1. Conjunto canónico de nutrientes

**Energía**
- Energía (kcal) y (kJ)

**Macronutrientes**
- Proteína (g)
- Grasa total (g)
- Hidratos de carbono totales (g) — declarar si es «disponibles» o «por diferencia»
- Fibra alimentaria (g) — soluble / insoluble cuando exista
- Agua (g)
- Alcohol (g)
- Cenizas (g)

**Desglose de grasas**
- AGS (saturados), AGM (monoinsaturados), AGP (poliinsaturados), grasas trans (g)
- Colesterol (mg)
- Omega-3 (ALA, EPA, DHA) y Omega-6 (g) cuando exista

**Desglose de hidratos**
- Azúcares totales (g), azúcares añadidos (g, si la fuente lo da), almidón (g), polioles (g)

**Vitaminas liposolubles**
- A (µg RAE, con retinol y β-caroteno separados si existen)
- D (µg), E (mg equiv. α-tocoferol), K (µg)

**Vitaminas hidrosolubles**
- C (mg), B1 tiamina, B2 riboflavina, B3 niacina (mg NE), B5 ác. pantoténico, B6 (mg)
- B7 biotina (µg), B9 folato (µg DFE), B12 (µg)

**Minerales y oligoelementos**
- Ca, Fe, Mg, P, K, Na, Zn (mg)
- Cu, Mn (mg); Se, I, Cr, Mo (µg); F (mg)

**Avanzado (fase posterior)**
- Aminoácidos, índice/carga glucémica, perfil de ácidos grasos ampliado

### 3.2. Unidades y conversiones críticas

Fuente frecuente de errores. Se fijan de entrada:
- Vitamina A en **µg RAE** (Retinol Activity Equivalents), no UI.
- Niacina en **mg NE** (Niacin Equivalents).
- Folato en **µg DFE** (Dietary Folate Equivalents).
- Vitamina E en **mg de α-tocoferol**.
- Vitamina D en **µg** (1 µg = 40 UI).
- Tabla de conversión documentada y testeada por separado.

### 3.3. Política de valores faltantes (regla de oro)

En nutrición, **«0» y «sin dato» son cosas distintas** y confundirlos arruina el rigor. Se distinguen tres estados:
- `0` real (el alimento no contiene el nutriente).
- `traza` (< límite de cuantificación).
- `N/D` (no determinado / la fuente no lo reporta).

Nunca se rellena un hueco con cero. Nunca se fabrican datos (regla del proyecto en `CLAUDE.md`).

### 3.4. Parte comestible y estado del alimento

Para rigor clínico se modela:
- **Factor de parte comestible** (peso neto tras retirar piel, hueso, cáscara). El usuario puede meter peso bruto o neto.
- **Crudo vs cocinado.** Factores de cambio de peso al cocinar y de retención de nutrientes. Se marca el estado del alimento en la ficha.

---

## 4. Motor de cálculo

### 4.1. Cálculo por gramaje (funcionalidad estrella)
```
valor(nutriente, gramos) = valor_por_100g × (gramos / 100) × factor_parte_comestible
```
Instantáneo, con propagación del estado N/D (si el dato base es N/D, el resultado es N/D, no 0).

### 4.2. Agregación
- Alimento → **plato/receta** (suma de ingredientes con sus gramajes).
- Plato → **dieta del día** → **dieta semanal**.
- Recálculo por peso cocinado del plato final.

### 4.3. Comparación con referencias
- % de cobertura frente a **VRN (Reglamento UE 1169/2011)** para etiquetado y frente a **valores de referencia EFSA (DRV)** para dietética.
- Ajuste por perfil: sexo, edad, embarazo/lactancia, nivel de actividad.
- Reparto de macros en % de la energía (P/G/HC) y por comidas.

---

## 5. Módulo de intercambios SEEN/SED

Sistema español de raciones de intercambio. **1 ración = 10 g del macronutriente principal del grupo.**

**Seis grupos:**
1. Lácteos (ración por HC)
2. Farináceos / harinas (ración por HC)
3. Frutas (ración por HC)
4. Verduras y hortalizas (ración por HC)
5. Alimentos proteicos: carnes, pescados, huevos (ración por proteína)
6. Grasas (ración por grasa)

**Funciones del módulo:**
- Tabla directa: gramos de cada alimento equivalentes a 1 intercambio.
- **Función inversa** (la que pides): alimento + gramos → cuántos intercambios aporta.
- Sustituciones dentro del mismo grupo (equivalencias para variar la dieta).
- Diseño de menús por intercambios (útil en dietas de diabetes y control clínico).

---

## 6. Arquitectura técnica

```
┌─────────────────────────────────────────────┐
│  Frontend PWA (React + Vite, responsive)     │  ← PC y móvil, instalable, offline
│  Buscador · Calculadora · Plato · Intercambios│
└───────────────────┬─────────────────────────┘
                    │  API REST
┌───────────────────┴─────────────────────────┐
│  Motor Python (FastAPI)                       │
│  cálculo · agregación · VRN · intercambios    │
└───────────────────┬─────────────────────────┘
                    │
┌───────────────────┴─────────────────────────┐
│  SQLite canónica (portable, embebible)        │
│  alimentos · nutrientes · mapeos · grupos     │
└───────────────────▲─────────────────────────┘
                    │  Pipeline ETL (una vez / actualizable)
        ┌───────────┼───────────┐
     BEDCA        USDA         CIQUAL
```

**Stack**
- Motor: **Python + FastAPI**, testeado con pytest.
- Datos: **SQLite** (un solo fichero, portable, funciona offline en móvil).
- Frontend: **React + Vite + Tailwind**, empaquetado como **PWA** (instalable en PC y en el teléfono desde el navegador).
- Estética: **Sistema Visual Pelamovic** (Botanical Green `#2D6A4F`, blanco puro, sans-serif).
- Export: PDF y Excel de la dieta calculada.
- Futuro opcional: Tauri para app de escritorio nativa si se quiere.

---

## 7. Fases de desarrollo

| Fase | Entregable | Estado |
|------|-----------|--------|
| **F0. Diseño** | Esquema canónico cerrado (nutrientes, unidades, política N/D, licencias) | Pendiente |
| **F1. Pipeline datos** | ETL que ingiere USDA (API), BEDCA y CIQUAL → SQLite canónica + tabla de mapeo de nutrientes | Pendiente |
| **F2. Motor cálculo** | Módulo Python de gramaje + parte comestible + agregación + tests | Pendiente |
| **F3. Intercambios** | Módulo SEEN/SED (tabla directa + función inversa) + tests | Pendiente |
| **F4. API** | FastAPI con endpoints de búsqueda, cálculo, plato, intercambios | Pendiente |
| **F5. Frontend PWA** | Buscador, calculadora por gramaje, constructor de plato, vista de intercambios | Pendiente |
| **F6. Referencias y export** | % VRN/EFSA por perfil, avisos, export PDF/Excel | Pendiente |
| **F7. Escalado clínico** | Gestión de perfiles/pacientes, dietas guardadas, plantillas | Pendiente |

---

## 8. Rigor y control de calidad

- **Constitución Pelamovic Art. 16:** capa de control independiente. Todo resultado positivo (p. ej. «este alimento cubre el 100 % de la vitamina C») se audita antes de darlo por bueno.
- **No fabricar datos.** Se usan solo las fuentes verificadas. Huecos = N/D explícito.
- **Validación cruzada:** cotejar el mismo alimento en las tres bases y reportar discrepancias grandes (control de calidad del emparejamiento).
- **Tests unitarios** en motor de cálculo, conversiones de unidades y módulo de intercambios.
- **Disclaimer clínico** visible: la herramienta apoya el diseño de dietas, no sustituye el juicio del profesional sanitario.

---

## 9. Riesgos y puntos a resolver en F0

1. **Licencias de datos.** USDA FoodData Central es dominio público. BEDCA y CIQUAL tienen términos de uso propios (cita obligatoria, posibles límites para uso comercial). Revisar antes de un uso clínico/comercial.
2. **Emparejamiento de alimentos** entre las tres bases (mismo alimento, nombres y códigos distintos). Estrategia de matching y prioridad de fuente.
3. **Conversiones de unidades:** riesgo alto de error silencioso. Se aíslan y testean.
4. **Crudo vs cocinado:** decidir cómo se presentan y si se aplican factores de retención.
5. **Prioridad de fuente por alimento:** BEDCA primero para alimentos españoles, USDA para micros, CIQUAL como refuerzo. Definir reglas.

---

## 10. Nombre propuesto

**NutriMovic** (marca del ecosistema Pelamovic). Alternativas: NutriScope, Pelanutri. A confirmar por Pelayo.
