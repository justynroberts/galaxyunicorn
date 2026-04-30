import type { DeviceStatus, MessagePayload, EffectPayload, BrightnessPayload } from '../types/display';

let requestQueue: Promise<unknown> = Promise.resolve();

function enqueue<T>(fn: () => Promise<T>): Promise<T> {
  const result = requestQueue.then(fn, fn);
  requestQueue = result.then(() => {}, () => {});
  return result;
}

async function request<T>(baseUrl: string, path: string, method: string, body?: unknown): Promise<T> {
  const res = await fetch(`${baseUrl}${path}`, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
    signal: AbortSignal.timeout(5000),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || 'Request failed');
  }
  return res.json();
}

export function getStatus(baseUrl: string): Promise<DeviceStatus> {
  return enqueue(() => request<DeviceStatus>(baseUrl, '/status', 'GET'));
}

export function sendMessage(baseUrl: string, payload: MessagePayload) {
  return enqueue(() => request(baseUrl, '/message', 'POST', payload));
}

export function sendPixels(baseUrl: string, pixelsBase64: string) {
  return enqueue(() => request(baseUrl, '/pixels', 'POST', { pixels: pixelsBase64 }));
}

export function setEffect(baseUrl: string, payload: EffectPayload) {
  return enqueue(() => request(baseUrl, '/effect', 'POST', payload));
}

export function setBrightness(baseUrl: string, payload: BrightnessPayload) {
  return enqueue(() => request(baseUrl, '/brightness', 'POST', payload));
}

export function clearDisplay(baseUrl: string) {
  return enqueue(() => request(baseUrl, '/clear', 'POST'));
}
