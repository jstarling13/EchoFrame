/**
 * Recreated in code from the logo image the owner supplied directly in
 * chat (a navy open-frame mark with three "echo" lines, one accented in
 * gold, next to an "EchoFrame" serif wordmark) — there was no source
 * file on disk to copy. Swap this for the real exported asset whenever
 * one is available; sizing/colors can be adjusted to match exactly.
 */
export default function LogoMark({
  className,
  height = 40,
  variant = "navy",
}: {
  className?: string;
  height?: number;
  variant?: "navy" | "white";
}) {
  const lineColor = variant === "white" ? "#ffffff" : "var(--brand-navy, #14284f)";
  const goldColor = variant === "white" ? "#e0b94a" : "var(--brand-gold, #b8902f)";

  return (
    <svg
      className={className}
      height={height}
      viewBox="0 0 34 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path
        d="M31 2H8C4.68629 2 2 4.68629 2 8V32C2 35.3137 4.68629 38 8 38H31"
        stroke={lineColor}
        strokeWidth="3"
      />
      <line x1="12" y1="15" x2="24" y2="15" stroke={lineColor} strokeWidth="3" />
      <line x1="12" y1="20.5" x2="17" y2="20.5" stroke={goldColor} strokeWidth="3" />
      <line x1="18.5" y1="20.5" x2="30" y2="20.5" stroke={lineColor} strokeWidth="3" />
      <line x1="12" y1="26" x2="27" y2="26" stroke={lineColor} strokeWidth="3" />
    </svg>
  );
}
