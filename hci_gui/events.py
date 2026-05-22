"""Event objects passed to element callbacks (`on_click`, `on_change`, …).

You only need to read these if your callback takes a parameter, e.g.
`Button("OK", x, y, on_click=lambda evt: print(evt.x, evt.y))`.
A zero-argument callback works too.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ClickEvent:
    """Mouse click on an element.

    Attributes:
        x, y:       absolute mouse position in window pixels
        local_x, local_y: position relative to the element's top-left corner
        button:     mouse button index (1=left, 2=middle, 3=right)
        element:    the element that was clicked (filled in by the dispatcher)
    """
    x: int
    y: int
    local_x: int
    local_y: int
    button: int = 1
    element: Optional[object] = None


@dataclass
class HoverEvent:
    x: int
    y: int
    local_x: int
    local_y: int
    entered: bool = True
    element: Optional[object] = None


@dataclass
class KeyEvent:
    """A key press / release.

    Attributes:
        key:     pygame key constant (e.g. pygame.K_RETURN)
        char:    the printable character or '' for non-printable keys
        pressed: True for key-down, False for key-up
    """
    key: int
    char: str
    pressed: bool = True
