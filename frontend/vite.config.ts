import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

// NutriMovic — PWA estática (desplegable en GitHub Pages sin backend).
// `base` relativo para que funcione en cualquier subruta (usuario.github.io/repo/).
// Si prefieres una ruta fija, exporta VITE_BASE_PATH="/nombre-repo/" antes del build.
export default defineConfig({
  base: './',
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['icons/favicon.svg', 'icons/apple-touch-icon.png', 'offline.html'],
      manifest: {
        name: 'NutriMovic — Calculadora nutricional',
        short_name: 'NutriMovic',
        description:
          'Hoja de dieta con datos reales: macronutrientes, micronutrientes, intercambios y objetivos.',
        lang: 'es',
        start_url: '.',
        scope: '.',
        display: 'standalone',
        orientation: 'portrait-primary',
        background_color: '#FFFFFF',
        theme_color: '#217346',
        icons: [
          { src: 'icons/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
          { src: 'icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
          { src: 'icons/icon-maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        // El catálogo (grande) no se precachea; se cachea en tiempo de ejecución.
        globPatterns: ['**/*.{js,css,html,svg,png,woff2}'],
        globIgnores: ['**/catalog.json'],
        maximumFileSizeToCacheInBytes: 4 * 1024 * 1024,
        runtimeCaching: [
          {
            urlPattern: /catalog\.json$/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'nutrimovic-catalogo',
              expiration: { maxEntries: 2, maxAgeSeconds: 60 * 60 * 24 * 30 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          {
            urlPattern: /themealdb\.com\/images\/ingredients/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'nutrimovic-fotos',
              expiration: { maxEntries: 500, maxAgeSeconds: 60 * 60 * 24 * 30 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
        ],
      },
      devOptions: { enabled: false },
    }),
  ],
  server: { port: 5176, strictPort: true },
  preview: { port: 5176 },
});
