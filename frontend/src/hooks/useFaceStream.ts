import { useCallback, useEffect, useRef, useState } from "react";

import { FaceStreamClient, type FaceStreamStatus } from "../lib/ws";
import type { FaceFrameMessage } from "../types/messages";

interface UseFaceStreamReturn {
  /** Current WS lifecycle status. */
  status: FaceStreamStatus;
  /** Most recent message from the server, or null if none yet. */
  latestMessage: FaceFrameMessage | null;
  /** Last error surfaced by the WS client, or null. */
  error: Error | null;
  /** Send a JPEG blob upstream. No-op if the connection isn't open. */
  send: (frame: Blob) => void;
}

/**
 * React hook around `FaceStreamClient`.
 *
 * Owns the WebSocket lifecycle: connects on mount, closes on unmount.
 * Re-establishes the connection if `url` changes. Updates React state
 * on every status change and incoming message so consumers re-render
 * accordingly.
 *
 * StrictMode-safe: client creation lives inside `useEffect`, so the
 * dev-mode double-mount tears down and rebuilds the socket cleanly.
 */
export function useFaceStream(url: string): UseFaceStreamReturn {
  const [status, setStatus] = useState<FaceStreamStatus>("idle");
  const [latestMessage, setLatestMessage] = useState<FaceFrameMessage | null>(
    null,
  );
  const [error, setError] = useState<Error | null>(null);

  // Ref instead of state — `send` reads through it and we don't want
  // identity churn on the exposed callback.
  const clientRef = useRef<FaceStreamClient | null>(null);

  useEffect(() => {
    const client = new FaceStreamClient(url, {
      onMessage: setLatestMessage,
      onStatusChange: setStatus,
      onError: setError,
    });
    clientRef.current = client;
    client.connect();

    return () => {
      client.close();
      clientRef.current = null;
    };
  }, [url]);

  // Stable identity (empty deps) — the ref provides the up-to-date client.
  const send = useCallback((frame: Blob) => {
    clientRef.current?.send(frame);
  }, []);

  return { status, latestMessage, error, send };
}