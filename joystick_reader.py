import csv
import sys
from collections import deque
from datetime import datetime
from pathlib import Path

import pygame
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from pygame.joystick import JoystickType
from PySide6.QtCore import Qt
from PySide6.QtCore import QTimerEvent
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QMainWindow
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QWidget


UPDATE_INTERVAL_MS = 50


class JoystickPlotter:
    def __init__(self, parent=None, *, reader: "JoystickReader"):
        self.reader = reader

        self.figure = Figure()
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setParent(parent)

        self.axes.plot([], [], "ro", label="current pos", zorder=1_000_000)
        self.axes.set_xlim(-1.0, 1.0)
        self.axes.set_ylim(-1.0, 1.0)
        self.axes.grid()
        self.axes.legend()
        self.on_next()

        self.animation = FuncAnimation(
            self.figure,
            self.on_update,
            blit=True,
            interval=UPDATE_INTERVAL_MS,
            cache_frame_data=False,
        )

    def on_update(self, _) -> list[Line2D]:
        current_pos, *other_traces, current_trace = self.axes.get_lines()
        current_pos.set_data([self.reader.x], [self.reader.y])
        current_trace.set_data(self.reader.xdata, self.reader.ydata)

        self.axes.legend()
        self.canvas.draw()

        return [current_pos, *other_traces, current_trace]

    def on_next(self) -> None:
        num = len(self.reader.all_data)
        self.axes.plot([], [], "-", label=f"Joystick {num}", zorder=num)

    def on_stop(self, savedir: Path = Path(".")) -> None:
        self.figure.savefig(savedir / "plot.png")


class JoystickReader:
    joystick: JoystickType
    all_data: list[tuple[deque[float], deque[float]]]

    def __init__(self) -> None:
        pygame.init()
        pygame.joystick.init()

        self.joystick = pygame.joystick.Joystick(1)
        self.joystick.init()

        self.all_data = []
        self.on_next()

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

    def on_update(self) -> None:
        pygame.event.get()
        x = self.joystick.get_axis(0)
        y = -self.joystick.get_axis(1)
        if self.x != x or self.y != y:
            self.xdata.append(x)
            self.ydata.append(y)

    def on_stop(self, savedir: Path = Path(".")) -> None:
        for i, data in enumerate(self.all_data, 1):
            with open(savedir / f"joystick{i}.csv", "w") as fh:
                writer = csv.writer(fh)
                writer.writerows(zip(*data))

        pygame.quit()

    def on_next(self) -> None:
        self.all_data.append((deque(maxlen=1_000_000), deque(maxlen=1_000_000)))
        self.xdata.append(0)
        self.ydata.append(0)


class ButtonBar(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        self.next_button = QPushButton("Next (n)", self)
        self.stop_button = QPushButton("Stop (s)", self)

        layout.addWidget(self.next_button)
        layout.addWidget(self.stop_button)

        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Joystick Motion Plotter")

        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)
        self.central_layout = QVBoxLayout(self.main_widget)

        self.reader = JoystickReader()

        self.plotter = JoystickPlotter(parent=self, reader=self.reader)
        self.central_layout.addWidget(self.plotter.canvas)

        self.button_bar = ButtonBar()
        self.central_layout.addWidget(self.button_bar)
        self.button_bar.next_button.clicked.connect(self.on_next)
        self.button_bar.stop_button.clicked.connect(self.on_stop)

        self.timer = self.startTimer(UPDATE_INTERVAL_MS)

    def timerEvent(self, event: QTimerEvent) -> None:
        self.reader.on_update()

    def on_next(self) -> None:
        self.reader.on_next()
        self.plotter.on_next()

    def on_stop(self) -> None:
        ts = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        savedir = Path(f"joystick_reader_{ts}")
        savedir.mkdir(parents=True)
        self.reader.on_stop(savedir)
        self.plotter.on_stop(savedir)
        if (app := QApplication.instance()) is not None:
            app.quit()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        match event.key():
            case Qt.Key.Key_N:
                self.on_next()
            case Qt.Key.Key_S:
                self.on_stop()


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
