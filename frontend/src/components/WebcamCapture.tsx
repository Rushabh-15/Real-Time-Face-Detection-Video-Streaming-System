import { useEffect, useRef, useState } from "react";

interface WebcamCaptureProps {
  /** Called once per captured frame with a JPEG-encoded Blob. */
  onFrame: (frame: Blob) => void;
  /** Capture rate. Default 10 fps — enough to feel live, light on CPU. */
  fps?: number;
  /** Requested capture dimensions. Default 640x480. */
  width?: number;
  height?: number;
}

/**
 * Webcam capture component.
 *
 * Acquires the user's camera via getUserMedia, displays it in a <video>
 * element, and at the configured fps draws each frame to a hidden
 * <canvas>, JPEG-encodes it, and emits via `onFrame`.
 *
 * Knows nothing about WebSocket or face detection — pure media capture.
 */
export function WebcamCapture({
  onFrame,
  fps = 10,
  width = 640,
  height = 480,
}: WebcamCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [streaming, setStreaming] = useState(false);

  // Effect 1: acquire camera, attach to video element, stop on unmount.
  useEffect(() => {
    let stream: MediaStream | null = null;
    let cancelled = false;

    async function start() {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { width, height },
          audio: false,
        });
        // Component unmounted while awaiting permission — release the
        // camera we just opened.
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          setStreaming(true);
        }
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "camera unavailable";
        setError(message);
      }
    }

    start();

    return () => {
      cancelled = true;
      stream?.getTracks().forEach((t) => t.stop());
      setStreaming(false);
    };
  }, [width, height]);

  // Effect 2: at fps Hz, draw current video frame to canvas → JPEG → onFrame.
  useEffect(() => {
    if (!streaming) return;

    const interval = setInterval(() => {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      if (!video || !canvas) return;
      // Skip frames before the video has decoded data to draw.
      if (video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) return;

      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      canvas.toBlob(
        (blob) => {
          if (blob) onFrame(blob);
        },
        "image/jpeg",
        0.85,
      );
    }, 1000 / fps);

    return () => clearInterval(interval);
  }, [streaming, fps, onFrame]);

  if (error) {
    return (
      <div role="alert" style={{ color: "#c00" }}>
        Webcam unavailable: {error}
      </div>
    );
  }

  return (
    <div>
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        width={width}
        height={height}
        style={{ display: "block", background: "#000" }}
      />
      {/* Hidden capture surface — never displayed, just used for toBlob. */}
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        style={{ display: "none" }}
      />
    </div>
  );
}