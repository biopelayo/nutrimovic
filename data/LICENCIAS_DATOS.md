# Estado de licencia de las fuentes de datos — NutriMovic

Este documento resume el estado de licencia y las condiciones de uso de cada
fuente de composición de alimentos que integra NutriMovic. Es una guía de
trabajo, no un dictamen jurídico. **Antes de cualquier uso comercial o
publicación, verifica los términos vigentes en la web oficial de cada fuente**,
porque cambian con el tiempo.

Resumen rápido:

| Fuente | Ámbito | Licencia (estado) | Cita obligatoria | Uso comercial |
|--------|--------|-------------------|------------------|---------------|
| USDA FoodData Central | EE. UU. | Dominio público | Recomendada | Permitido |
| BEDCA | España | Términos propios | Sí | Verificar |
| CIQUAL (ANSES) | Francia | Etalab 2.0 (abierta) | Sí | Permitido (verificar) |

---

## 1. USDA FoodData Central

- **Organismo:** U.S. Department of Agriculture (USDA), Agricultural Research
  Service.
- **Web:** https://fdc.nal.usda.gov/ · Guía de la API:
  https://fdc.nal.usda.gov/api-guide
- **Licencia:** dominio público. Las obras del Gobierno federal de EE. UU. no
  están sujetas a copyright dentro de EE. UU. (17 U.S.C. §105). USDA declara sus
  datos como de dominio público y de uso libre.
- **Cita:** no es una obligación legal, pero USDA recomienda citar la fuente y
  la fecha de acceso (los datos se versionan). Formato sugerido: «U.S. Department
  of Agriculture, Agricultural Research Service. FoodData Central, [año].
  fdc.nal.usda.gov».
- **Uso comercial:** permitido.
- **A tener en cuenta:**
  - La API requiere una clave gratuita (`FDC_API_KEY`), con límite de peticiones
    por hora. La clave es una condición de acceso, no una restricción de licencia
    sobre los datos.
  - Hay varios `dataType` (Foundation, SR Legacy, Survey FNDDS, Branded). Los
    *Branded* incluyen datos aportados por fabricantes; conviene revisar su
    procedencia antes de tratarlos como referencia.

## 2. BEDCA — Base de Datos Española de Composición de Alimentos

- **Organismo:** Red BEDCA, con la Agencia Española de Seguridad Alimentaria y
  Nutrición (AESAN) y el entonces Ministerio competente.
- **Web:** https://www.bedca.net/
- **Licencia:** BEDCA no publica una licencia abierta estándar (tipo CC o
  Etalab). El acceso es por consulta web y exportación puntual, sujeto a sus
  condiciones de uso. **Debe revisarse la nota legal del sitio antes de
  redistribuir los datos o incorporarlos a un producto.**
- **Cita:** obligatoria. Debe citarse BEDCA como fuente en cualquier uso o
  publicación de sus datos.
- **Uso comercial:** **por verificar.** No consta una autorización comercial
  general y explícita. Para un producto comercial, lo prudente es contactar con
  la Red BEDCA / AESAN y obtener permiso o confirmación por escrito antes de
  distribuir.
- **A tener en cuenta:**
  - No hay API pública documentada equivalente a la de USDA; la ingesta parte de
    un fichero exportado localmente.
  - Es la referencia canónica para alimentos españoles y, por eso, la fuente de
    máxima prioridad en `SOURCE_PRIORITY`. Esa prioridad es de calidad del dato,
    no una licencia para redistribuir libremente.

## 3. CIQUAL — Tabla de composición de alimentos (ANSES, Francia)

- **Organismo:** ANSES (Agence nationale de sécurité sanitaire de l'alimentation,
  de l'environnement et du travail).
- **Web:** https://ciqual.anses.fr/
- **Licencia:** los datos de CIQUAL se publican bajo **Licence Ouverte / Open
  Licence (Etalab 2.0)**, una licencia abierta compatible con CC BY. Permite
  reutilizar, redistribuir y adaptar, incluido el uso comercial, con la
  condición de atribución. **Verifica en el portal la versión y el alcance
  vigentes para la descarga concreta que uses.**
- **Cita:** obligatoria (atribución Etalab). Formato sugerido: «Table CIQUAL
  [año], ANSES» con enlace a ciqual.anses.fr.
- **Uso comercial:** permitido bajo Etalab 2.0, sujeto a atribución. Aun así,
  **confirma la licencia del fichero descargado** antes de publicar.
- **A tener en cuenta:**
  - El fichero se descarga como CSV/XLS (separador `;`, coma decimal, francés).
  - CIQUAL reporta el sodio y, por separado, la sal («sel»); no mezclar ambos.
    El loader usa la columna de sodio directa cuando existe.

---

## Reglas de integración que protegen la licencia y el rigor

1. **Trazabilidad:** cada alimento guarda su `source` y `source_ref` (id en la
   fuente original), de modo que siempre puede citarse y auditarse su origen.
2. **Sin mezcla silenciosa:** la fusión por prioridad (`build_db.merge_foods`)
   registra de qué fuente sale cada alimento; los huecos se rellenan desde
   fuentes de menor prioridad sin sobrescribir valores útiles.
3. **Sin invención:** los huecos se propagan como `not_determined`, nunca como 0.
4. **Datos semilla:** la fuente `seed_provisional` es interna y provisional; no
   debe publicarse ni presentarse como dato oficial.

## Pendientes de verificación antes de un uso comercial

- [ ] BEDCA: confirmar por escrito con Red BEDCA / AESAN el permiso de uso y
      redistribución en un producto comercial.
- [ ] CIQUAL: confirmar la licencia (Etalab 2.0) del fichero exacto descargado y
      su versión.
- [ ] USDA: revisar la procedencia de los alimentos *Branded* si se incorporan.
- [ ] Revisar la obligación y el formato exacto de atribución de las tres
      fuentes en la interfaz final de NutriMovic.
