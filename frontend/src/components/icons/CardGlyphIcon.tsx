import { SvgIcon, type SvgIconProps } from "@mui/material";

/**
 * A minimal card-silhouette glyph: a portrait card frame, a corner mana pip,
 * and the type-line divider. Stands in for the generic "AutoAwesome" sparkle
 * icon (the AI-slop "magic" cliche named in docs/UI_DEGENERIC_DESIGN.md item 2)
 * with something legible as specifically-Magic without tracing an actual
 * mana symbol or WotC card frame art. Line-art only (currentColor), so it
 * follows text/icon color the same way MUI's built-in icons do.
 */
export const CardGlyphIcon = (props: SvgIconProps) => (
  <SvgIcon {...props} viewBox="0 0 24 24">
    <rect
      x="4.5"
      y="2.5"
      width="15"
      height="19"
      rx="2"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
    />
    <circle cx="16.5" cy="6" r="1.6" fill="none" stroke="currentColor" strokeWidth="1.5" />
    <line x1="6.5" y1="9.5" x2="17.5" y2="9.5" stroke="currentColor" strokeWidth="1.2" />
    <line x1="6.5" y1="18" x2="12" y2="18" stroke="currentColor" strokeWidth="1.2" opacity="0.6" />
  </SvgIcon>
);
