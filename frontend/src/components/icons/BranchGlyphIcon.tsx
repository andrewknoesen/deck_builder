import { SvgIcon, type SvgIconProps } from "@mui/material";

/**
 * A root node branching into two, each branching again — a literal small
 * decision tree. Stands in for "Practice Mode" (the goldfish session is a
 * branching tree you can rewind), instead of MUI's generic SportsEsports
 * icon (a gamepad, which has nothing to do with what this feature actually
 * looks like on screen — see GoldfishTree.tsx).
 */
export const BranchGlyphIcon = (props: SvgIconProps) => (
  <SvgIcon {...props} viewBox="0 0 24 24">
    <line x1="12" y1="5.5" x2="7" y2="11.5" stroke="currentColor" strokeWidth="1.3" />
    <line x1="12" y1="5.5" x2="17" y2="11.5" stroke="currentColor" strokeWidth="1.3" />
    <line x1="7" y1="12.5" x2="4.5" y2="18.5" stroke="currentColor" strokeWidth="1.1" opacity="0.7" />
    <line x1="7" y1="12.5" x2="9.5" y2="18.5" stroke="currentColor" strokeWidth="1.1" opacity="0.7" />
    <line x1="17" y1="12.5" x2="14.5" y2="18.5" stroke="currentColor" strokeWidth="1.1" opacity="0.7" />
    <line x1="17" y1="12.5" x2="19.5" y2="18.5" stroke="currentColor" strokeWidth="1.1" opacity="0.7" />
    <circle cx="12" cy="4.5" r="1.6" fill="currentColor" />
    <circle cx="7" cy="12" r="1.4" fill="currentColor" opacity="0.85" />
    <circle cx="17" cy="12" r="1.4" fill="currentColor" opacity="0.85" />
    <circle cx="4.5" cy="19.5" r="1.1" fill="currentColor" opacity="0.6" />
    <circle cx="9.5" cy="19.5" r="1.1" fill="currentColor" opacity="0.6" />
    <circle cx="14.5" cy="19.5" r="1.1" fill="currentColor" opacity="0.6" />
    <circle cx="19.5" cy="19.5" r="1.1" fill="currentColor" opacity="0.6" />
  </SvgIcon>
);
