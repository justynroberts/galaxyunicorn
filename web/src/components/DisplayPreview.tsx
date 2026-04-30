import { useRef, useEffect } from 'react';
import { DISPLAY_WIDTH, DISPLAY_HEIGHT } from '../types/display';

interface Props {
  pixels: Uint8Array;
  className?: string;
}

const CELL_SIZE = 12;
const GAP = 2;
const DOT_RADIUS = 4;

export function DisplayPreview({ pixels, className = '' }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const totalW = DISPLAY_WIDTH * (CELL_SIZE + GAP) + GAP;
  const totalH = DISPLAY_HEIGHT * (CELL_SIZE + GAP) + GAP;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d')!;

    ctx.fillStyle = '#0a0a0a';
    ctx.fillRect(0, 0, totalW, totalH);

    for (let y = 0; y < DISPLAY_HEIGHT; y++) {
      for (let x = 0; x < DISPLAY_WIDTH; x++) {
        const idx = (y * DISPLAY_WIDTH + x) * 3;
        const r = pixels[idx] || 0;
        const g = pixels[idx + 1] || 0;
        const b = pixels[idx + 2] || 0;

        const cx = GAP + x * (CELL_SIZE + GAP) + CELL_SIZE / 2;
        const cy = GAP + y * (CELL_SIZE + GAP) + CELL_SIZE / 2;

        // Glow effect for lit pixels
        if (r > 20 || g > 20 || b > 20) {
          const gradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, DOT_RADIUS + 3);
          gradient.addColorStop(0, `rgba(${r}, ${g}, ${b}, 0.4)`);
          gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
          ctx.fillStyle = gradient;
          ctx.fillRect(cx - DOT_RADIUS - 3, cy - DOT_RADIUS - 3,
            (DOT_RADIUS + 3) * 2, (DOT_RADIUS + 3) * 2);
        }

        // LED dot
        ctx.beginPath();
        ctx.arc(cx, cy, DOT_RADIUS, 0, Math.PI * 2);
        ctx.fillStyle = r > 5 || g > 5 || b > 5
          ? `rgb(${r}, ${g}, ${b})`
          : '#1a1a1a';
        ctx.fill();
      }
    }
  }, [pixels, totalW, totalH]);

  return (
    <div className={`inline-block rounded-lg overflow-hidden border border-surface-600 ${className}`}>
      <canvas
        ref={canvasRef}
        width={totalW}
        height={totalH}
        style={{ width: totalW, height: totalH }}
      />
    </div>
  );
}
