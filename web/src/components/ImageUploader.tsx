import { useState, useCallback, useRef } from 'react';
import { DISPLAY_WIDTH, DISPLAY_HEIGHT } from '../types/display';
import { DisplayPreview } from './DisplayPreview';
import { processImage, rgbToBase64, type FitMode } from '../lib/imageProcessor';
import { sendPixels } from '../lib/api';

interface Props {
  baseUrl: string;
  connected: boolean;
}

export function ImageUploader({ baseUrl, connected }: Props) {
  const [preview, setPreview] = useState<Uint8Array | null>(null);
  const [imgSrc, setImgSrc] = useState<string | null>(null);
  const [fitMode, setFitMode] = useState<FitMode>('crop');
  const [dither, setDither] = useState(false);
  const [sending, setSending] = useState(false);
  const [dragging, setDragging] = useState(false);
  const imgRef = useRef<HTMLImageElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const processAndPreview = useCallback((img: HTMLImageElement, fit: FitMode, useDither: boolean) => {
    imgRef.current = img;
    const rgb = processImage(img, fit, useDither);
    setPreview(rgb);
  }, []);

  const handleFile = useCallback((file: File) => {
    if (!file.type.startsWith('image/')) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      const src = e.target?.result as string;
      setImgSrc(src);
      const img = new Image();
      img.onload = () => processAndPreview(img, fitMode, dither);
      img.src = src;
    };
    reader.readAsDataURL(file);
  }, [fitMode, dither, processAndPreview]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const handleFitChange = useCallback((newFit: FitMode) => {
    setFitMode(newFit);
    if (imgRef.current) processAndPreview(imgRef.current, newFit, dither);
  }, [dither, processAndPreview]);

  const handleDitherChange = useCallback((newDither: boolean) => {
    setDither(newDither);
    if (imgRef.current) processAndPreview(imgRef.current, fitMode, newDither);
  }, [fitMode, processAndPreview]);

  const handleSend = async () => {
    if (!preview) return;
    setSending(true);
    try {
      await sendPixels(baseUrl, rgbToBase64(preview));
    } catch { /* ignore */ }
    setSending(false);
  };

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        onDragOver={e => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          dragging ? 'border-white bg-surface-700' : 'border-surface-500 hover:border-gray-400'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])}
        />
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-10 h-10 text-gray-500 mx-auto mb-2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
        </svg>
        <p className="text-gray-400">Drop an image here or click to browse</p>
        <p className="text-xs text-gray-600 mt-1">
          Will be resized to {DISPLAY_WIDTH}x{DISPLAY_HEIGHT} pixels
        </p>
      </div>

      {imgSrc && (
        <div className="flex gap-4">
          <div className="shrink-0">
            <label className="block text-sm font-medium text-gray-400 mb-1.5">Original</label>
            <img src={imgSrc} alt="Original" className="max-w-48 max-h-32 rounded border border-surface-600 object-contain" />
          </div>
          <div className="space-y-3 flex-1">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1.5">Fit Mode</label>
              <div className="flex gap-2">
                {(['stretch', 'fit', 'crop'] as FitMode[]).map(mode => (
                  <button
                    key={mode}
                    onClick={() => handleFitChange(mode)}
                    className={`px-3 py-1.5 rounded-lg text-sm capitalize transition-colors ${
                      fitMode === mode ? 'bg-white text-black' : 'bg-surface-700 text-gray-300 hover:bg-surface-600'
                    }`}
                  >
                    {mode}
                  </button>
                ))}
              </div>
            </div>
            <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
              <input
                type="checkbox"
                checked={dither}
                onChange={e => handleDitherChange(e.target.checked)}
                className="rounded bg-surface-700 border-surface-500"
              />
              Floyd-Steinberg dithering
            </label>
          </div>
        </div>
      )}

      {preview && (
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1.5">Preview ({DISPLAY_WIDTH}x{DISPLAY_HEIGHT})</label>
          <DisplayPreview pixels={preview} />
        </div>
      )}

      <button
        onClick={handleSend}
        disabled={!connected || sending || !preview}
        className="w-full bg-white text-black font-semibold py-2.5 rounded-lg hover:bg-gray-200 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
      >
        {sending ? 'Sending...' : 'Send to Display'}
      </button>
    </div>
  );
}
