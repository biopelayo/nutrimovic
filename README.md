# NutriMovic

Hoja de dieta y calculadora nutricional por gramaje, pensada para consulta de
nutrición y endocrino. Introduces alimentos y sus gramos y calcula al instante
macronutrientes, micronutrientes, **intercambios** (HC · proteína · grasa),
medidas caseras y alérgenos, con ficha de paciente, objetivos y seguimiento.

**Web (PWA instalable):** se publica sola en GitHub Pages — ver [DEPLOY.md](DEPLOY.md).

## Qué incluye

- **Hoja de dieta** con 3.718 alimentos reales: buscas, pones gramos y el total
  se actualiza en vivo. Intercambios por los tres macronutrientes en columnas.
- **Plantilla** para montar un plato o menú, con intercambios y cobertura VRN.
- **Paciente**: antropometría (IMC, peso ideal, cintura/cadera), objetivos
  (Mifflin-St Jeor, gasto total, reparto de macros), comparación dieta-objetivos,
  seguimiento entre visitas, recordatorio de 24 h y notas de consulta.
- **Comidas**: reparto por comidas con % de energía y exportación a PDF.
- **Alertas**: semáforo de macros, sodio, azúcares, grasas saturadas, fibra y alérgenos.

## Fuentes de datos y licencias

Los valores de composición provienen de:

- **USDA FoodData Central** (Foundation Foods) — dominio público.
  <https://fdc.nal.usda.gov>
- **CIQUAL 2020** (Table de composition nutritionnelle, ANSES) — Licence Ouverte /
  Open Licence (Etalab 2.0). Reutilización con atribución a ANSES.
  <https://ciqual.anses.fr>
- Un conjunto reducido de datos de prueba propios, marcados como provisionales.

Los nombres se han traducido al español. Detalle por fuente en
[data/LICENCIAS_DATOS.md](data/LICENCIAS_DATOS.md).

## Aviso

Herramienta de apoyo a la decisión clínica; **no sustituye** al criterio del
profesional sanitario. Los datos de pacientes se guardan solo en el navegador
del usuario (localStorage), no se envían a ningún servidor.

## Desarrollo

- Frontend (React + Vite, PWA): `cd frontend && npm install && npm run dev`.
  La app es estática y funciona sin backend (catálogo en `frontend/public/catalog.json`).
- Backend (FastAPI) y ETL: solo para **regenerar** el catálogo desde USDA/CIQUAL.
  Requiere `backend/.env` con `FDC_API_KEY` (no incluida en el repo).

## Autor

Pelayo González de Lena Rodríguez ([@biopelayo](https://github.com/biopelayo)).
