export type RGB = [number, number, number];

export interface DeviceStatus {
  mode: string;
  brightness: number;
  effect: string | null;
  ip: string;
  free_mem: number;
  uptime: number;
}

export interface MessagePayload {
  text: string;
  color: RGB;
  speed: number;
  scale: number;
  repeat: number;
  font: string;
}

export interface PixelsPayload {
  pixels: string; // base64 encoded
}

export interface EffectPayload {
  name: string;
}

export interface BrightnessPayload {
  value: number;
}

export const DISPLAY_WIDTH = 53;
export const DISPLAY_HEIGHT = 11;
export const TOTAL_PIXELS = DISPLAY_WIDTH * DISPLAY_HEIGHT;

export const EFFECTS = [
  { name: 'fire', label: 'Fire', description: 'Rising flame simulation with heat map' },
  { name: 'rainbow', label: 'Rainbow', description: 'Diagonal HSV rainbow stripes' },
  { name: 'supercomputer', label: 'Supercomputer', description: 'Blinking amber LEDs, retro mainframe' },
  { name: 'retroprompt', label: 'Retro Prompt', description: 'C64, Spectrum, BBC Micro boot screens' },
] as const;

export const FONTS = [
  { value: 'bitmap5', label: 'Bitmap 5px' },
  { value: 'bitmap6', label: 'Bitmap 6px' },
  { value: 'bitmap7', label: 'Bitmap 7px' },
  { value: 'bitmap8', label: 'Bitmap 8px' },
  { value: 'bitmap10', label: 'Bitmap 10px' },
  { value: 'font6', label: 'Font 6px' },
  { value: 'font8', label: 'Font 8px' },
  { value: 'font10', label: 'Font 10px' },
] as const;

export type EffectName = typeof EFFECTS[number]['name'];

export const PRESET_COLORS: { name: string; color: RGB }[] = [
  { name: 'White', color: [255, 255, 255] },
  { name: 'Red', color: [255, 0, 0] },
  { name: 'Green', color: [0, 255, 0] },
  { name: 'Blue', color: [0, 0, 255] },
  { name: 'Yellow', color: [255, 255, 0] },
  { name: 'Cyan', color: [0, 255, 255] },
  { name: 'Magenta', color: [255, 0, 255] },
  { name: 'Orange', color: [255, 165, 0] },
  { name: 'Purple', color: [128, 0, 255] },
  { name: 'Pink', color: [255, 105, 180] },
];
