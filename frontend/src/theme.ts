// Design tokens extracted from Stitch's tailwind.config block (light + dark modes)
// These are mirrored as CSS custom properties in inkwell.css for actual rendering.

export const LIGHT_TOKENS = {
  background:           '#fdf8f7',
  surface:              '#fdf8f7',
  surfaceContainer:     '#f2edeb',
  surfaceContainerHigh: '#ece7e6',
  onSurface:            '#1c1b1b',
  onSurfaceVariant:     '#4c463f',
  primary:              '#0b0704',
  outline:              '#7e766e',
  outlineVariant:       '#cfc5bc',
  inkFaint:             '#8A8377',
  mossReliable:         '#5C6E4A',
  rustUnreliable:       '#9C4A32',
} as const;

export const DARK_TOKENS = {
  background:           '#1a1816',
  surface:              '#1a1816',
  surfaceContainer:     '#24221f',
  surfaceContainerHigh: '#2e2b27',
  onSurface:            '#e3e0df',
  onSurfaceVariant:     '#cfc5bc',
  primary:              '#cfc5bd',
  outline:              '#9c938b',
  outlineVariant:       '#4c463f',
  inkFaint:             '#cfc5bc',
  mossReliable:         '#b9cda2',
  rustUnreliable:       '#ffb4a4',
} as const;

export type ClassificationStatus = 'verified' | 'flagged' | 'unverified' | 'inconclusive';

export interface StampConfig {
  label: string;
  lightColor: string;
  darkColor: string;
  lightBg: string;
  darkBg: string;
}

export const STAMP_CONFIGS: Record<ClassificationStatus, StampConfig> = {
  verified: {
    label: 'VERIFIED',
    lightColor: LIGHT_TOKENS.mossReliable,
    darkColor:  DARK_TOKENS.mossReliable,
    lightBg:    'rgba(92, 110, 74, 0.05)',
    darkBg:     'rgba(185, 205, 162, 0.1)',
  },
  // --- STUBS: full visuals added in future iteration ---
  flagged: {
    label: 'FLAGGED',
    lightColor: LIGHT_TOKENS.rustUnreliable,
    darkColor:  DARK_TOKENS.rustUnreliable,
    lightBg:    'rgba(156, 74, 50, 0.05)',
    darkBg:     'rgba(255, 180, 164, 0.1)',
  },
  unverified: {
    label: 'UNVERIFIED',
    lightColor: '#7c6f00',
    darkColor:  '#d4bc00',
    lightBg:    'rgba(180, 160, 0, 0.05)',
    darkBg:     'rgba(212, 188, 0, 0.1)',
  },
  inconclusive: {
    label: 'INCONCLUSIVE',
    lightColor: LIGHT_TOKENS.outline,
    darkColor:  DARK_TOKENS.outline,
    lightBg:    'rgba(126, 118, 110, 0.05)',
    darkBg:     'rgba(156, 147, 139, 0.1)',
  },
};

export function classificationToStatus(
  classification: string,
  authenticityScore: number,
): ClassificationStatus {
  if (classification === 'reliable' && authenticityScore >= 75) return 'verified';
  if (classification === 'unreliable') return 'flagged';
  if (classification === 'mixed') return 'unverified';
  return 'inconclusive';
}
