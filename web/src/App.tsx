import { useState } from 'react';
import { useDevice } from './hooks/useDevice';
import { DeviceStatus } from './components/DeviceStatus';
import { BrightnessSlider } from './components/BrightnessSlider';
import { MessageComposer } from './components/MessageComposer';
import { EffectSelector } from './components/EffectSelector';
import { PixelArtEditor } from './components/PixelArtEditor';
import { ImageUploader } from './components/ImageUploader';
import { AnimationPlayer } from './components/AnimationPlayer';
import { clearDisplay } from './lib/api';

type Tab = 'message' | 'effects' | 'animate' | 'pixel' | 'image';

const TABS: { id: Tab; label: string }[] = [
  { id: 'message', label: 'Message' },
  { id: 'effects', label: 'Effects' },
  { id: 'animate', label: 'Animate' },
  { id: 'pixel', label: 'Pixel Art' },
  { id: 'image', label: 'Image' },
];

export default function App() {
  const { baseUrl, setBaseUrl, status, connected, error } = useDevice();
  const [activeTab, setActiveTab] = useState<Tab>('message');

  return (
    <div className="min-h-screen bg-surface-900">
      {/* Header */}
      <header className="border-b border-surface-700 bg-surface-800/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="white" className="w-4 h-4">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
                </svg>
              </div>
              <h1 className="text-lg font-semibold text-white">Galactic Unicorn</h1>
            </div>
            <div className="flex items-center gap-4">
              <BrightnessSlider
                baseUrl={baseUrl}
                initialValue={status?.brightness ?? 0.5}
                connected={connected}
              />
              <button
                onClick={() => clearDisplay(baseUrl)}
                disabled={!connected}
                className="px-3 py-1.5 rounded-lg text-sm bg-surface-700 text-gray-400 hover:bg-surface-600 disabled:opacity-30 transition-colors"
              >
                Clear
              </button>
            </div>
          </div>
          <div className="mt-2">
            <DeviceStatus
              connected={connected}
              status={status}
              error={error}
              baseUrl={baseUrl}
              onBaseUrlChange={setBaseUrl}
            />
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className="max-w-4xl mx-auto px-4">
        <div className="flex border-b border-surface-700 mt-2">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-white text-white'
                  : 'border-transparent text-gray-500 hover:text-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="py-6">
          {activeTab === 'message' && (
            <MessageComposer baseUrl={baseUrl} connected={connected} />
          )}
          {activeTab === 'effects' && (
            <EffectSelector
              baseUrl={baseUrl}
              connected={connected}
              activeEffect={status?.effect ?? null}
            />
          )}
          {activeTab === 'animate' && (
            <AnimationPlayer baseUrl={baseUrl} connected={connected} />
          )}
          {activeTab === 'pixel' && (
            <PixelArtEditor baseUrl={baseUrl} connected={connected} />
          )}
          {activeTab === 'image' && (
            <ImageUploader baseUrl={baseUrl} connected={connected} />
          )}
        </div>

        {/* Mode indicator */}
        {status && connected && (
          <div className="fixed bottom-4 right-4 bg-surface-700 border border-surface-500 rounded-lg px-3 py-2 text-xs text-gray-400">
            Mode: <span className="text-gray-200 font-medium">{status.mode}</span>
            {status.effect && (
              <> / <span className="text-gray-200 font-medium">{status.effect}</span></>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
