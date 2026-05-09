import { ProcessedFeed } from "./components/ProcessedFeed";
import { WebcamCapture } from "./components/WebcamCapture";
import { useFaceStream } from "./hooks/useFaceStream";
import type { FaceStreamStatus } from "./lib/ws";

const WS_URL = import.meta.env.VITE_BACKEND_WS_URL;

export default function App() {
  const { status, latestMessage, error, send } = useFaceStream(WS_URL);

  return (
    <main
      style={{
        fontFamily: "system-ui",
        padding: "2rem",
        maxWidth: 1400,
        margin: "0 auto",
      }}
    >
      <header style={{ marginBottom: "1.5rem" }}>
        <h1 style={{ margin: 0 }}>face-detect-stream</h1>
        <p style={{ margin: "0.25rem 0", color: "#666" }}>
          Connection: <StatusBadge status={status} />
          {error && (
            <span style={{ color: "#c00", marginLeft: "1rem" }}>
              {error.message}
            </span>
          )}
        </p>
      </header>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "1.5rem",
          alignItems: "start",
        }}
      >
        <section>
          <h2 style={{ fontSize: "1rem", color: "#666", marginTop: 0 }}>
            Webcam input
          </h2>
          <WebcamCapture onFrame={send} />
        </section>
        <section>
          <h2 style={{ fontSize: "1rem", color: "#666", marginTop: 0 }}>
            Server output
          </h2>
          <ProcessedFeed message={latestMessage} />
        </section>
      </div>
    </main>
  );
}

function StatusBadge({ status }: { status: FaceStreamStatus }) {
  const color =
    status === "open"
      ? "#0a0"
      : status === "connecting"
        ? "#a80"
        : status === "closed" || status === "closing"
          ? "#c00"
          : "#666";
  return (
    <span style={{ color, fontWeight: 600, textTransform: "uppercase" }}>
      {status}
    </span>
  );
}