from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from app.ui.theme import METRIC_CHART_HEIGHT


DONUT_PENDING_COLOR = "#D00B60"
DONUT_READY_COLOR = "#08AEA9"
DONUT_EDGE_COLOR = "#5C5C5C"

DONUT_TRACK_COLOR = "#1a1a1a"
DONUT_CENTER_COLOR = "#1a1a1a"
DARK_DONUT_TRACK_COLOR = "#4b5563"
DARK_DONUT_CENTER_COLOR = "#e5e7eb"
DONUT_CENTER_FONT_POINT_SIZE = 14
DONUT_CENTER_FONT_WEIGHT = QFont.Weight.Bold


class DonutChart(QWidget):
    #just draw arcs with QPainter w/ PySide6. no difference in styling
    def __init__(self):
        super().__init__()
        self._segments: list[tuple[str,int,str]] = []
        self._track_color = DONUT_TRACK_COLOR
        self._center_color = DONUT_CENTER_COLOR
        self._center_value: int = 0    # this will be total # of patients
        self.setMinimumSize(METRIC_CHART_HEIGHT, METRIC_CHART_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def set_segments(self, segments: list[tuple[str,int,str]], center_value: int | None = None) -> None:
            self._segments = segments
            self._center_value = center_value if center_value is not None else sum(v for _, v, _ in segments)
            self.update()

    def paintEvent(self, event) -> None:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            side = min(self.width(), self.height())
            thickness = side * 0.18
            margin = thickness/2+4
            rect = QRectF(margin, margin, side-2*margin, side-2*margin)


            denom = self._center_value if self._center_value > 0 else sum(value for _, value, _ in self._segments)
            track_pen = QPen(QColor(self._track_color), thickness)
            track_pen.setCapStyle(Qt.PenCapStyle.FlatCap)
            painter.setPen(track_pen)
            painter.drawArc(rect, 0, 360*16)

            if denom > 0:
                start_angle = 90*16
                for _, value, color in self._segments:
                    if value <= 0:
                        continue
                    span_angle = int(-(value/denom) * 360 * 16)
                    pen = QPen(QColor(color), thickness)
                    pen.setCapStyle(Qt.PenCapStyle.FlatCap)
                    painter.setPen(pen)
                    painter.drawArc(rect, start_angle, span_angle)
                    start_angle += span_angle
            painter.setPen(QColor(self._center_color))
            font = QFont(painter.font())
            font.setPointSize(DONUT_CENTER_FONT_POINT_SIZE)
            font.setWeight(DONUT_CENTER_FONT_WEIGHT)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(self._center_value))
            painter.end()

    def set_theme(self, theme: str) -> None:
        dark = theme == "Dark"
        self._track_color = DARK_DONUT_TRACK_COLOR if dark else DONUT_TRACK_COLOR
        self._center_color = DARK_DONUT_CENTER_COLOR if dark else DONUT_CENTER_COLOR
        self.update()
