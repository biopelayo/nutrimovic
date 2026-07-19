import { useState } from 'react';
import { GROUP_BY_ID } from '../data/foodGroups';
import { foodImageUrl } from '../lib/foodImage';
import type { FoodGroup } from '../types';

interface Props {
  name: string;
  group: FoodGroup;
  imageName?: string | null;
  size?: number;
}

/** Miniatura con foto real del alimento; si falta o falla, inicial coloreada. */
export function FoodThumb({ name, group, imageName, size = 38 }: Props) {
  const [failed, setFailed] = useState(false);
  const url = foodImageUrl(imageName);
  const g = GROUP_BY_ID[group];

  return (
    <span className="thumb" style={{ width: size, height: size }}>
      {url && !failed ? (
        <img src={url} alt="" loading="lazy" onError={() => setFailed(true)} />
      ) : (
        <span
          className="grid h-full w-full place-items-center font-display text-sm font-semibold text-white"
          style={{ backgroundColor: g?.color ?? '#A8A29E' }}
          aria-hidden
        >
          {name.trim().charAt(0).toUpperCase()}
        </span>
      )}
    </span>
  );
}
