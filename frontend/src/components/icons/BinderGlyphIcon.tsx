import { SvgIcon, type SvgIconProps } from "@mui/material";

/**
 * A binder page divided into card slots — stands in for "Collection"
 * (how players actually store owned cards), instead of MUI's generic
 * Collections icon (stacked photo squares, a stock-photo-app glyph).
 */
export const BinderGlyphIcon = (props: SvgIconProps) => (
  <SvgIcon {...props} viewBox="0 0 24 24">
    <rect x="3" y="2.5" width="18" height="19" rx="1.6" fill="none" stroke="currentColor" strokeWidth="1.4" />
    <line x1="12" y1="2.5" x2="12" y2="21.5" stroke="currentColor" strokeWidth="1" opacity="0.6" />
    <line x1="3" y1="12" x2="21" y2="12" stroke="currentColor" strokeWidth="1" opacity="0.6" />
    <circle cx="3" cy="7" r="0.9" fill="currentColor" />
    <circle cx="3" cy="17" r="0.9" fill="currentColor" />
  </SvgIcon>
);
