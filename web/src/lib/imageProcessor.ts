import { DISPLAY_WIDTH, DISPLAY_HEIGHT, TOTAL_PIXELS } from '../types/display';

export type FitMode = 'stretch' | 'fit' | 'crop';

export function processImage(
  img: HTMLImageElement,
  fitMode: FitMode = 'stretch',
  dither: boolean = false
): Uint8Array {
  const canvas = document.createElement('canvas');
  canvas.width = DISPLAY_WIDTH;
  canvas.height = DISPLAY_HEIGHT;
  const ctx = canvas.getContext('2d')!;

  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';

  // Clear to black
  ctx.fillStyle = '#000';
  ctx.fillRect(0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT);

  if (fitMode === 'stretch') {
    ctx.drawImage(img, 0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT);
  } else if (fitMode === 'fit') {
    const scale = Math.min(DISPLAY_WIDTH / img.width, DISPLAY_HEIGHT / img.height);
    const w = img.width * scale;
    const h = img.height * scale;
    const x = (DISPLAY_WIDTH - w) / 2;
    const y = (DISPLAY_HEIGHT - h) / 2;
    ctx.drawImage(img, x, y, w, h);
  } else {
    // crop: fill and center-crop
    const scale = Math.max(DISPLAY_WIDTH / img.width, DISPLAY_HEIGHT / img.height);
    const w = img.width * scale;
    const h = img.height * scale;
    const x = (DISPLAY_WIDTH - w) / 2;
    const y = (DISPLAY_HEIGHT - h) / 2;
    ctx.drawImage(img, x, y, w, h);
  }

  const imageData = ctx.getImageData(0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT);

  if (dither) {
    floydSteinbergDither(imageData);
  }

  // Convert RGBA to RGB
  const rgb = new Uint8Array(TOTAL_PIXELS * 3);
  for (let i = 0; i < TOTAL_PIXELS; i++) {
    rgb[i * 3] = imageData.data[i * 4];
    rgb[i * 3 + 1] = imageData.data[i * 4 + 1];
    rgb[i * 3 + 2] = imageData.data[i * 4 + 2];
  }
  return rgb;
}

function floydSteinbergDither(imageData: ImageData) {
  const { data, width, height } = imageData;
  const levels = 4; // quantize to N levels per channel

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const idx = (y * width + x) * 4;
      for (let c = 0; c < 3; c++) {
        const old = data[idx + c];
        const quantized = Math.round((old / 255) * (levels - 1)) * (255 / (levels - 1));
        const error = old - quantized;
        data[idx + c] = quantized;

        // Distribute error
        if (x + 1 < width) data[idx + 4 + c] += error * 7 / 16;
        if (y + 1 < height) {
          if (x > 0) data[idx + width * 4 - 4 + c] += error * 3 / 16;
          data[idx + width * 4 + c] += error * 5 / 16;
          if (x + 1 < width) data[idx + width * 4 + 4 + c] += error * 1 / 16;
        }
      }
    }
  }
}

export function rgbToBase64(rgb: Uint8Array): string {
  let binary = '';
  for (let i = 0; i < rgb.length; i++) {
    binary += String.fromCharCode(rgb[i]);
  }
  return btoa(binary);
}

export function pixelGridToRgb(grid: Uint8Array): Uint8Array {
  // grid is already in RGB format (width * height * 3)
  return grid;
}
