import csv
from argparse import ArgumentParser
from collections import deque
from collections.abc import Sequence

import matplotlib.pyplot as plt
import pygame
from matplotlib.animation import FuncAnimation
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from pygame.joystick import JoystickType


__all__ = ["JoystickReader", "main"]


class JoystickReader:
    joystick: JoystickType
    axes: Axes
    ani: FuncAnimation
    all_data: list[tuple[deque[float], deque[float]]]
    _running: bool

    def __init__(self) -> None:
        pygame.init()
        pygame.joystick.init()

        self.joystick = pygame.joystick.Joystick(1)
        self.joystick.init()

        plt.ion()
        self.axes: Axes
        fig, self.axes = plt.subplots()
        self.axes.plot([], [], "ro", label="current pos", zorder=1_000_000)
        self.axes.set_xlim(-1.0, 1.0)
        self.axes.set_ylim(-1.0, 1.0)
        self.axes.grid()

        self.all_data = []
        self._on_next()

        self.ani = FuncAnimation(
            fig,
            self._on_update,
            blit=True,
            interval=50,
            cache_frame_data=False,
        )
        self._running = True

        fig.canvas.mpl_connect("key_press_event", self._on_key)
        fig.canvas.mpl_connect("close_event", lambda _: self._on_quit())

    @property
    def xdata(self) -> deque[float]:
        """The current trace x-coordinates"""
        return self.all_data[-1][0]

    @property
    def ydata(self) -> deque[float]:
        """The current trace y-coordinates"""
        return self.all_data[-1][1]

    @property
    def x(self) -> float:
        """The current x-coordinate"""
        return self.xdata[-1]

    @property
    def y(self) -> float:
        """The current y-coordinate"""
        return self.ydata[-1]

    def run(self) -> None:
        try:
            while self._running:
                self._read()

        except KeyboardInterrupt:
            pass

        self._save()

    def _read(self) -> None:
        pygame.event.get()
        x = self.joystick.get_axis(0)
        y = -self.joystick.get_axis(1)
        if self.x != x or self.y != y:
            self.xdata.append(x)
            self.ydata.append(y)

        plt.pause(0.005)

    def _save(self) -> None:
        assert not self._running

        for i, data in enumerate(self.all_data, 1):
            with open(f"joystick{i}.csv", "w") as fh:
                writer = csv.writer(fh)
                writer.writerows(zip(*data))

        pygame.quit()

    def _on_update(self, _) -> list[Line2D]:
        current_pos, *other_traces, current_trace = self.axes.get_lines()
        current_pos.set_data([self.x], [self.y])
        current_trace.set_data(self.xdata, self.ydata)
        return [current_pos, *other_traces, current_trace]

    def _on_next(self) -> None:
        self.all_data.append((deque(maxlen=1_000_000), deque(maxlen=1_000_000)))
        num = len(self.all_data)
        self.axes.plot([], [], "-", label=f"Joystick {num}", zorder=num)
        self.xdata.append(0)
        self.ydata.append(0)

    def _on_quit(self) -> None:
        self._running = False

    def _on_key(self, event) -> None:
        match event.key:
            case "n":
                self._on_next()
            case "q":
                self._on_quit()


def main(argv: Sequence[str] | None = None) -> int:
    ArgumentParser().parse_args(argv)

    jr = JoystickReader()
    jr.run()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
