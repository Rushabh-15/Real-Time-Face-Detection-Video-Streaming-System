import type { FaceFrameMessage } from "../types/messages";

export type FaceStreamStatus =
  | "idle"
  | "connecting"
  | "open"
  | "closing"
  | "closed";

export interface FaceStreamCallbacks {
  onMessage: (msg: FaceFrameMessage) => void;
  onStatusChange?: (status: FaceStreamStatus) => void;
  onError?: (err: Error) => void;
}

/**
 * Thin WebSocket wrapper for the face-stream protocol.
 *
 * Outbound: binary JPEG frames via `send(blob)`.
 * Inbound: JSON `FaceFrameMessage` parsed and delivered via `onMessage`.
 *
 * This is a transport adapter, not a connection manager — no
 * reconnection, no buffering, no backoff. The React hook on top decides
 * those policies.
 */
export class FaceStreamClient {
  private ws: WebSocket | null = null;
  private status: FaceStreamStatus = "idle";

  constructor(
    private readonly url: string,
    private readonly callbacks: FaceStreamCallbacks,
  ) {}

  getStatus(): FaceStreamStatus {
    return this.status;
  }

  /** Open the WebSocket. Idempotent — second call is a no-op while a socket exists. */
  connect(): void {
    if (this.ws !== null) {
      return;
    }

    this.setStatus("connecting");
    const ws = new WebSocket(this.url);

    ws.addEventListener("open", () => {
      this.setStatus("open");
    });

    ws.addEventListener("message", (event) => {
      this.handleMessage(event);
    });

    ws.addEventListener("close", () => {
      this.ws = null;
      this.setStatus("closed");
    });

    ws.addEventListener("error", () => {
      // The browser only surfaces a generic Event on WS errors — no
      // useful detail. Wrap as a generic Error and let the caller decide.
      this.callbacks.onError?.(new Error("websocket error"));
    });

    this.ws = ws;
  }

  /** Send a JPEG blob upstream. Silently drops if not OPEN. */
  send(frame: Blob): void {
    if (this.ws === null || this.ws.readyState !== WebSocket.OPEN) {
      return;
    }
    this.ws.send(frame);
  }

  /** Initiate a clean close. The "closed" status fires after the browser confirms. */
  close(): void {
    if (this.ws === null) return;
    this.setStatus("closing");
    this.ws.close();
  }

  private handleMessage(event: MessageEvent): void {
    if (typeof event.data !== "string") {
      this.callbacks.onError?.(new Error("expected text frame from server"));
      return;
    }

    let parsed: FaceFrameMessage;
    try {
      parsed = JSON.parse(event.data) as FaceFrameMessage;
    } catch (err) {
      this.callbacks.onError?.(
        err instanceof Error ? err : new Error(String(err)),
      );
      return;
    }

    this.callbacks.onMessage(parsed);
  }

  private setStatus(status: FaceStreamStatus): void {
    this.status = status;
    this.callbacks.onStatusChange?.(status);
  }
}