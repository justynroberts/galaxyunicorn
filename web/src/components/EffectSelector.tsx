import { useState } from 'react';
import { EFFECTS } from '../types/display';
import { setEffect, clearDisplay } from '../lib/api';

interface Props {
  baseUrl: string;
  connected: boolean;
  activeEffect: string | null;
}

const EFFECT_COLORS: Record<string, string> = {
  fire: 'border-orange-500/50 hover:border-orange-400',
  rainbow: 'border-purple-500/50 hover:border-purple-400',
  supercomputer: 'border-amber-500/50 hover:border-amber-400',
  retroprompt: 'border-blue-500/50 hover:border-blue-400',
};

const EFFECT_ICONS: Record<string, string> = {
  fire: 'M12.356 3.066a1 1 0 00-1.712 0c-.207.342-1.674 2.862-2.432 5.125C7.04 11.454 8.29 15 12 15c3.71 0 4.96-3.546 3.788-6.809-.758-2.263-2.225-4.783-2.432-5.125z',
  rainbow: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z',
  supercomputer: 'M9 17V7h2v10H9zm4 0V7h2v10h-2z',
  retroprompt: 'M4 5h16v14H4V5zm2 2v10h12V7H6z',
};

export function EffectSelector({ baseUrl, connected, activeEffect }: Props) {
  const [loading, setLoading] = useState<string | null>(null);

  const handleSelect = async (name: string) => {
    setLoading(name);
    try {
      if (activeEffect === name) {
        await clearDisplay(baseUrl);
      } else {
        await setEffect(baseUrl, { name });
      }
    } catch { /* ignore */ }
    setLoading(null);
  };

  const handleStop = async () => {
    setLoading('stop');
    try {
      await clearDisplay(baseUrl);
    } catch { /* ignore */ }
    setLoading(null);
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        {EFFECTS.map(effect => {
          const isActive = activeEffect === effect.name;
          return (
            <button
              key={effect.name}
              onClick={() => handleSelect(effect.name)}
              disabled={!connected || loading !== null}
              className={`p-4 rounded-lg border-2 text-left transition-all ${
                isActive
                  ? 'bg-surface-600 border-white/30'
                  : `bg-surface-700 ${EFFECT_COLORS[effect.name] || 'border-surface-500 hover:border-gray-400'}`
              } disabled:opacity-30 disabled:cursor-not-allowed`}
            >
              <div className="flex items-center gap-2 mb-1">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 text-gray-400">
                  <path d={EFFECT_ICONS[effect.name]} />
                </svg>
                <span className="font-semibold text-gray-200">{effect.label}</span>
                {isActive && (
                  <span className="ml-auto text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded">
                    Active
                  </span>
                )}
              </div>
              <p className="text-xs text-gray-500">{effect.description}</p>
            </button>
          );
        })}
      </div>

      {activeEffect && (
        <button
          onClick={handleStop}
          disabled={!connected || loading !== null}
          className="w-full bg-surface-700 border border-red-500/30 text-red-400 font-medium py-2 rounded-lg hover:bg-red-500/10 disabled:opacity-30 transition-colors"
        >
          {loading === 'stop' ? 'Stopping...' : 'Stop Effect'}
        </button>
      )}
    </div>
  );
}
