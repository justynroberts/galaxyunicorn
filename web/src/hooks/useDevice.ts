import { useState, useEffect, useCallback, useRef } from 'react';
import type { DeviceStatus } from '../types/display';
import { getStatus } from '../lib/api';

const STORAGE_KEY = 'galactic-device-url';

function getInitialUrl(): string {
  try {
    return localStorage.getItem(STORAGE_KEY) || 'http://192.168.3.43';
  } catch {
    return 'http://192.168.3.43';
  }
}

export function useDevice() {
  const [baseUrl, setBaseUrlState] = useState(getInitialUrl);
  const [status, setStatus] = useState<DeviceStatus | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<number | null>(null);

  const setBaseUrl = useCallback((url: string) => {
    const cleaned = url.replace(/\/+$/, '');
    setBaseUrlState(cleaned);
    try {
      localStorage.setItem(STORAGE_KEY, cleaned);
    } catch { /* ignore */ }
  }, []);

  const poll = useCallback(async () => {
    try {
      const s = await getStatus(baseUrl);
      setStatus(s);
      setConnected(true);
      setError(null);
    } catch {
      setConnected(false);
      setError('Device unreachable');
    }
  }, [baseUrl]);

  useEffect(() => {
    poll();
    intervalRef.current = window.setInterval(poll, 3000);
    return () => {
      if (intervalRef.current) window.clearInterval(intervalRef.current);
    };
  }, [poll]);

  return { baseUrl, setBaseUrl, status, connected, error, refresh: poll };
}
