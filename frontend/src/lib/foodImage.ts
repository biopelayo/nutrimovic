// Imágenes reales de alimentos desde TheMealDB (libres, sin clave).
// https://www.themealdb.com/images/ingredients/<Nombre>.png  (y -Small.png)
export function foodImageUrl(imageName?: string | null, small = true): string | null {
  if (!imageName) return null;
  const enc = encodeURIComponent(imageName.trim());
  return `https://www.themealdb.com/images/ingredients/${enc}${small ? '-Small' : ''}.png`;
}
