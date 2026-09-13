import { ImageResponse } from "next/og";

export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#fefefe",
        }}
      >
        <div
          style={{
            fontSize: 96,
            fontWeight: 700,
            display: "flex",
          }}
        >
          <span style={{ color: "#14284f" }}>Echo</span>
          <span style={{ color: "#7297c5" }}>Frame</span>
        </div>
        <div style={{ fontSize: 32, color: "#55585e", marginTop: 24 }}>
          AI Implementation &amp; Workflow Automation
        </div>
      </div>
    ),
    { ...size }
  );
}
