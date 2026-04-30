import { useState, useRef, useCallback, useEffect } from 'react';
import { TOTAL_PIXELS } from '../types/display';
import { ANIMATIONS, type Animation } from '../lib/animations';
import { DisplayPreview } from './DisplayPreview';
import { rgbToBase64 } from '../lib/imageProcessor';
import { sendPixels } from '../lib/api';

interface Props {
  baseUrl: string;
  connected: boolean;
}

export function AnimationPlayer({ baseUrl, connected }: Props) {
  const [selected, setSelected] = useState<Animation>(ANIMATIONS[0]);
  const [playing, setPlaying] = useState(false);
  const [fps, setFps] = useState(8);
  const [preview, setPreview] = useState(() => new Uint8Array(TOTAL_PIXELS * 3));
  const frameRef = useRef(0);
  const timerRef = useRef<number | null>(null);
  const sendingRef = useRef(false);
  const pixelsRef = useRef(new Uint8Array(TOTAL_PIXELS * 3));

  const tick = useCallback(async () => {
    if (sendingRef.current) return;

    const pixels = pixelsRef.current;
    selected.fn(frameRef.current, pixels);
    frameRef.current++;

    // Update preview
    setPreview(new Uint8Array(pixels));

    // Send to device
    if (connected) {
      sendingRef.current = true;
      try {
        await sendPixels(baseUrl, rgbToBase64(pixels));
      } catch {
        // Device might be slow, skip frame
      }
      sendingRef.current = false;
    }
  }, [selected, baseUrl, connected]);

  const start = useCallback(() => {
    if (playing) return;
    frameRef.current = 0;
    pixelsRef.current.fill(0);
    setPlaying(true);
  }, [playing]);

  const stop = useCallback(() => {
    setPlaying(false);
    if (timerRef.current) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
    frameRef.current = 0;
    pixelsRef.current.fill(0);
    setPreview(new Uint8Array(TOTAL_PIXELS * 3));
  }, []);

  useEffect(() => {
    if (playing) {
      timerRef.current = window.setInterval(tick, 1000 / fps);
    }
    return () => {
      if (timerRef.current) {
        window.clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [playing, tick, fps]);

  // Reset when animation changes
  useEffect(() => {
    const wasPlaying = playing;
    if (timerRef.current) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
    frameRef.current = 0;
    pixelsRef.current.fill(0);
    setPreview(new Uint8Array(TOTAL_PIXELS * 3));
    if (wasPlaying) {
      setPlaying(false);
      // Restart after brief reset
      setTimeout(() => setPlaying(true), 50);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected]);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {ANIMATIONS.map(anim => (
          <button
            key={anim.name}
            onClick={() => setSelected(anim)}
            className={`p-3 rounded-lg border text-left transition-all ${
              selected.name === anim.name
                ? 'bg-surface-600 border-white/30'
                : 'bg-surface-700 border-surface-500 hover:border-gray-400'
            }`}
          >
            <div className="font-medium text-sm text-gray-200 capitalize">{anim.name}</div>
            <div className="text-xs text-gray-500 mt-0.5">{anim.description}</div>
          </button>
        ))}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-400 mb-1.5">Preview</label>
        <DisplayPreview pixels={preview} />
      </div>

      <div className="flex items-center gap-4">
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-400 mb-1.5">
            FPS: {fps}
          </label>
          <input
            type="range"
            min={2}
            max={15}
            value={fps}
            onChange={e => setFps(parseInt(e.target.value))}
            className="w-full"
          />
        </div>
        <div className="text-xs text-gray-600 w-24">
          {playing && (
            <span>Frame {frameRef.current}</span>
          )}
        </div>
      </div>

      <div className="flex gap-3">
        {!playing ? (
          <button
            onClick={start}
            disabled={!connected}
            className="flex-1 bg-white text-black font-semibold py-2.5 rounded-lg hover:bg-gray-200 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            Play
          </button>
        ) : (
          <button
            onClick={stop}
            className="flex-1 bg-surface-700 border border-red-500/30 text-red-400 font-medium py-2.5 rounded-lg hover:bg-red-500/10 transition-colors"
          >
            Stop
          </button>
        )}
      </div>
    </div>
  );
}
