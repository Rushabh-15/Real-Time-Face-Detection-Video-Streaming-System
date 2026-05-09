/**
 * Wire-format types for the face-stream WebSocket protocol.
 *
 * These mirror `backend/app/schemas/ws.py`. Kept in sync by hand —
 * the schema is small and stable enough that automated codegen would
 * cost more than it saves.
 */

/**
 * Region of interest: an axis-aligned face bounding box in pixel coordinates.
 */
export interface ROI {
  /** Top-left x in pixels (≥ 0). */
  x: number;
  /** Top-left y in pixels (≥ 0). */
  y: number;
  /** Width in pixels (> 0). */
  w: number;
  /** Height in pixels (> 0). */
  h: number;
  /** Detection confidence in [0, 1]. */
  confidence: number;
}

/**
 * Server → client message: an annotated frame and its detected ROI.
 *
 * `frame` is a base64-encoded JPEG (no data URI prefix); display via
 * `new Image()` or by setting `<img src={`data:image/jpeg;base64,${frame}`} />`.
 *
 * `roi` is null when no face was detected — clients should display the
 * frame as-is (which is itself the un-annotated original re-encoded).
 */
export interface FaceFrameMessage {
  frame: string;
  roi: ROI | null;
}