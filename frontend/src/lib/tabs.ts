export type TabId = 'plantilla' | 'dieta' | 'paciente' | 'comidas' | 'alertas';

export interface TabMeta {
  id: TabId;
  label: string;
}

export const TABS: TabMeta[] = [
  { id: 'plantilla', label: 'Plantilla' },
  { id: 'dieta', label: 'Hoja de dieta' },
  { id: 'paciente', label: 'Paciente' },
  { id: 'comidas', label: 'Comidas' },
  { id: 'alertas', label: 'Alertas' },
];
