"""Elements — the building blocks you put on a Screen.

Every element is a coloured rectangle on the window with optional text
and event handlers. All elements inherit from `Element`. Concrete classes
shipped here: `Label`, `Button`, `TextBox`, `Checkbox`, `Slider`,
`Image`, `Container`.

The rendering style is intentionally close to macOS / Aqua: rounded
corners, soft drop shadows on cards, hairline borders, and a
translucent focus ring on text boxes.

Coordinates are in window pixels, with (0, 0) at the top-left.
"""

from __future__ import annotations

from typing import Callable, List, Optional

import pygame

from .colors import (
    ColorLike,
    HAIRLINE,
    LABEL_PRIMARY,
    LABEL_SECONDARY,
    LABEL_TERTIARY,
    SYSTEM_BLUE,
    SYSTEM_GRAY_3,
    SYSTEM_GRAY_5,
    _is_light,
    _shade,
    contrast_text_color,
    to_rgb,
)
from .events import ClickEvent, HoverEvent, KeyEvent
from .theme import (
    RADIUS_LARGE,
    RADIUS_MEDIUM,
    RADIUS_SMALL,
    TEXT_INSET,
    draw_focus_ring,
    draw_shadow,
    draw_top_highlight,
    get_font,
)


# Counter so elements created without an explicit `name=` still get a unique one.
_AUTO_ID = 0


def _next_name(prefix: str) -> str:
    global _AUTO_ID
    _AUTO_ID += 1
    return f"{prefix}_{_AUTO_ID}"


class Element:
    """Base class for every element.

    Args:
        x, y:           top-left position in window pixels
        x_size, y_size: width and height in pixels
        color:          fill color (named string or RGB tuple)
        name:           identifier used by the cognitive models; auto-generated if omitted
        visible:        if False, the element is not drawn and ignores events
    """

    def __init__(
        self,
        x: int,
        y: int,
        x_size: int,
        y_size: int,
        color: ColorLike = "lightgrey",
        name: Optional[str] = None,
        visible: bool = True,
    ) -> None:
        self.x = int(x)
        self.y = int(y)
        self.x_size = int(x_size)
        self.y_size = int(y_size)
        self.color: ColorLike = color
        self.name = name or _next_name(self.__class__.__name__.lower())
        self.visible = bool(visible)

        self.data = None
        self._hovered = False
        self._screen = None

    # ---- Geometry helpers ----------------------------------------------

    def loc(self) -> List[int]:
        """Return the element center as [x, y]."""
        return [round(self.x + self.x_size / 2), round(self.y + self.y_size / 2)]

    def max_size(self) -> int:
        return max(self.x_size, self.y_size)

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.x_size, self.y_size)

    def contains(self, x: int, y: int) -> bool:
        return self.x <= x < self.x + self.x_size and self.y <= y < self.y + self.y_size

    def hit_test(self, x: int, y: int) -> Optional["Element"]:
        """Return the deepest visible element at (x, y), or None.

        Default behavior: return self if (x, y) is inside this element.
        Container overrides this to recurse into its children so a click
        on a child element reaches the child rather than the container.
        """
        if not self.visible or not self.contains(x, y):
            return None
        return self

    def walk(self):
        """Yield self and every descendant element. Container overrides this."""
        yield self

    # ---- Rendering ----------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        """Override in subclasses. Default draws a filled rectangle."""
        if not self.visible:
            return
        pygame.draw.rect(surface, to_rgb(self.color), self.rect, border_radius=RADIUS_SMALL)

    # ---- Event hooks --------------------------------------------------

    def handle_click(self, event: ClickEvent) -> None:
        """Called by the Screen when this element is clicked. Override or set on_click."""

    def handle_hover(self, event: HoverEvent) -> None:
        """Called when the cursor enters or leaves this element."""

    def handle_key(self, event: KeyEvent) -> None:
        """Called for every key press while this element has focus."""


# ---------------------------------------------------------------------- #
# Concrete elements                                                      #
# ---------------------------------------------------------------------- #


class Label(Element):
    """Static text. Not interactive.

    Pass ``text_align="left"`` (or ``"right"``) together with an
    explicit ``x_size`` when you have a label whose text grows or
    shrinks after construction (e.g. a status line) — otherwise the
    auto-sized rect is too small for the new text and the default
    centred alignment pushes the text off the visible region.
    """

    def __init__(
        self,
        text: str,
        x: int,
        y: int,
        font_size: int = 18,
        color: ColorLike = "transparent",
        text_color: Optional[ColorLike] = LABEL_PRIMARY,
        name: Optional[str] = None,
        x_size: Optional[int] = None,
        y_size: Optional[int] = None,
        text_align: str = "center",
        bold: bool = False,
    ) -> None:
        if x_size is None or y_size is None:
            font = get_font(font_size, bold=bold)
            w, h = font.size(text or " ")
            x_size = x_size or w + 4
            y_size = y_size or h + 4
        super().__init__(x, y, x_size, y_size, color=color, name=name)
        self.text = text
        self.font_size = font_size
        self.text_color = text_color
        self.text_align = text_align
        self.bold = bold

    def _is_transparent(self) -> bool:
        return isinstance(self.color, str) and self.color.lower() == "transparent"

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        if not self._is_transparent():
            pygame.draw.rect(
                surface, to_rgb(self.color), self.rect,
                border_radius=RADIUS_SMALL,
            )

        font = get_font(self.font_size, bold=self.bold)
        if self.text_color is not None:
            text_color = to_rgb(self.text_color)
        elif self._is_transparent():
            text_color = LABEL_PRIMARY
        else:
            text_color = contrast_text_color(self.color)
        rendered = font.render(self.text, True, text_color)

        if self.text_align == "left":
            text_rect = rendered.get_rect(midleft=(self.x + 4, self.rect.centery))
        elif self.text_align == "right":
            text_rect = rendered.get_rect(midright=(self.x + self.x_size - 4, self.rect.centery))
        else:
            text_rect = rendered.get_rect(center=self.rect.center)
        surface.blit(rendered, text_rect)


class Button(Element):
    """Clickable button.

    Pass `on_click=fn` (a function taking a ClickEvent or no arguments) to
    react to clicks. Both signatures are supported, so you can start with
    `on_click=lambda: print("hi")`.

    The widget auto-picks between two macOS-style treatments:

    * **Filled** (vivid colors such as blue, red, green): solid fill,
      white text, a soft shadow, and a subtle highlight on top — like
      the default macOS push button.
    * **Tinted / secondary** (very light colors such as ``"lightblue"``,
      ``"lightgrey"``): light background with a hairline border and
      dark text — like a macOS secondary control.
    """

    def __init__(
        self,
        text: str,
        x: int,
        y: int,
        x_size: int = 120,
        y_size: int = 32,
        color: ColorLike = "blue",
        text_color: Optional[ColorLike] = None,
        font_size: int = 16,
        on_click: Optional[Callable] = None,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(x, y, x_size, y_size, color=color, name=name)
        self.text = text
        self.font_size = font_size
        self.text_color = text_color
        self.on_click = on_click
        self._pressed = False

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        base = to_rgb(self.color)
        light_button = _is_light(base)

        # Hover / pressed shading. Filled buttons darken on press, tinted
        # buttons darken on hover (macOS conventions).
        if self._pressed:
            fill = _shade(base, -0.10 if not light_button else -0.06)
        elif self._hovered:
            fill = _shade(base, -0.05 if not light_button else -0.04)
        else:
            fill = base

        # Soft drop shadow for filled buttons.
        if not light_button:
            draw_shadow(surface, self.rect, radius=RADIUS_MEDIUM,
                        offset_y=2, spread=6, alpha=45)

        pygame.draw.rect(surface, fill, self.rect, border_radius=RADIUS_MEDIUM)

        if not light_button:
            draw_top_highlight(surface, self.rect, RADIUS_MEDIUM, alpha=55)
        else:
            # Hairline border helps light buttons sit on a white card.
            pygame.draw.rect(
                surface, HAIRLINE, self.rect,
                width=1, border_radius=RADIUS_MEDIUM,
            )

        font = get_font(self.font_size, bold=not light_button)
        tc = to_rgb(self.text_color) if self.text_color else contrast_text_color(base)
        rendered = font.render(self.text, True, tc)
        surface.blit(rendered, rendered.get_rect(center=self.rect.center))

    def handle_click(self, event: ClickEvent) -> None:
        if self.on_click is None:
            return
        try:
            self.on_click(event)
        except TypeError:
            self.on_click()


class TextBox(Element):
    """Single-line text input. Click to focus, then type.

    Styling mimics macOS: a white field with a hairline border, a soft
    inner shadow at the top, and a translucent blue focus ring when the
    field is active.
    """

    def __init__(
        self,
        x: int,
        y: int,
        x_size: int = 200,
        y_size: int = 32,
        placeholder: str = "",
        text: str = "",
        color: ColorLike = "white",
        font_size: int = 16,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(x, y, x_size, y_size, color=color, name=name)
        self.placeholder = placeholder
        self.text = text
        self.font_size = font_size
        self.focused = False

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return

        # Translucent blue focus ring (drawn behind the field).
        if self.focused:
            draw_focus_ring(surface, self.rect, radius=RADIUS_MEDIUM, inset=1)

        pygame.draw.rect(
            surface, to_rgb(self.color), self.rect, border_radius=RADIUS_MEDIUM,
        )

        # Hairline border (darker when focused for a stronger affordance).
        border = SYSTEM_BLUE if self.focused else HAIRLINE
        pygame.draw.rect(
            surface, border, self.rect,
            width=1, border_radius=RADIUS_MEDIUM,
        )

        # Subtle inner shadow at the top of the field.
        inner_shadow = pygame.Surface(
            (self.x_size - 2, 4), pygame.SRCALPHA,
        )
        pygame.draw.rect(
            inner_shadow, (0, 0, 0, 18),
            inner_shadow.get_rect(),
            border_top_left_radius=RADIUS_MEDIUM,
            border_top_right_radius=RADIUS_MEDIUM,
        )
        surface.blit(inner_shadow, (self.x + 1, self.y + 1))

        font = get_font(self.font_size)
        if self.text:
            rendered = font.render(self.text, True, LABEL_PRIMARY)
        else:
            rendered = font.render(self.placeholder, True, LABEL_TERTIARY)
        surface.blit(
            rendered,
            rendered.get_rect(midleft=(self.x + TEXT_INSET, self.rect.centery)),
        )

        # Blinking-ish caret (always on while focused — keeps things simple).
        if self.focused:
            caret_x = self.x + TEXT_INSET + font.size(self.text)[0] + 1
            pygame.draw.line(
                surface, SYSTEM_BLUE,
                (caret_x, self.y + 6),
                (caret_x, self.y + self.y_size - 6),
                1,
            )

    def handle_click(self, event: ClickEvent) -> None:
        self.focused = True

    def handle_key(self, event: KeyEvent) -> None:
        if not (self.focused and event.pressed):
            return
        if event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
        elif event.key in (pygame.K_RETURN, pygame.K_TAB, pygame.K_ESCAPE):
            self.focused = False
        elif event.char and event.char.isprintable():
            self.text += event.char


class Checkbox(Element):
    """A small checkable box with a label to its right.

    Styled as a rounded square that fills with system-blue when checked
    and shows a clean white check-glyph on top.
    """

    def __init__(
        self,
        label: str,
        x: int,
        y: int,
        size: int = 18,
        checked: bool = False,
        color: ColorLike = "white",
        on_change: Optional[Callable] = None,
        name: Optional[str] = None,
        font_size: int = 16,
    ) -> None:
        font = get_font(font_size)
        label_w, label_h = font.size(label)
        super().__init__(x, y, size + 10 + label_w, max(size, label_h), color=color, name=name)
        self.label = label
        self.box_size = size
        self.checked = checked
        self.on_change = on_change
        self.font_size = font_size

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        box_rect = pygame.Rect(
            self.x, self.y + (self.y_size - self.box_size) // 2,
            self.box_size, self.box_size,
        )

        if self.checked:
            pygame.draw.rect(surface, SYSTEM_BLUE, box_rect, border_radius=RADIUS_SMALL)
            # White check-mark
            pad = max(3, self.box_size // 5)
            pygame.draw.line(
                surface, (255, 255, 255),
                (box_rect.left + pad, box_rect.centery),
                (box_rect.centerx - 1, box_rect.bottom - pad), 2,
            )
            pygame.draw.line(
                surface, (255, 255, 255),
                (box_rect.centerx - 1, box_rect.bottom - pad),
                (box_rect.right - pad + 1, box_rect.top + pad), 2,
            )
        else:
            pygame.draw.rect(surface, to_rgb(self.color), box_rect, border_radius=RADIUS_SMALL)
            pygame.draw.rect(surface, SYSTEM_GRAY_3, box_rect, width=1, border_radius=RADIUS_SMALL)

        font = get_font(self.font_size)
        rendered = font.render(self.label, True, LABEL_PRIMARY)
        surface.blit(
            rendered,
            rendered.get_rect(midleft=(self.x + self.box_size + 10, self.rect.centery)),
        )

    def handle_click(self, event: ClickEvent) -> None:
        self.checked = not self.checked
        if self.on_change is not None:
            try:
                self.on_change(self.checked)
            except TypeError:
                self.on_change()


class Slider(Element):
    """Horizontal slider that returns a float in [min_value, max_value].

    Styled like the macOS continuous slider: a thin neutral track, a
    blue filled portion up to the current value, and a white circular
    knob with a soft shadow.
    """

    def __init__(
        self,
        x: int,
        y: int,
        x_size: int = 200,
        y_size: int = 24,
        min_value: float = 0.0,
        max_value: float = 1.0,
        value: Optional[float] = None,
        color: ColorLike = "lightgrey",
        on_change: Optional[Callable] = None,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(x, y, x_size, y_size, color=color, name=name)
        self.min_value = float(min_value)
        self.max_value = float(max_value)
        self.value = float(value) if value is not None else self.min_value
        self.on_change = on_change
        self._dragging = False

    def _value_to_x(self) -> int:
        t = (self.value - self.min_value) / max(self.max_value - self.min_value, 1e-9)
        return int(self.x + t * self.x_size)

    def _x_to_value(self, mx: int) -> float:
        t = (mx - self.x) / max(self.x_size, 1)
        t = max(0.0, min(1.0, t))
        return self.min_value + t * (self.max_value - self.min_value)

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        track = pygame.Rect(self.x, self.rect.centery - 2, self.x_size, 4)
        pygame.draw.rect(surface, SYSTEM_GRAY_5, track, border_radius=2)

        # Filled portion up to the current value.
        knob_x = self._value_to_x()
        filled = pygame.Rect(self.x, track.y, max(0, knob_x - self.x), track.height)
        pygame.draw.rect(surface, SYSTEM_BLUE, filled, border_radius=2)

        # Knob: soft shadow + white disc + thin border.
        knob_r = max(8, self.y_size // 2)
        knob_rect = pygame.Rect(
            knob_x - knob_r, self.rect.centery - knob_r,
            knob_r * 2, knob_r * 2,
        )
        draw_shadow(surface, knob_rect, radius=knob_r, offset_y=1, spread=5, alpha=70)
        pygame.draw.circle(surface, (255, 255, 255), (knob_x, self.rect.centery), knob_r)
        pygame.draw.circle(
            surface, SYSTEM_GRAY_3, (knob_x, self.rect.centery), knob_r, 1,
        )

    def handle_click(self, event: ClickEvent) -> None:
        self.value = self._x_to_value(event.x)
        if self.on_change is not None:
            try:
                self.on_change(self.value)
            except TypeError:
                self.on_change()


class Image(Element):
    """Display an image file (PNG / JPEG)."""

    def __init__(
        self,
        path: str,
        x: int,
        y: int,
        x_size: Optional[int] = None,
        y_size: Optional[int] = None,
        name: Optional[str] = None,
    ) -> None:
        pygame.display.init()
        surf = pygame.image.load(path)
        if x_size and y_size:
            surf = pygame.transform.smoothscale(surf, (x_size, y_size))
        super().__init__(x, y, surf.get_width(), surf.get_height(),
                         color="transparent", name=name)
        self._surface = surf
        self.path = path

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        surface.blit(self._surface, (self.x, self.y))


class Container(Element):
    """A grouping element that draws a background and contains child elements.

    Containers now look like macOS cards: rounded corners, an optional
    soft drop shadow, and a hairline border by default. Pass
    ``shadow=False`` to opt out (useful for inner panels). Pass
    ``border_color`` and ``border_width`` to override the default
    hairline.
    """

    def __init__(
        self,
        x: int,
        y: int,
        x_size: int,
        y_size: int,
        color: ColorLike = "white",
        name: Optional[str] = None,
        children: Optional[List[Element]] = None,
        border_color: Optional[ColorLike] = None,
        border_width: int = 0,
        shadow: bool = True,
        radius: int = RADIUS_LARGE,
    ) -> None:
        super().__init__(x, y, x_size, y_size, color=color, name=name)
        self.children: List[Element] = list(children) if children else []
        self.border_color = border_color
        self.border_width = int(border_width)
        self.shadow = bool(shadow)
        self.radius = int(radius)

    def add(self, element: Element) -> Element:
        self.children.append(element)
        return element

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return

        # Only cast a shadow if the card sits on a non-white surface.
        # We can't easily query that here, so we just honor the flag.
        if self.shadow:
            draw_shadow(
                surface, self.rect,
                radius=self.radius, offset_y=4, spread=14, alpha=42,
            )

        pygame.draw.rect(
            surface, to_rgb(self.color), self.rect, border_radius=self.radius,
        )

        if self.border_color is not None and self.border_width > 0:
            pygame.draw.rect(
                surface, to_rgb(self.border_color), self.rect,
                width=self.border_width, border_radius=self.radius,
            )
        elif not self.shadow:
            # Inner panels: a soft hairline keeps them from disappearing.
            pygame.draw.rect(
                surface, HAIRLINE, self.rect,
                width=1, border_radius=self.radius,
            )

        for child in self.children:
            child.draw(surface)

    def hit_test(self, x: int, y: int) -> Optional[Element]:
        if not self.visible or not self.contains(x, y):
            return None
        for child in reversed(self.children):
            target = child.hit_test(x, y)
            if target is not None:
                return target
        return self

    def walk(self):
        yield self
        for child in self.children:
            yield from child.walk()
