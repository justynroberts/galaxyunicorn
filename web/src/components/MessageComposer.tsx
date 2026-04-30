import { useState } from 'react';
import type { RGB } from '../types/display';
import { FONTS } from '../types/display';
import { ColorPicker } from './ColorPicker';
import { sendMessage } from '../lib/api';

interface Props {
  baseUrl: string;
  connected: boolean;
}

export function MessageComposer({ baseUrl, connected }: Props) {
  const [text, setText] = useState('');
  const [color, setColor] = useState<RGB>([0, 255, 0]);
  const [speed, setSpeed] = useState(2);
  const [scale, setScale] = useState(1);
  const [repeat, setRepeat] = useState(1);
  const [font, setFont] = useState('bitmap8');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSend = async () => {
    if (!text.trim()) return;
    setSending(true);
    setError(null);
    try {
      await sendMessage(baseUrl, { text: text.trim(), color, speed, scale, repeat, font });
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Send failed');
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="space-y-5">
      <div>
        <label className="block text-sm font-medium text-gray-400 mb-1.5">Message</label>
        <input
          type="text"
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          placeholder="Type your message..."
          className="w-full bg-surface-700 border border-surface-500 rounded-lg px-4 py-2.5 text-gray-100 placeholder-gray-600 focus:outline-none focus:border-gray-400"
        />
      </div>

      <div className="grid grid-cols-2 gap-5">
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1.5">Color</label>
          <ColorPicker color={color} onChange={setColor} />
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1.5">Font</label>
            <select
              value={font}
              onChange={e => setFont(e.target.value)}
              className="w-full bg-surface-700 border border-surface-500 rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:border-gray-400"
            >
              {FONTS.map(f => (
                <option key={f.value} value={f.value}>{f.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1.5">
              Speed: {speed}
            </label>
            <input
              type="range"
              min={1}
              max={5}
              value={speed}
              onChange={e => setSpeed(parseInt(e.target.value))}
              className="w-full"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1.5">
              Scale: {scale}
            </label>
            <input
              type="range"
              min={1}
              max={3}
              value={scale}
              onChange={e => setScale(parseInt(e.target.value))}
              className="w-full"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1.5">
              Repeat: {repeat === 0 ? 'Infinite' : repeat}
            </label>
            <input
              type="range"
              min={0}
              max={10}
              value={repeat}
              onChange={e => setRepeat(parseInt(e.target.value))}
              className="w-full"
            />
          </div>
        </div>
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      <button
        onClick={handleSend}
        disabled={!connected || sending || !text.trim()}
        className="w-full bg-white text-black font-semibold py-2.5 rounded-lg hover:bg-gray-200 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
      >
        {sending ? 'Sending...' : 'Send Message'}
      </button>
    </div>
  );
}
