import { useState, useCallback } from 'react';
import { setBrightness } from '../lib/api';

interface Props {
  baseUrl: string;
  initialValue: number;
  connected: boolean;
}

export function BrightnessSlider({ baseUrl, initialValue, connected }: Props) {
  const [value, setValue] = useState(initialValue);

  const handleChange = useCallback(async (newValue: number) => {
    setValue(newValue);
    if (connected) {
      try {
        await setBrightness(baseUrl, { value: newValue });
      } catch { /* ignore */ }
    }
  }, [baseUrl, connected]);

  return (
    <div className="flex items-center gap-3">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4 text-gray-500">
        <path d="M10 2a.75.75 0 01.75.75v1.5a.75.75 0 01-1.5 0v-1.5A.75.75 0 0110 2zM10 15a.75.75 0 01.75.75v1.5a.75.75 0 01-1.5 0v-1.5A.75.75 0 0110 15zM10 7a3 3 0 100 6 3 3 0 000-6zM15.657 5.404a.75.75 0 10-1.06-1.06l-1.061 1.06a.75.75 0 001.06 1.06l1.06-1.06zM6.464 14.596a.75.75 0 10-1.06-1.06l-1.06 1.06a.75.75 0 001.06 1.06l1.06-1.06zM18 10a.75.75 0 01-.75.75h-1.5a.75.75 0 010-1.5h1.5A.75.75 0 0118 10zM5 10a.75.75 0 01-.75.75h-1.5a.75.75 0 010-1.5h1.5A.75.75 0 015 10zM14.596 15.657a.75.75 0 001.06-1.06l-1.06-1.061a.75.75 0 10-1.06 1.06l1.06 1.06zM5.404 6.464a.75.75 0 001.06-1.06l-1.06-1.06a.75.75 0 10-1.06 1.06l1.06 1.06z" />
      </svg>
      <input
        type="range"
        min={0}
        max={1}
        step={0.05}
        value={value}
        onChange={e => handleChange(parseFloat(e.target.value))}
        className="w-28"
        disabled={!connected}
      />
      <span className="text-xs text-gray-500 w-8 text-right">{Math.round(value * 100)}%</span>
    </div>
  );
}
