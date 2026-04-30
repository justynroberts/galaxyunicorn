import { useRef, useEffect, useCallback, useState } from 'react';
import type { RGB } from '../types/display';
import { PRESET_COLORS } from '../types/display';
import { hsvToRgb, rgbToHsv, rgbToHex, hexToRgb, rgbToCss } from '../lib/colorUtils';

interface Props {
  color: RGB;
  onChange: (color: RGB) => void;
}

export function ColorPicker({ color, onChange }: Props) {
  const svCanvasRef = useRef<HTMLCanvasElement>(null);
  const hueCanvasRef = useRef<HTMLCanvasElement>(null);
  const [hsv, setHsv] = useState(() => rgbToHsv(...color));
  const [hexInput, setHexInput] = useState(rgbToHex(...color));
  const draggingSV = useRef(false);
  const draggingHue = useRef(false);

  const SV_SIZE = 160;
  const HUE_W = 20;
  const HUE_H = SV_SIZE;

  // Draw SV canvas
  useEffect(() => {
    const canvas = svCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d')!;
    for (let x = 0; x < SV_SIZE; x++) {
      for (let y = 0; y < SV_SIZE; y++) {
        const s = x / SV_SIZE;
        const v = 1 - y / SV_SIZE;
        const [r, g, b] = hsvToRgb(hsv[0], s, v);
        ctx.fillStyle = `rgb(${r},${g},${b})`;
        ctx.fillRect(x, y, 1, 1);
      }
    }
    // Cursor
    const cx = hsv[1] * SV_SIZE;
    const cy = (1 - hsv[2]) * SV_SIZE;
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(cx, cy, 5, 0, Math.PI * 2);
    ctx.stroke();
    ctx.strokeStyle = '#000';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(cx, cy, 6, 0, Math.PI * 2);
    ctx.stroke();
  }, [hsv]);

  // Draw hue bar
  useEffect(() => {
    const canvas = hueCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d')!;
    for (let y = 0; y < HUE_H; y++) {
      const h = y / HUE_H;
      const [r, g, b] = hsvToRgb(h, 1, 1);
      ctx.fillStyle = `rgb(${r},${g},${b})`;
      ctx.fillRect(0, y, HUE_W, 1);
    }
    // Indicator
    const iy = hsv[0] * HUE_H;
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.strokeRect(0, iy - 2, HUE_W, 4);
  }, [hsv]);

  const updateFromHSV = useCallback((h: number, s: number, v: number) => {
    const newHsv: [number, number, number] = [h, s, v];
    setHsv(newHsv);
    const rgb = hsvToRgb(h, s, v);
    setHexInput(rgbToHex(...rgb));
    onChange(rgb);
  }, [onChange]);

  const handleSVMouse = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!draggingSV.current && e.type !== 'mousedown') return;
    const rect = svCanvasRef.current!.getBoundingClientRect();
    const s = Math.max(0, Math.min(1, (e.clientX - rect.left) / SV_SIZE));
    const v = Math.max(0, Math.min(1, 1 - (e.clientY - rect.top) / SV_SIZE));
    updateFromHSV(hsv[0], s, v);
  }, [hsv, updateFromHSV]);

  const handleHueMouse = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!draggingHue.current && e.type !== 'mousedown') return;
    const rect = hueCanvasRef.current!.getBoundingClientRect();
    const h = Math.max(0, Math.min(1, (e.clientY - rect.top) / HUE_H));
    updateFromHSV(h, hsv[1], hsv[2]);
  }, [hsv, updateFromHSV]);

  const handleHexChange = (hex: string) => {
    setHexInput(hex);
    if (/^#[0-9a-fA-F]{6}$/.test(hex)) {
      const rgb = hexToRgb(hex);
      setHsv(rgbToHsv(...rgb));
      onChange(rgb);
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <canvas
          ref={svCanvasRef}
          width={SV_SIZE}
          height={SV_SIZE}
          className="rounded cursor-crosshair"
          style={{ width: SV_SIZE, height: SV_SIZE }}
          onMouseDown={e => { draggingSV.current = true; handleSVMouse(e); }}
          onMouseMove={handleSVMouse}
          onMouseUp={() => draggingSV.current = false}
          onMouseLeave={() => draggingSV.current = false}
        />
        <canvas
          ref={hueCanvasRef}
          width={HUE_W}
          height={HUE_H}
          className="rounded cursor-pointer"
          style={{ width: HUE_W, height: HUE_H }}
          onMouseDown={e => { draggingHue.current = true; handleHueMouse(e); }}
          onMouseMove={handleHueMouse}
          onMouseUp={() => draggingHue.current = false}
          onMouseLeave={() => draggingHue.current = false}
        />
      </div>

      <div className="flex items-center gap-2">
        <div
          className="w-8 h-8 rounded border border-surface-500"
          style={{ backgroundColor: rgbToCss(...color) }}
        />
        <input
          type="text"
          value={hexInput}
          onChange={e => handleHexChange(e.target.value)}
          className="bg-surface-700 border border-surface-500 rounded px-2 py-1 text-sm font-mono text-gray-200 w-24"
        />
      </div>

      <div className="flex flex-wrap gap-1.5">
        {PRESET_COLORS.map(p => (
          <button
            key={p.name}
            onClick={() => {
              onChange(p.color);
              setHsv(rgbToHsv(...p.color));
              setHexInput(rgbToHex(...p.color));
            }}
            className="w-6 h-6 rounded border border-surface-500 hover:scale-110 transition-transform"
            style={{ backgroundColor: rgbToCss(...p.color) }}
            title={p.name}
          />
        ))}
      </div>
    </div>
  );
}
