"""
Coordinated laser + galvo controller.
Synchronizes laser color/blanking with mirror positioning for pattern drawing.
"""
import time
import threading

from ..motor.galvo import Galvo
from ..laser.rgb_driver import RGBLaser
from .. import config


class LaserController:
    """
    High-level controller that synchronizes laser output with galvo positioning.

    Handles blanking (laser off during moves), settle time, and provides
    draw primitives and continuous pattern re-tracing for POV effects.

    Args:
        pi: pigpio.pi instance
    """

    def __init__(self, pi):
        self._pi = pi
        self.galvo = Galvo(pi)
        self.laser = RGBLaser(pi)

        self._tracing = False
        self._trace_thread = None
        self._trace_lock = threading.Lock()

    def enable(self):
        """Enable both motors and master laser output."""
        self.galvo.enable()
        self.laser.on()

    def disable(self):
        """Disable motors and turn laser off."""
        self.stop_tracing()
        self.laser.off()
        self.galvo.disable()

    def move_to(self, x, y):
        """
        Move to position (normalized coords) with laser blanked.

        Args:
            x: X position (-1.0 to 1.0)
            y: Y position (-1.0 to 1.0)
        """
        with self.laser.blanked():
            self.galvo.move_to_normalized(x, y)
            time.sleep(config.BLANKING_SETTLE_TIME)

    def draw_line(self, x1, y1, x2, y2, color=(255, 255, 255)):
        """
        Draw a line from (x1,y1) to (x2,y2) with the laser on.

        Blanks, moves to start, turns on laser, moves to end.

        Args:
            x1, y1: Start position (normalized)
            x2, y2: End position (normalized)
            color: (R, G, B) tuple (0-255)
        """
        # Blank move to start
        self.move_to(x1, y1)

        # Laser on, draw to end
        self.laser.set_color(*color)
        self.galvo.move_to_normalized(x2, y2)

    def draw_path(self, points, color=(255, 255, 255)):
        """
        Draw connected line segments through a list of points.

        Blanks to the first point, then draws laser-on segments to each
        subsequent point.

        Args:
            points: List of (x, y) normalized coordinate tuples
            color: (R, G, B) tuple (0-255)
        """
        if not points:
            return

        # Blank move to first point
        first = points[0]
        self.move_to(first[0], first[1])

        # Draw through remaining points
        self.laser.set_color(*color)
        for point in points[1:]:
            self.galvo.move_to_normalized(point[0], point[1])
            time.sleep(config.MIN_POINT_DWELL_TIME)

    def draw_path_colored(self, points_with_colors):
        """
        Draw connected segments with per-segment color.

        Args:
            points_with_colors: List of (x, y, r, g, b) tuples
        """
        if not points_with_colors:
            return

        first = points_with_colors[0]
        self.move_to(first[0], first[1])
        self.laser.set_color(first[2], first[3], first[4])

        for x, y, r, g, b in points_with_colors[1:]:
            self.laser.set_color(r, g, b)
            self.galvo.move_to_normalized(x, y)
            time.sleep(config.MIN_POINT_DWELL_TIME)

    def trace_loop(self, points, color=(255, 255, 255)):
        """
        Continuously re-trace a path for persistence-of-vision effect.

        Runs in a background thread. Call stop_tracing() to stop.

        Args:
            points: List of (x, y) normalized coordinate tuples
            color: (R, G, B) tuple (0-255)
        """
        self.stop_tracing()

        self._tracing = True
        self._trace_thread = threading.Thread(
            target=self._trace_worker,
            args=(list(points), color),
            daemon=True,
        )
        self._trace_thread.start()

    def stop_tracing(self):
        """Stop the background tracing loop."""
        self._tracing = False
        if self._trace_thread is not None:
            self._trace_thread.join(timeout=2.0)
            self._trace_thread = None

    @property
    def is_tracing(self):
        """Whether a pattern is currently being traced."""
        return self._tracing

    def _trace_worker(self, points, color):
        """Background worker that continuously re-draws a path."""
        if len(points) < 2:
            self._tracing = False
            return

        try:
            # Initial blank move to first point
            self.move_to(points[0][0], points[0][1])
            self.laser.set_color(*color)

            while self._tracing:
                for point in points:
                    if not self._tracing:
                        break
                    self.galvo.move_to_normalized(point[0], point[1])
                # After completing the shape, loop back to start
                # (move to first point with laser ON for closed shapes)
        finally:
            self.laser.set_color(0, 0, 0)
            self._tracing = False

    def get_status(self):
        """Return combined status of galvo and laser."""
        return {
            'galvo': self.galvo.get_status(),
            'laser': self.laser.get_status(),
            'tracing': self._tracing,
        }
