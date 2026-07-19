// Alérgenos de declaración obligatoria en la UE (Reglamento 1169/2011, Anexo II).
export const ALLERGEN_LABELS: Record<string, string> = {
  gluten: 'Gluten',
  crustaceos: 'Crustáceos',
  huevo: 'Huevo',
  pescado: 'Pescado',
  cacahuetes: 'Cacahuetes',
  soja: 'Soja',
  lactosa: 'Lácteos',
  frutos_secos: 'Frutos de cáscara',
  apio: 'Apio',
  mostaza: 'Mostaza',
  sesamo: 'Sésamo',
  sulfitos: 'Sulfitos',
  altramuces: 'Altramuces',
  moluscos: 'Moluscos',
};

export function allergenLabel(code: string): string {
  return ALLERGEN_LABELS[code] ?? code;
}
