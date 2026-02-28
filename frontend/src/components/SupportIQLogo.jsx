import { cn } from "@/lib/utils";

/**
 * SupportIQ brand logo — black/white themed icon + wordmark.
 * Renders an inline SVG so it always matches the theme.
 */
export function SupportIQIcon({ className }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 32 32"
      fill="none"
      className={cn("h-5 w-5", className)}
    >
      {/* Rounded square background */}
      <rect width="32" height="32" rx="8" className="fill-foreground" />
      {/* Chat bubble outline */}
      <path
        d="M8 10a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-4l-3 3-3-3h-2a2 2 0 0 1-2-2V10z"
        className="fill-background"
      />
      {/* IQ text inside bubble */}
      <text
        x="16"
        y="18"
        textAnchor="middle"
        className="fill-foreground"
        style={{ fontSize: "8px", fontWeight: 800, fontFamily: "system-ui, sans-serif" }}
      >
        IQ
      </text>
    </svg>
  );
}

export function SupportIQWordmark({ className, iconClassName }) {
  return (
    <span className={cn("flex items-center gap-2 font-bold tracking-tight", className)}>
      <SupportIQIcon className={iconClassName} />
      <span>
        Support<span className="text-muted-foreground font-semibold">IQ</span>
      </span>
    </span>
  );
}
