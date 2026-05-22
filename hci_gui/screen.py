"""A `Screen` is a single page of the UI.

A Screen owns a list of elements, draws them, and dispatches mouse and
keyboard events to them. An `App` holds many screens and switches
between them with `app.go_to(name)`.
"""

from __future__ import annotations

from typing import Callable, Iterable, List, Optional

import pygame

from .colors import ColorLike, to_rgb
from .elements import Element
from .events import ClickEvent, HoverEvent, KeyEvent


class Screen:
    """A named container of elements with its own background.

    Args:
        name:        unique identifier; used by App.go_to(name)
        background:  fill color drawn before any elements
        on_show:     optional callback fired every time this screen becomes active
    """

    def __init__(
        self,
        name: str,
        background: ColorLike = "window_bg",
        on_show: Optional[Callable[["Screen"], None]] = None,
    ) -> None:
        self.name = name
        self.background = background
        self.on_show = on_show
        self.elements: List[Element] = []
        self._focused: Optional[Element] = None
        self._app = None

    # ---- Element management ---------------------------------------------

    def add(self, element: Element) -> Element:
        """Attach an element. Returns it so you can chain `btn = screen.add(Button(...))`."""
        element._screen = self
        self.elements.append(element)
        return element

    def remove(self, element: Element) -> None:
        if element in self.elements:
            self.elements.remove(element)

    def get(self, name: str) -> Optional[Element]:
        """Find an element by its `name` attribute (or None).

        Searches recursively into Containers as well, so an element added
        inside a container is still findable.
        """
        for e in self._all_elements():
            if e.name == name:
                return e
        return None

    def __iter__(self) -> Iterable[Element]:
        return iter(self.elements)

    def _all_elements(self) -> Iterable[Element]:
        """Yield every element on this screen, recursing into containers."""
        for e in self.elements:
            yield from e.walk()

    # ---- Drawing ---------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(to_rgb(self.background))
        for e in self.elements:
            e.draw(surface)

    # ---- Event dispatching ----------------------------------------------

    def dispatch_click(self, x: int, y: int, button: int = 1) -> Optional[Element]:
        """Forward a click to the topmost visible element under (x, y).

        Hit-testing recurses into containers, so a click on an element
        inside a container reaches the element itself (not the container).
        """
        # Defocus every element on the screen first; the element that gets the
        # click can re-focus itself in its handle_click.
        self._focused = None
        for e in self._all_elements():
            if hasattr(e, "focused"):
                e.focused = False

        # Find the deepest visible element under the cursor.
        target: Optional[Element] = None
        for e in reversed(self.elements):
            target = e.hit_test(x, y)
            if target is not None:
                break
        if target is None:
            return None

        event = ClickEvent(
            x=x, y=y,
            local_x=x - target.x, local_y=y - target.y,
            button=button, element=target,
        )
        target.handle_click(event)
        if hasattr(target, "focused") and target.focused:
            self._focused = target
        return target

    def dispatch_hover(self, x: int, y: int) -> None:
        for e in self._all_elements():
            inside = e.visible and e.contains(x, y)
            if inside and not e._hovered:
                e._hovered = True
                e.handle_hover(HoverEvent(x, y, x - e.x, y - e.y, entered=True, element=e))
            elif (not inside) and e._hovered:
                e._hovered = False
                e.handle_hover(HoverEvent(x, y, x - e.x, y - e.y, entered=False, element=e))

    def dispatch_key(self, key: int, char: str, pressed: bool) -> None:
        if self._focused is None:
            return
        self._focused.handle_key(KeyEvent(key=key, char=char, pressed=pressed))
