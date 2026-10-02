import { useEffect, useRef, useState, useCallback } from 'react';
import { api } from '../api/client';

/**
 * Connects to /ws/tenant/{tenantId} with the access token as a query param
 * (the browser WebSocket API can't set custom headers, so this is the
 * standard approach). Reconnects with backoff if the connection drops —
 * important on free-tier hosts where the backend can cold-sleep.
 */
export function useTenantSocket(tenantId, onEvent) {
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const retryDelay = useRef(1000);

  const send = useCallback((payload) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(payload));
    }
  }, []);

  useEffect(() => {
    if (!tenantId) return;
    let cancelled = false;

    function connect() {
      const { access } = api.getTokens();
      if (!access) return;
      const wsBase = api.API_BASE.replace(/^http/, 'ws');
      const ws = new WebSocket(`${wsBase}/ws/tenant/${tenantId}?token=${access}`);
      wsRef.current = ws;

      ws.onopen = () => {
        if (cancelled) return;
        setConnected(true);
        retryDelay.current = 1000; // reset backoff on a healthy connection
      };
      ws.onmessage = (msg) => {
        try {
          onEvent(JSON.parse(msg.data));
        } catch {
          // ignore malformed frames
        }
      };
      ws.onclose = () => {
        setConnected(false);
        if (cancelled) return;
        // Reconnect with capped exponential backoff — handles a
        // free-tier backend cold-starting after being asleep.
        setTimeout(connect, retryDelay.current);
        retryDelay.current = Math.min(retryDelay.current * 2, 15000);
      };
    }

    connect();
    return () => {
      cancelled = true;
      wsRef.current?.close();
    };
  }, [tenantId, onEvent]);

  return { connected, send };
}
