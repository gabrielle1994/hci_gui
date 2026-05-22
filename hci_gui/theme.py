"""Design tokens and small rendering helpers shared by every element.

This module centralises the values that give ``hci_gui`` its modern,
macOS-inspired look: corner radii, system font lookup, hairline
strokes, and a soft drop-shadow utility. Keeping them in one place
means we can adjust the look of every widget without hunting through
``elements.py``.

"""

from __future__ import annotations

from functools import lru_cache
from typing import Tuple

import pygame


# ----- Corner radii (in pixels). Mirrors Apple's HIG-ish defaults. ---- #
RADIUS_SMALL  = 4    # checkbox, slider track
RADIUS_MEDIUM = 6    # buttons, text fields
RADIUS_LARGE  = 10   # cards / containers

# Stroke widths.
HAIRLINE_WIDTH = 1
FOCUS_RING_WIDTH = 3

# Padding / inset used inside several widgets.
TEXT_INSET = 10

# Subtle highlight added to the top edge of "filled" buttons.
TOP_HIGHLIGHT_ALPHA = 60

# Focus-ring color — macOS uses a translucent system-blue halo.
FOCUS_RING = (0, 122, 255, 90)


# ----- Font lookup ---------------------------------------------------- #
# We prefer SF Pro on Mac, fall back to other modern UI fonts elsewhere.
# Pygame's SysFont accepts a comma-separated string of candidates.
_FONT_STACK = (
    "sfprodisplay,sfprotext,sfpro,helveticaneue,segoeui,roboto,arial"
)


@lru_cache(maxsize=128)
def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    """Return a (cached) Pygame Font from the modern UI font stack."""
    pygame.font.init()
    font = pygame.font.SysFont(_FONT_STACK, int(size), bold=bold)
    return font


# ----- Soft drop shadow ---------------------------------------------- #

def draw_shadow(
    surface: pygame.Surface,
    rect: pygame.Rect,
    radius: int = RADIUS_MEDIUM,
    offset_y: int = 3,
    spread: int = 8,
    alpha: int = 55,
) -> None:
    """Paint a soft drop shadow underneath ``rect``.

    Implemented as a stack of expanding semi-transparent rounded
    rectangles. Outer layers are painted first with a low alpha,
    then progressively smaller, more opaque layers are blended on
    top. The result is a believable Gaussian-ish falloff that's
    darkest right next to the element and fades into the background.
    """
    spread = max(1, int(spread))
    pad = spread
    shadow_surf = pygame.Surface(
        (rect.width + pad * 2, rect.height + pad * 2),
        pygame.SRCALPHA,
    )
    # Iterate from outermost (i=spread) to innermost (i=1). Each layer's
    # per-draw alpha increases as we move inward; the SRCALPHA blend then
    # accumulates additional darkness near the element, while the outer
    # layers contribute only a thin halo.
    for i in range(spread, 0, -1):
        t = (spread - i + 1) / spread          # 0 < t <= 1, max at innermost
        layer_alpha = int(alpha * t * t)
        if layer_alpha <= 0:
            continue
        layer_rect = pygame.Rect(
            pad - i, pad - i,
            rect.width + i * 2, rect.height + i * 2,
        )
        pygame.draw.rect(
            shadow_surf,
            (0, 0, 0, layer_alpha),
            layer_rect,
            border_radius=radius + i,
        )
    surface.blit(shadow_surf, (rect.x - pad, rect.y - pad + offset_y))


# ----- Top highlight (subtle white sheen along the top of a button) -- #

def draw_top_highlight(
    surface: pygame.Surface,
    rect: pygame.Rect,
    radius: int,
    alpha: int = TOP_HIGHLIGHT_ALPHA,
) -> None:
    """Draw a faint white highlight along the top edge of a rounded rect.

    Used to give "filled" buttons (e.g. the primary blue Log-in button)
    a slight glossy lift without going full skeuomorphic. The highlight
    is painted as a stack of rounded rects with decreasing alpha so
    the falloff is smooth and never shows a horizontal seam.
    """
    if rect.width <= 0 or rect.height <= 0 or alpha <= 0:
        return
    highlight = pygame.Surface(rect.size, pygame.SRCALPHA)
    layers = max(3, rect.height // 4)
    for i in range(layers):
        t = 1.0 - i / layers
        layer_alpha = int(alpha * t * t)
        if layer_alpha <= 0:
            continue
        pygame.draw.rect(
            highlight,
            (255, 255, 255, layer_alpha),
            pygame.Rect(0, 0, rect.width, max(2, rect.height - i * 2)),
            border_radius=radius,
        )
    surface.blit(highlight, rect.topleft)


def draw_focus_ring(
    surface: pygame.Surface,
    rect: pygame.Rect,
    radius: int = RADIUS_MEDIUM,
    color: Tuple[int, int, int, int] = FOCUS_RING,
    inset: int = 0,
) -> None:
    """Draw a translucent focus ring around ``rect``."""
    pad = FOCUS_RING_WIDTH + 1
    ring_surf = pygame.Surface(
        (rect.width + pad * 2, rect.height + pad * 2),
        pygame.SRCALPHA,
    )
    ring_rect = pygame.Rect(
        pad - inset, pad - inset,
        rect.width + inset * 2, rect.height + inset * 2,
    )
    pygame.draw.rect(
        ring_surf, color, ring_rect,
        width=FOCUS_RING_WIDTH,
        border_radius=radius + inset,
    )
    surface.blit(ring_surf, (rect.x - pad, rect.y - pad))
