import { useState } from 'react';
import type { DeviceStatus as StatusType } from '../types/display';
import { resetWifi } from '../lib/api';

interface Props {
  connected: boolean;
  status: StatusType | null;
  error: string | null;
  baseUrl: string;
  onBaseUrlChange: (url: string) => void;
}

export function DeviceStatus({ connected, status, error, baseUrl, onBaseUrlChange }: Props) {
  const [editing, setEditing] = useState(false);
  const [urlInput, setUrlInput] = useState(baseUrl);

  const handleSave = () => {
    onBaseUrlChange(urlInput);
    setEditing(false);
  };

  const handleResetWifi = async () => {
    const confirmed = window.confirm(
      'Reset WiFi credentials? The display will reboot into setup mode and create a "GalacticUnicorn-Setup" network you can join to reconfigure.'
    );
    if (!confirmed) return;
    try {
      await resetWifi(baseUrl);
    } catch {
      // Device reboots before responding cleanly - this is expected
    }
  };

  return (
    <div className="flex items-center gap-3 text-sm">
      <div className="flex items-center gap-2">
        <div className={`w-2.5 h-2.5 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
        <span className="text-gray-400">
          {connected ? 'Connected' : 'Disconnected'}
        </span>
      </div>

      {editing ? (
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={urlInput}
            onChange={e => setUrlInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSave()}
            className="bg-surface-700 border border-surface-500 rounded px-2 py-1 text-sm text-gray-200 w-56 font-mono"
            autoFocus
          />
          <button onClick={handleSave} className="text-green-400 hover:text-green-300">
            Save
          </button>
          <button onClick={() => setEditing(false)} className="text-gray-500 hover:text-gray-300">
            Cancel
          </button>
        </div>
      ) : (
        <button
          onClick={() => { setUrlInput(baseUrl); setEditing(true); }}
          className="text-gray-500 hover:text-gray-300 font-mono text-xs"
          title="Click to change device address"
        >
          {baseUrl.replace('http://', '')}
        </button>
      )}

      {status && connected && (
        <span className="text-gray-600 text-xs">
          {Math.round(status.free_mem / 1024)}KB free
        </span>
      )}
      {error && !connected && (
        <span className="text-red-400 text-xs">{error}</span>
      )}

      {connected && (
        <button
          onClick={handleResetWifi}
          className="ml-auto text-xs text-gray-500 hover:text-red-400 border border-surface-500 hover:border-red-500/50 rounded px-2 py-1 transition-colors"
          title="Clear saved WiFi credentials and reboot into setup mode"
        >
          Reset WiFi
        </button>
      )}
    </div>
  );
}
