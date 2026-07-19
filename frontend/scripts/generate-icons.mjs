// Generador de iconos NutriMovic sin dependencias externas.
// Dibuja una hoja botánica blanca sobre verde #2D6A4F y codifica PNG a mano.
import { deflateSync } from 'node:zlib';
import { mkdirSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const OUT = join(dirname(fileURLToPath(import.meta.url)), '..', 'public', 'icons');
mkdirSync(OUT, { recursive: true });

const GREEN = [45, 106, 79]; // #2D6A4F
const GREEN_LIGHT = [82, 183, 136]; // #52B788
const WHITE = [255, 255, 255];

// --- CRC32 para los chunks PNG ---
const crcTable = (() => {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    t[n] = c >>> 0;
  }
  return t;
})();
function crc32(buf) {
  let c = 0xffffffff;
  for (let i = 0; i < buf.length; i++) c = crcTable[(c ^ buf[i]) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}
function chunk(type, data) {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length, 0);
  const typeBuf = Buffer.from(type, 'ascii');
  const body = Buffer.concat([typeBuf, data]);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(body), 0);
  return Buffer.concat([len, body, crc]);
}
function encodePNG(size, rgba) {
  const sig = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(size, 0);
  ihdr.writeUInt32BE(size, 4);
  ihdr[8] = 8; // bit depth
  ihdr[9] = 6; // color type RGBA
  // raw: cada fila precedida por byte de filtro 0
  const stride = size * 4;
  const raw = Buffer.alloc((stride + 1) * size);
  for (let y = 0; y < size; y++) {
    raw[y * (stride + 1)] = 0;
    rgba.copy(raw, y * (stride + 1) + 1, y * stride, y * stride + stride);
  }
  const idat = deflateSync(raw, { level: 9 });
  return Buffer.concat([
    sig,
    chunk('IHDR', ihdr),
    chunk('IDAT', idat),
    chunk('IEND', Buffer.alloc(0)),
  ]);
}

// Interseccion de dos circulos (forma de lente = hoja), rotada 45 grados.
function drawLeaf(size, { maskable }) {
  const rgba = Buffer.alloc(size * size * 4);
  const cx = size / 2;
  const cy = size / 2;
  // Radio de la hoja: en maskable dejamos mas margen (zona segura 80%).
  const leaf = maskable ? size * 0.30 : size * 0.36;
  const R = leaf * 1.35; // radio de cada circulo generador
  const d = leaf * 0.62; // separacion de centros
  const cos = Math.cos(-Math.PI / 4);
  const sin = Math.sin(-Math.PI / 4);

  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const i = (y * size + x) * 4;
      // fondo verde
      let color = GREEN;
      // coordenadas centradas y rotadas
      const dx = x - cx;
      const dy = y - cy;
      const rx = dx * cos - dy * sin;
      const ry = dx * sin + dy * cos;
      const d1 = Math.hypot(rx - d, ry);
      const d2 = Math.hypot(rx + d, ry);
      const inLeaf = d1 < R && d2 < R;
      if (inLeaf) {
        // nervadura central (linea fina hacia el verde claro)
        color = Math.abs(rx) < size * 0.012 ? GREEN_LIGHT : WHITE;
      }
      rgba[i] = color[0];
      rgba[i + 1] = color[1];
      rgba[i + 2] = color[2];
      rgba[i + 3] = 255;
    }
  }
  return rgba;
}

const targets = [
  { name: 'icon-192.png', size: 192, maskable: false },
  { name: 'icon-512.png', size: 512, maskable: false },
  { name: 'icon-maskable-512.png', size: 512, maskable: true },
  { name: 'apple-touch-icon.png', size: 180, maskable: false },
];
for (const t of targets) {
  const rgba = drawLeaf(t.size, { maskable: t.maskable });
  writeFileSync(join(OUT, t.name), encodePNG(t.size, rgba));
  console.log('  generado', t.name);
}

// Favicon SVG (misma identidad, vectorial).
const favicon = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="14" fill="#2D6A4F"/>
  <g transform="rotate(-45 32 32)">
    <path d="M32 14 C44 20 44 44 32 50 C20 44 20 20 32 14 Z" fill="#FFFFFF"/>
    <line x1="32" y1="16" x2="32" y2="48" stroke="#52B788" stroke-width="1.6"/>
  </g>
</svg>`;
writeFileSync(join(OUT, 'favicon.svg'), favicon);
console.log('  generado favicon.svg');
