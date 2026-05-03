import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

import { COLOR_MAP } from './constants';

export const baseUrl = import.meta.env.VITE_SITE_URL || 'http://localhost:5173';

export const createUrl = (pathname, params) => {
  const paramsString = params.toString();
  const queryString = `${paramsString.length ? '?' : ''}${paramsString}`;

  return `${pathname}${queryString}`;
};

export const ensureStartsWith = (stringToCheck, startsWith) =>
  stringToCheck.startsWith(startsWith) ? stringToCheck : `${startsWith}${stringToCheck}`;

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

export const getColorHex = (colorName) => {
  // Check if colorName contains a slash for split colors
  if (colorName.includes('/')) {
    const parts = colorName.split('/');
    if (parts.length === 2) {
      const firstColor = parts[0].toLowerCase().replace(/[^a-z-]/g, '');
      const secondColor = parts[1].toLowerCase().replace(/[^a-z-]/g, '');
      return [COLOR_MAP[firstColor] || '#9ca3af', COLOR_MAP[secondColor] || '#9ca3af'];
    }
  }

  // Handle single color case
  const normalizedName = colorName.toLowerCase().replace(/[^a-z-]/g, '');
  return COLOR_MAP[normalizedName] || '#9ca3af'; // Default to gray if not found
};

export const getLabelPosition = (index) => {
  const positions = ['top-left', 'bottom-right', 'top-right', 'bottom-left'];

  return positions[index % positions.length];
};
