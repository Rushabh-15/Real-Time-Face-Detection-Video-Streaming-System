import type { FaceFrameMessage } from "../types/messages";

interface ProcessedFeedProps {
  message: FaceFrameMessage | null;
  width?: number;
  height?: number;
}

/**
 * Display component for the server-annotated frame.
 *
 * Renders the base64-encoded JPEG inline via a data URI, plus a
 * monospace readout of the detected ROI. Three render states:
 *   - `message === null`: placeholder ("waiting for first frame")
 *   - `message.roi === null`: image + "no face detected"
 *   - both non-null: image + ROI coordinates + confidence
 *
 * Pure display: doesn't open the WS, doesn't fetch frames. Parent
 * supplies the message via prop.
 */
export function ProcessedFeed({
  message,
  width = 640,
  height = 480,
}: ProcessedFeedProps) {
  if (message === null) {
    return (
      <div
        style={{
          width,
          height,
          background: "#222",
          color: "#888",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: "system-ui",
        }}
      >
        Waiting for first frame…
      </div>
    );
  }

  return (
    <div>
      <img
        src={`data:image/jpeg;base64,${message.frame}`}
        alt="Annotated webcam frame"
        width={width}
        height={height}
        style={{ display: "block", background: "#000" }}
      />
      {message.roi === null ? (
        <p
          style={{
            color: "#888",
            margin: "0.5rem 0",
            fontFamily: "monospace",
          }}
        >
          No face detected
        </p>
      ) : (
        <p
          style={{
            margin: "0.5rem 0",
            fontFamily: "monospace",
            fontSize: "0.9rem",
          }}
        >
          {`x:${message.roi.x}  y:${message.roi.y}  w:${message.roi.w}  h:${message.roi.h}  confidence:${message.roi.confidence.toFixed(3)}`}
        </p>
      )}
    </div>
  );
}