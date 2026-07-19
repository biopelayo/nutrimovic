# Publicar NutriMovic en la web (GitHub Pages)

La app es **estática**: no necesita servidor. Los 3.718 alimentos van embebidos en
`frontend/public/catalog.json` y todo el cálculo ocurre en el navegador. Se instala
como PWA en el móvil.

## Pasos (una sola vez)

1. Crea un repositorio vacío en tu GitHub (p. ej. `nutrimovic`).
2. Desde la carpeta del proyecto (`D:\Antigravity\nutricalc`):
   ```bash
   git init
   git add .
   git commit -m "NutriMovic: hoja de dieta con datos reales"
   git branch -M main
   git remote add origin https://github.com/<tu-usuario>/nutrimovic.git
   git push -u origin main
   ```
3. En GitHub: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
4. El workflow `.github/workflows/deploy.yml` se ejecuta solo en cada `push` y publica
   la web. La URL aparece en la pestaña **Actions** / **Settings → Pages**
   (normalmente `https://<tu-usuario>.github.io/nutrimovic/`).

## Notas

- El `base` del build es relativo (`./`), así que funciona en cualquier subruta.
  Si quieres una ruta fija, exporta `VITE_BASE_PATH="/nutrimovic/"` antes de compilar.
- El catálogo (`catalog.json`, ~varios MB) se cachea en el navegador tras la primera
  carga, así la app va rápida y funciona offline.
- La clave de USDA (`backend/.env`) **no se sube** (está en `.gitignore`). El backend
  y el ETL solo hacen falta para regenerar datos, no para la web publicada.

## Probar el build en local (sin publicar)

```bash
cd frontend
npm run build
npm run preview   # sirve dist/ en http://localhost:5176
```
