import { SvgIcon, type SvgIconProps } from "@mui/material";

/**
 * Three offset, overlapping card outlines — stands in for "Your Decks"
 * (a deck being literally a stack of cards), instead of MUI's generic
 * Style icon (a paint-swatch glyph with no MTG meaning).
 */
export const CardStackGlyphIcon = (props: SvgIconProps) => (
  <SvgIcon {...props} viewBox="0 0 24 24">
    <rect x="8" y="2" width="11" height="14" rx="1.3" fill="none" stroke="currentColor" strokeWidth="1.3" opacity="0.45" />
    <rect x="5" y="5" width="11" height="14" rx="1.3" fill="none" stroke="currentColor" strokeWidth="1.3" opacity="0.7" />
    <rect x="2" y="8" width="11" height="14" rx="1.3" fill="none" stroke="currentColor" strokeWidth="1.4" />
  </SvgIcon>
);
