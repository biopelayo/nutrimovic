/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Estética Microsoft Excel: verde Excel + grises de cuadrícula.
        brand: {
          DEFAULT: '#217346', // verde Excel
          2: '#33A06F',
          3: '#A8D5BA',
          4: '#E7F2EB',
          dark: '#185C37',
        },
        botanical: {
          DEFAULT: '#217346',
          2: '#33A06F',
          3: '#A8D5BA',
          4: '#E7F2EB',
          dark: '#185C37',
        },
        accent: {
          DEFAULT: '#C0392B', // rojo Excel para avisos/acento
          soft: '#E8A87C',
          4: '#FBECEA',
        },
        ink: {
          DEFAULT: '#171717',
          soft: '#444444',
          muted: '#7F7F7F',
        },
        line: '#D4D4D4', // línea de cuadrícula
        grid: '#D4D4D4',
        surface: '#F3F3F3', // área gris fuera de la hoja
        paper: '#FFFFFF',
        excelhead: '#F5F5F5', // fondo de encabezados de columna/fila
        excelsel: '#E6F2EC', // celda/columna seleccionada
        warm: '#C0392B',
        group: {
          dairy: '#4C86C6',
          starchy: '#C99A3D',
          fruit: '#C85C7E',
          vegetable: '#5A9E5A',
          protein: '#C15B4B',
          fat: '#C7A93D',
          legume: '#8A6FB0',
          nuts: '#9A6B3F',
          beverage: '#3FA0A6',
          sweets: '#C77BA0',
          sauces: '#7FA34A',
          prepared: '#6B7280',
          other: '#A8A29E',
        },
      },
      fontFamily: {
        // Tipografía tipo Excel (Calibri / Segoe UI).
        sans: ['Calibri', 'Segoe UI', 'system-ui', 'Arial', 'sans-serif'],
        display: ['Calibri', 'Segoe UI', 'system-ui', 'Arial', 'sans-serif'],
      },
      borderRadius: {
        card: '2px',
      },
      boxShadow: {
        card: '0 1px 2px rgba(0,0,0,0.08)',
        panel: '0 4px 16px rgba(0,0,0,0.18)',
        thumb: '0 0 0 1px rgba(0,0,0,0.08)',
      },
    },
  },
  plugins: [],
};
