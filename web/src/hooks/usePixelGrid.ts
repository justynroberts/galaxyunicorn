import { useState, useCallback, useRef } from 'react';
import { DISPLAY_WIDTH, DISPLAY_HEIGHT, TOTAL_PIXELS, type RGB } from '../types/display';

export function usePixelGrid() {
  const [grid, setGrid] = useState(() => new Uint8Array(TOTAL_PIXELS * 3));
  const undoStack = useRef<Uint8Array[]>([]);
  const redoStack = useRef<Uint8Array[]>([]);

  const pushUndo = useCallback(() => {
    undoStack.current.push(new Uint8Array(grid));
    if (undoStack.current.length > 20) undoStack.current.shift();
    redoStack.current = [];
  }, [grid]);

  const setPixel = useCallback((x: number, y: number, color: RGB) => {
    setGrid(prev => {
      const next = new Uint8Array(prev);
      const idx = (y * DISPLAY_WIDTH + x) * 3;
      next[idx] = color[0];
      next[idx + 1] = color[1];
      next[idx + 2] = color[2];
      return next;
    });
  }, []);

  const fill = useCallback((startX: number, startY: number, color: RGB) => {
    setGrid(prev => {
      const next = new Uint8Array(prev);
      const targetIdx = (startY * DISPLAY_WIDTH + startX) * 3;
      const targetR = prev[targetIdx];
      const targetG = prev[targetIdx + 1];
      const targetB = prev[targetIdx + 2];

      if (targetR === color[0] && targetG === color[1] && targetB === color[2]) return prev;

      const stack: [number, number][] = [[startX, startY]];
      const visited = new Set<number>();

      while (stack.length > 0) {
        const [x, y] = stack.pop()!;
        const key = y * DISPLAY_WIDTH + x;
        if (visited.has(key)) continue;
        if (x < 0 || x >= DISPLAY_WIDTH || y < 0 || y >= DISPLAY_HEIGHT) continue;

        const idx = key * 3;
        if (next[idx] !== targetR || next[idx + 1] !== targetG || next[idx + 2] !== targetB) continue;

        visited.add(key);
        next[idx] = color[0];
        next[idx + 1] = color[1];
        next[idx + 2] = color[2];

        stack.push([x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]);
      }
      return next;
    });
  }, []);

  const clearGrid = useCallback(() => {
    pushUndo();
    setGrid(new Uint8Array(TOTAL_PIXELS * 3));
  }, [pushUndo]);

  const undo = useCallback(() => {
    const prev = undoStack.current.pop();
    if (prev) {
      redoStack.current.push(new Uint8Array(grid) as Uint8Array<ArrayBuffer>);
      setGrid(prev as Uint8Array<ArrayBuffer>);
    }
  }, [grid]);

  const redo = useCallback(() => {
    const next = redoStack.current.pop();
    if (next) {
      undoStack.current.push(new Uint8Array(grid) as Uint8Array<ArrayBuffer>);
      setGrid(next as Uint8Array<ArrayBuffer>);
    }
  }, [grid]);

  const loadPixels = useCallback((pixels: Uint8Array) => {
    pushUndo();
    setGrid(new Uint8Array(pixels));
  }, [pushUndo]);

  return {
    grid,
    setPixel,
    fill,
    clearGrid,
    undo,
    redo,
    pushUndo,
    loadPixels,
    canUndo: undoStack.current.length > 0,
    canRedo: redoStack.current.length > 0,
  };
}
