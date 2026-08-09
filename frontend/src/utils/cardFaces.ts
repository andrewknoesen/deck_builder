import type { ScryfallCard, ScryfallCardFace } from "../types/mtg";

/**
 * Returns the two faces worth flipping between, or undefined if there's
 * nothing meaningfully different to show (no card_faces, or a reversible/
 * art-series print where both faces share the same name).
 */
export function getFlippableFaces(
    card: ScryfallCard | null | undefined
): [ScryfallCardFace, ScryfallCardFace] | undefined {
    const faces = card?.card_faces;
    if (!faces || faces.length < 2) return undefined;
    if (faces[0].name === faces[1].name) return undefined;
    return [faces[0], faces[1]];
}
