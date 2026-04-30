import { useRef, useEffect, useCallback, useState } from 'react';
import type { RGB } from '../types/display';
import { DISPLAY_WIDTH, DISPLAY_HEIGHT } from '../types/display';
import { ColorPicker } from './ColorPicker';
import { DisplayPreview } from './DisplayPreview';
import { rgbToBase64 } from '../lib/imageProcessor';
import { sendPixels } from '../lib/api';
import { usePixelGrid } from '../hooks/usePixelGrid';

type Tool = 'pencil' | 'eraser' | 'fill';

interface Props {
  baseUrl: string;
  connected: boolean;
}

const CELL_SIZE = 14;
const GAP = 1;

export function PixelArtEditor({ baseUrl, connected }: Props) {
  const { grid, setPixel, fill, clearGrid, undo, redo, pushUndo, canUndo, canRedo } = usePixelGrid();
  const [color, setColor] = useState<RGB>([255, 255, 255]);
  const [tool, setTool] = useState<Tool>('pencil');
  const [sending, setSending] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const paintingRef = useRef(false);
  const lastPosRef = useRef<[number, number] | null>(null);

  const totalW = DISPLAY_WIDTH * (CELL_SIZE + GAP) + GAP;
  const totalH = DISPLAY_HEIGHT * (CELL_SIZE + GAP) + GAP;

  // Render grid
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d')!;

    ctx.fillStyle = '#1a1a1a';
    ctx.fillRect(0, 0, totalW, totalH);

    for (let y = 0; y < DISPLAY_HEIGHT; y++) {
      for (let x = 0; x < DISPLAY_WIDTH; x++) {
        const idx = (y * DISPLAY_WIDTH + x) * 3;
        const r = grid[idx];
        const g = grid[idx + 1];
        const b = grid[idx + 2];
        const px = GAP + x * (CELL_SIZE + GAP);
        const py = GAP + y * (CELL_SIZE + GAP);

        ctx.fillStyle = r > 0 || g > 0 || b > 0
          ? `rgb(${r},${g},${b})`
          : '#222';
        ctx.fillRect(px, py, CELL_SIZE, CELL_SIZE);
      }
    }
  }, [grid, totalW, totalH]);

  const getGridPos = useCallback((e: React.MouseEvent<HTMLCanvasElement>): [number, number] | null => {
    const rect = canvasRef.current!.getBoundingClientRect();
    const scaleX = totalW / rect.width;
    const scaleY = totalH / rect.height;
    const mx = (e.clientX - rect.left) * scaleX;
    const my = (e.clientY - rect.top) * scaleY;

    const x = Math.floor((mx - GAP) / (CELL_SIZE + GAP));
    const y = Math.floor((my - GAP) / (CELL_SIZE + GAP));
    if (x >= 0 && x < DISPLAY_WIDTH && y >= 0 && y < DISPLAY_HEIGHT) {
      return [x, y];
    }
    return null;
  }, [totalW, totalH]);

  const applyTool = useCallback((x: number, y: number) => {
    if (tool === 'pencil') {
      setPixel(x, y, color);
    } else if (tool === 'eraser') {
      setPixel(x, y, [0, 0, 0]);
    } else if (tool === 'fill') {
      fill(x, y, color);
    }
  }, [tool, color, setPixel, fill]);

  const handleMouseDown = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const pos = getGridPos(e);
    if (!pos) return;
    pushUndo();
    paintingRef.current = true;
    lastPosRef.current = pos;
    applyTool(pos[0], pos[1]);
  }, [getGridPos, applyTool, pushUndo]);

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!paintingRef.current) return;
    const pos = getGridPos(e);
    if (!pos) return;
    if (lastPosRef.current && pos[0] === lastPosRef.current[0] && pos[1] === lastPosRef.current[1]) return;
    lastPosRef.current = pos;
    if (tool !== 'fill') {
      applyTool(pos[0], pos[1]);
    }
  }, [getGridPos, applyTool, tool]);

  const handleMouseUp = useCallback(() => {
    paintingRef.current = false;
    lastPosRef.current = null;
  }, []);

  const handleSend = async () => {
    setSending(true);
    try {
      await sendPixels(baseUrl, rgbToBase64(grid));
    } catch { /* ignore */ }
    setSending(false);
  };

  const tools: { id: Tool; label: string; icon: string }[] = [
    { id: 'pencil', label: 'Pencil', icon: 'M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931z' },
    { id: 'eraser', label: 'Eraser', icon: 'M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88' },
    { id: 'fill', label: 'Fill', icon: 'M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z' },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 flex-wrap">
        {tools.map(t => (
          <button
            key={t.id}
            onClick={() => setTool(t.id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors ${
              tool === t.id ? 'bg-white text-black' : 'bg-surface-700 text-gray-300 hover:bg-surface-600'
            }`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
              <path strokeLinecap="round" strokeLinejoin="round" d={t.icon} />
            </svg>
            {t.label}
          </button>
        ))}
        <div className="flex-1" />
        <button
          onClick={undo}
          disabled={!canUndo}
          className="px-2 py-1.5 rounded text-sm bg-surface-700 text-gray-400 hover:bg-surface-600 disabled:opacity-30"
          title="Undo"
        >
          Undo
        </button>
        <button
          onClick={redo}
          disabled={!canRedo}
          className="px-2 py-1.5 rounded text-sm bg-surface-700 text-gray-400 hover:bg-surface-600 disabled:opacity-30"
          title="Redo"
        >
          Redo
        </button>
        <button
          onClick={clearGrid}
          className="px-2 py-1.5 rounded text-sm bg-surface-700 text-red-400 hover:bg-red-500/10"
        >
          Clear
        </button>
      </div>

      <div className="flex gap-5">
        <div className="flex-1">
          <canvas
            ref={canvasRef}
            width={totalW}
            height={totalH}
            style={{ width: '100%', height: 'auto', cursor: 'crosshair' }}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
          />
        </div>
        <div className="w-48 shrink-0">
          <label className="block text-sm font-medium text-gray-400 mb-1.5">Color</label>
          <ColorPicker color={color} onChange={setColor} />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-400 mb-1.5">Preview</label>
        <DisplayPreview pixels={grid} />
      </div>

      <button
        onClick={handleSend}
        disabled={!connected || sending}
        className="w-full bg-white text-black font-semibold py-2.5 rounded-lg hover:bg-gray-200 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
      >
        {sending ? 'Sending...' : 'Send to Display'}
      </button>
    </div>
  );
}
