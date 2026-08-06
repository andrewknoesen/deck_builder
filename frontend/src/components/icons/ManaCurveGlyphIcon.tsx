import { SvgIcon, type SvgIconProps } from "@mui/material";

/**
 * A five-bar curve, ascending then descending — stands in for the "Numbers
 * while you build" feature (mana curve + draw odds), instead of a generic
 * icon. Deliberately not another line-art outline like CardGlyphIcon: this
 * one is meant to read as a small chart, tying the glyph to the actual
 * DeckStats feature rather than being interchangeable with it.
 */
export const ManaCurveGlyphIcon = (props: SvgIconProps) => (
  <SvgIcon {...props} viewBox="0 0 24 24">
    <rect x="2.5" y="14" width="3" height="6" rx="0.6" fill="currentColor" opacity="0.55" />
    <rect x="7" y="10" width="3" height="10" rx="0.6" fill="currentColor" opacity="0.75" />
    <rect x="11.5" y="4" width="3" height="16" rx="0.6" fill="currentColor" />
    <rect x="16" y="10" width="3" height="10" rx="0.6" fill="currentColor" opacity="0.75" />
    <rect x="20.5" y="14" width="1.5" height="6" rx="0.6" fill="currentColor" opacity="0.55" />
  </SvgIcon>
);
