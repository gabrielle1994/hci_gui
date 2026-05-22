"""Named colors and small palette helpers.

The named palette is inspired by Apple's macOS system colors (Human
Interface Guidelines) so the resulting UI looks closer to a modern
desktop app than to a 1995 Tk dialog. A color can still be passed to
any element as either:

  * a name  ("red", "blue", "system_gray_5", "label_secondary", ...)
  * a hex   ("#ff8800")
  * a tuple ((255, 136, 0))  --- optional 4th component is alpha.

Unknown names fall back to grey instead of crashing.
"""

from typing import Tuple, Union

Color = Tuple[int, int, int]
ColorLike = Union[str, Color, Tuple[int, int, int, int]]


# ----- macOS-inspired system palette ---------------------------------- #
# Values match the published macOS system color definitions (light mode).

SYSTEM_BLUE    = (0,   122, 255)
SYSTEM_GREEN   = (52,  199, 89)
SYSTEM_INDIGO  = (88,  86,  214)
SYSTEM_ORANGE  = (255, 149, 0)
SYSTEM_PINK    = (255, 45,  85)
SYSTEM_PURPLE  = (175, 82,  222)
SYSTEM_RED     = (255, 59,  48)
SYSTEM_TEAL    = (90,  200, 250)
SYSTEM_YELLOW  = (255, 204, 0)
SYSTEM_BROWN   = (162, 132, 94)
SYSTEM_MINT    = (0,   199, 190)
SYSTEM_CYAN    = (50,  173, 230)

# Apple-style monochrome scale (low number = darker, high = lighter).
SYSTEM_GRAY    = (142, 142, 147)
SYSTEM_GRAY_2  = (174, 174, 178)
SYSTEM_GRAY_3  = (199, 199, 204)
SYSTEM_GRAY_4  = (209, 209, 214)
SYSTEM_GRAY_5  = (229, 229, 234)
SYSTEM_GRAY_6  = (242, 242, 247)

# Common UI surfaces.
WINDOW_BG      = (236, 236, 236)
CARD_BG        = (255, 255, 255)
GROUPED_BG     = (242, 242, 247)
HAIRLINE       = (216, 216, 220)

# Label / text colors. Same look as Apple's `labelColor` hierarchy.
LABEL_PRIMARY   = (28,  28,  30)
LABEL_SECONDARY = (60,  60,  67)
LABEL_TERTIARY  = (110, 110, 115)
LABEL_QUATERNARY = (160, 160, 164)


NAMED_COLORS: "dict[str, Color]" = {
    # Neutrals -- map onto Apple's gray scale so things look balanced.
    "white":          CARD_BG,
    "black":          LABEL_PRIMARY,
    "grey":           SYSTEM_GRAY,
    "gray":           SYSTEM_GRAY,
    "lightgrey":      SYSTEM_GRAY_5,
    "lightgray":      SYSTEM_GRAY_5,
    "darkgrey":       LABEL_SECONDARY,
    "darkgray":       LABEL_SECONDARY,

    # Vibrant accent colors, refreshed to macOS system values.
    "red":            SYSTEM_RED,
    "green":          SYSTEM_GREEN,
    "blue":           SYSTEM_BLUE,
    "yellow":         SYSTEM_YELLOW,
    "orange":         SYSTEM_ORANGE,
    "purple":         SYSTEM_PURPLE,
    "pink":           SYSTEM_PINK,
    "brown":          SYSTEM_BROWN,
    "cyan":           SYSTEM_CYAN,
    "magenta":        SYSTEM_PINK,
    "teal":           SYSTEM_TEAL,
    "indigo":         SYSTEM_INDIGO,
    "mint":           SYSTEM_MINT,

    # Soft "tinted" variants used by secondary buttons.
    "lightblue":      (220, 232, 255),
    "lightred":       (255, 220, 220),
    "lightgreen":     (215, 240, 220),
    "lightyellow":    (255, 240, 200),
    "lightorange":    (255, 230, 200),
    "lightpurple":    (235, 220, 245),

    # Backgrounds & system semantics (exposed by name too).
    "window_bg":      WINDOW_BG,
    "card_bg":        CARD_BG,
    "grouped_bg":     GROUPED_BG,
    "hairline":       HAIRLINE,
    "system_gray":    SYSTEM_GRAY,
    "system_gray_2":  SYSTEM_GRAY_2,
    "system_gray_3":  SYSTEM_GRAY_3,
    "system_gray_4":  SYSTEM_GRAY_4,
    "system_gray_5":  SYSTEM_GRAY_5,
    "system_gray_6":  SYSTEM_GRAY_6,
    "label_primary":   LABEL_PRIMARY,
    "label_secondary": LABEL_SECONDARY,
    "label_tertiary":  LABEL_TERTIARY,
    "label_quaternary": LABEL_QUATERNARY,

    "transparent":    (0, 0, 0),  # sentinel; elements check the name
}


def to_rgb(color: ColorLike) -> Color:
    """Resolve a color name or RGB(A) tuple to an (r, g, b) tuple.

    Unknown names fall back to grey so a typo never crashes a student's app.
    """
    if isinstance(color, tuple):
        if len(color) in (3, 4):
            return (int(color[0]), int(color[1]), int(color[2]))
        raise ValueError(f"Color tuple must have 3 or 4 components, got {color!r}")
    if isinstance(color, str):
        key = color.strip().lower()
        if key in NAMED_COLORS:
            return NAMED_COLORS[key]
        if key.startswith("#") and len(key) == 7:
            return (int(key[1:3], 16), int(key[3:5], 16), int(key[5:7], 16))
    return NAMED_COLORS["grey"]


def contrast_text_color(bg: ColorLike) -> Color:
    """Return black or white, whichever has more contrast with `bg`.

    Useful for drawing label text on top of a button without the
    student having to think about it.
    """
    r, g, b = to_rgb(bg)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
    return LABEL_PRIMARY if luminance > 0.6 else (255, 255, 255)


# ----- Internal helpers used by elements ------------------------------ #

def _shade(rgb: Color, amount: float) -> Color:
    """Lighten (amount > 0) or darken (amount < 0) a color.

    ``amount`` is in [-1, 1]; ``0.1`` is a subtle change.
    """
    amount = max(-1.0, min(1.0, amount))
    if amount >= 0:
        return (
            int(rgb[0] + (255 - rgb[0]) * amount),
            int(rgb[1] + (255 - rgb[1]) * amount),
            int(rgb[2] + (255 - rgb[2]) * amount),
        )
    factor = 1 + amount
    return (int(rgb[0] * factor), int(rgb[1] * factor), int(rgb[2] * factor))


def _is_light(rgb: Color) -> bool:
    """True if a color is closer to white than to black."""
    luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255.0
    return luminance > 0.7
