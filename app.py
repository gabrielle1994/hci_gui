"""The top-level `App`: a single window, an event loop, and a screen router.

You create one App, attach one or more Screens to it, and call `app.run()`
to open the window. See `examples/01_hello_window.py` for the smallest
possible program.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import pygame

from .screen import Screen


class App:
    """One window, many screens.

    Args:
        width, height:  window size in pixels
        title:          window title bar
        fps:            target framerate; the loop sleeps to hit it
    """

    def __init__(
        self,
        width: int = 800,
        height: int = 600,
        title: str = "hci_gui app",
        fps: int = 60,
    ) -> None:
        self.width = int(width)
        self.height = int(height)
        self.title = title
        self.fps = int(fps)

        self.screens: Dict[str, Screen] = {}
        self.current: Optional[Screen] = None
        self._history: List[str] = []

        self._running = False
        self._surface: Optional[pygame.Surface] = None

    # ---- Screen management ----------------------------------------------

    def add_screen(self, screen: Screen, make_current: Optional[bool] = None) -> Screen:
        """Register a screen. The first one added becomes the active screen."""
        if screen.name in self.screens:
            raise ValueError(f"Screen named {screen.name!r} already exists")
        self.screens[screen.name] = screen
        screen._app = self
        if make_current or (make_current is None and self.current is None):
            self.current = screen
            if screen.on_show:
                screen.on_show(screen)
        return screen

    def go_to(self, name: str) -> None:
        """Switch to another screen by its name."""
        if name not in self.screens:
            raise KeyError(f"Unknown screen: {name!r}. "
                           f"Known: {list(self.screens)}")
        if self.current is not None:
            self._history.append(self.current.name)
        self.current = self.screens[name]
        if self.current.on_show:
            self.current.on_show(self.current)

    def go_back(self) -> None:
        """Return to the previously shown screen, if any."""
        if self._history:
            target = self._history.pop()
            self.current = self.screens[target]
            if self.current.on_show:
                self.current.on_show(self.current)

    # ---- Running --------------------------------------------------------

    def _init_pygame(self) -> None:
        if self._surface is not None:
            return
        pygame.display.init()
        pygame.font.init()
        self._surface = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(self.title)

    def stop(self) -> None:
        """Stop the main loop. Safe to call from a button callback."""
        self._running = False

    def screenshot(self, path: str) -> None:
        """Save the current frame as a PNG. Useful for screenshots in reports."""
        if self._surface is None:
            self._init_pygame()
            if self.current is not None:
                self.current.draw(self._surface)
        pygame.image.save(self._surface, path)

    def run(self) -> None:
        """Open the window and start the event loop."""
        if not self.screens:
            raise RuntimeError("No screens have been added; call app.add_screen(...) first.")
        self._init_pygame()
        clock = pygame.time.Clock()
        self._running = True

        while self._running:
            for event in pygame.event.get():
                self._handle_event(event)

            if self.current is not None:
                self.current.draw(self._surface)
            pygame.display.flip()
            clock.tick(self.fps)

    # ---- Internal -------------------------------------------------------

    def _handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self._running = False
            return
        if self.current is None:
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.current.dispatch_click(event.pos[0], event.pos[1], event.button)
        elif event.type == pygame.MOUSEMOTION:
            self.current.dispatch_hover(event.pos[0], event.pos[1])
        elif event.type == pygame.KEYDOWN:
            char = event.unicode if event.unicode else ""
            self.current.dispatch_key(event.key, char, pressed=True)
        elif event.type == pygame.KEYUP:
            self.current.dispatch_key(event.key, "", pressed=False)
