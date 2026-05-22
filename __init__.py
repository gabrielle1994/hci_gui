"""hci_gui — a tiny Pygame-based GUI library for the HCI course.

Two layers:
  * Elements, screens and the event loop (`App`, `Screen`, `Button`, …).
  * Cognitive models in `hci_gui.models`: `geometry` (provided) and
    `fitts` (placeholder you implement in Week 2).

See `HCI/README.md` and `HCI/examples/` for usage.
"""

from .app import App
from .screen import Screen
from .elements import (
    Element,
    Label,
    Button,
    TextBox,
    Checkbox,
    Slider,
    Image,
    Container,
)
from .events import ClickEvent, HoverEvent, KeyEvent
from . import models, colors, theme

__all__ = [
    "App",
    "Screen",
    "Element",
    "Label",
    "Button",
    "TextBox",
    "Checkbox",
    "Slider",
    "Image",
    "Container",
    "ClickEvent",
    "HoverEvent",
    "KeyEvent",
    "models",
    "colors",
    "theme",
]

__version__ = "0.1.0"
