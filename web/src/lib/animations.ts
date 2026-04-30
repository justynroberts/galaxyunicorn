import { DISPLAY_WIDTH, DISPLAY_HEIGHT } from '../types/display';

export type AnimationFn = (frame: number, pixels: Uint8Array) => void;

export interface Animation {
  name: string;
  description: string;
  fn: AnimationFn;
}

function hsvToRgb(h: number, s: number, v: number): [number, number, number] {
  const i = Math.floor(h * 6);
  const f = h * 6 - i;
  const p = v * (1 - s);
  const q = v * (1 - f * s);
  const t = v * (1 - (1 - f) * s);
  let r: number, g: number, b: number;
  switch (i % 6) {
    case 0: r = v; g = t; b = p; break;
    case 1: r = q; g = v; b = p; break;
    case 2: r = p; g = v; b = t; break;
    case 3: r = p; g = q; b = v; break;
    case 4: r = t; g = p; b = v; break;
    default: r = v; g = p; b = q; break;
  }
  return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
}

function setPx(pixels: Uint8Array, x: number, y: number, r: number, g: number, b: number) {
  if (x < 0 || x >= DISPLAY_WIDTH || y < 0 || y >= DISPLAY_HEIGHT) return;
  const idx = (y * DISPLAY_WIDTH + x) * 3;
  pixels[idx] = r;
  pixels[idx + 1] = g;
  pixels[idx + 2] = b;
}

const plasma: AnimationFn = (frame, pixels) => {
  const t = frame * 0.08;
  for (let y = 0; y < DISPLAY_HEIGHT; y++) {
    for (let x = 0; x < DISPLAY_WIDTH; x++) {
      const v1 = Math.sin(x * 0.3 + t);
      const v2 = Math.sin(y * 0.5 + t * 0.7);
      const v3 = Math.sin((x + y) * 0.2 + t * 0.5);
      const v4 = Math.sin(Math.sqrt(x * x + y * y) * 0.3 + t);
      const h = ((v1 + v2 + v3 + v4 + 4) / 8) % 1;
      const [r, g, b] = hsvToRgb(h, 1, 0.9);
      setPx(pixels, x, y, r, g, b);
    }
  }
};

const matrixRain: AnimationFn = (() => {
  const columns: { y: number; speed: number; length: number }[] = [];
  for (let x = 0; x < DISPLAY_WIDTH; x++) {
    columns.push({
      y: Math.random() * DISPLAY_HEIGHT * 2 - DISPLAY_HEIGHT,
      speed: 0.2 + Math.random() * 0.5,
      length: 3 + Math.floor(Math.random() * 6),
    });
  }
  return (_frame: number, pixels: Uint8Array) => {
    pixels.fill(0);
    for (let x = 0; x < DISPLAY_WIDTH; x++) {
      const col = columns[x];
      col.y += col.speed;
      if (col.y - col.length > DISPLAY_HEIGHT) {
        col.y = -col.length;
        col.speed = 0.2 + Math.random() * 0.5;
        col.length = 3 + Math.floor(Math.random() * 6);
      }
      for (let i = 0; i < col.length; i++) {
        const py = Math.floor(col.y - i);
        if (py >= 0 && py < DISPLAY_HEIGHT) {
          const brightness = 1 - (i / col.length);
          const g = i === 0 ? 255 : Math.round(180 * brightness);
          const r = i === 0 ? 200 : 0;
          setPx(pixels, x, py, r, g, 0);
        }
      }
    }
  };
})();

const colorWipe: AnimationFn = (frame, pixels) => {
  const totalSteps = DISPLAY_WIDTH * 3;
  const pos = frame % totalSteps;
  const colorIdx = Math.floor(pos / DISPLAY_WIDTH);
  const x = pos % DISPLAY_WIDTH;

  const colors: [number, number, number][] = [
    [255, 0, 0], [0, 255, 0], [0, 0, 255],
  ];
  const color = colors[colorIdx];

  for (let py = 0; py < DISPLAY_HEIGHT; py++) {
    setPx(pixels, x, py, color[0], color[1], color[2]);
  }
};

const sparkle: AnimationFn = (frame, pixels) => {
  // Fade existing pixels
  for (let i = 0; i < pixels.length; i++) {
    pixels[i] = Math.max(0, pixels[i] - 15);
  }
  // Add new sparkles
  const count = 3 + Math.floor(Math.sin(frame * 0.1) * 2 + 2);
  for (let i = 0; i < count; i++) {
    const x = Math.floor(Math.random() * DISPLAY_WIDTH);
    const y = Math.floor(Math.random() * DISPLAY_HEIGHT);
    const [r, g, b] = hsvToRgb(Math.random(), 0.3, 1);
    setPx(pixels, x, y, r, g, b);
  }
};

const bouncingBall: AnimationFn = (() => {
  let bx = 10, by = 5;
  let vx = 0.8, vy = 0.5;
  const trail: { x: number; y: number; age: number }[] = [];
  return (_frame: number, pixels: Uint8Array) => {
    pixels.fill(0);
    bx += vx;
    by += vy;
    if (bx <= 1 || bx >= DISPLAY_WIDTH - 2) vx = -vx;
    if (by <= 1 || by >= DISPLAY_HEIGHT - 2) vy = -vy;
    bx = Math.max(1, Math.min(DISPLAY_WIDTH - 2, bx));
    by = Math.max(1, Math.min(DISPLAY_HEIGHT - 2, by));

    trail.push({ x: Math.round(bx), y: Math.round(by), age: 0 });
    if (trail.length > 20) trail.shift();

    for (const t of trail) {
      t.age++;
      const brightness = Math.max(0, 1 - t.age / 20);
      const [r, g, b] = hsvToRgb(0.6, 1, brightness);
      setPx(pixels, t.x, t.y, r, g, b);
    }
    // Ball
    const rx = Math.round(bx);
    const ry = Math.round(by);
    setPx(pixels, rx, ry, 255, 255, 255);
    setPx(pixels, rx + 1, ry, 200, 200, 255);
    setPx(pixels, rx - 1, ry, 200, 200, 255);
    setPx(pixels, rx, ry + 1, 200, 200, 255);
    setPx(pixels, rx, ry - 1, 200, 200, 255);
  };
})();

const wave: AnimationFn = (frame, pixels) => {
  pixels.fill(0);
  const t = frame * 0.15;
  for (let x = 0; x < DISPLAY_WIDTH; x++) {
    const y1 = Math.round(5 + Math.sin(x * 0.2 + t) * 3);
    const y2 = Math.round(5 + Math.sin(x * 0.3 + t * 1.3 + 2) * 3);
    const y3 = Math.round(5 + Math.sin(x * 0.15 + t * 0.7 + 4) * 3);

    if (y1 >= 0 && y1 < DISPLAY_HEIGHT) setPx(pixels, x, y1, 0, 100, 255);
    if (y2 >= 0 && y2 < DISPLAY_HEIGHT) setPx(pixels, x, y2, 0, 255, 100);
    if (y3 >= 0 && y3 < DISPLAY_HEIGHT) setPx(pixels, x, y3, 255, 100, 0);

    // Fill below each wave
    for (let y = y1 + 1; y < DISPLAY_HEIGHT; y++) {
      const idx = (y * DISPLAY_WIDTH + x) * 3;
      pixels[idx] = Math.min(255, pixels[idx] + 0);
      pixels[idx + 1] = Math.min(255, pixels[idx + 1] + 15);
      pixels[idx + 2] = Math.min(255, pixels[idx + 2] + 40);
    }
  }
};

const pulse: AnimationFn = (frame, pixels) => {
  const t = frame * 0.06;
  const cx = DISPLAY_WIDTH / 2;
  const cy = DISPLAY_HEIGHT / 2;
  const maxR = Math.sqrt(cx * cx + cy * cy);

  for (let y = 0; y < DISPLAY_HEIGHT; y++) {
    for (let x = 0; x < DISPLAY_WIDTH; x++) {
      const dx = x - cx;
      const dy = (y - cy) * (DISPLAY_WIDTH / DISPLAY_HEIGHT); // aspect correct
      const dist = Math.sqrt(dx * dx + dy * dy);
      const v = Math.sin(dist * 0.8 - t * 3) * 0.5 + 0.5;
      const h = (dist / maxR + t * 0.2) % 1;
      const [r, g, b] = hsvToRgb(h, 1, v * 0.9);
      setPx(pixels, x, y, r, g, b);
    }
  }
};

const starfield: AnimationFn = (() => {
  const stars: { x: number; y: number; z: number }[] = [];
  for (let i = 0; i < 40; i++) {
    stars.push({
      x: (Math.random() - 0.5) * 200,
      y: (Math.random() - 0.5) * 200,
      z: Math.random() * 100,
    });
  }
  return (_frame: number, pixels: Uint8Array) => {
    pixels.fill(0);
    const cx = DISPLAY_WIDTH / 2;
    const cy = DISPLAY_HEIGHT / 2;
    for (const star of stars) {
      star.z -= 1.5;
      if (star.z <= 0) {
        star.x = (Math.random() - 0.5) * 200;
        star.y = (Math.random() - 0.5) * 200;
        star.z = 100;
      }
      const sx = Math.round(cx + star.x / star.z * 20);
      const sy = Math.round(cy + star.y / star.z * 10);
      const brightness = Math.round(255 * (1 - star.z / 100));
      if (sx >= 0 && sx < DISPLAY_WIDTH && sy >= 0 && sy < DISPLAY_HEIGHT) {
        setPx(pixels, sx, sy, brightness, brightness, brightness);
      }
    }
  };
})();

export const ANIMATIONS: Animation[] = [
  { name: 'plasma', description: 'Psychedelic plasma effect', fn: plasma },
  { name: 'matrix', description: 'Matrix digital rain', fn: matrixRain },
  { name: 'colorWipe', description: 'RGB color wipe across display', fn: colorWipe },
  { name: 'sparkle', description: 'Random sparkling pixels', fn: sparkle },
  { name: 'bounce', description: 'Bouncing ball with trail', fn: bouncingBall },
  { name: 'wave', description: 'Triple sine wave overlay', fn: wave },
  { name: 'pulse', description: 'Expanding rainbow rings', fn: pulse },
  { name: 'starfield', description: '3D starfield flythrough', fn: starfield },
];
