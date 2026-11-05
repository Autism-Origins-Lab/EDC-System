from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath
from PySide6.QtWidgets import QSizePolicy, QWidget

from app.ui.theme import (
    DARK_RISK_BAR_AXIS_COLOR,
    DARK_RISK_BAR_HIGH_COLOR,
    DARK_RISK_BAR_LOW_COLOR,
    DARK_RISK_BAR_TEXT_COLOR,
    DARK_RISK_BAR_UNKNOWN_COLOR,
    METRIC_CHART_HEIGHT,
    RISK_BAR_AXIS_COLOR,
    RISK_BAR_HIGH_COLOR,
    RISK_BAR_LOW_COLOR,
    RISK_BAR_TEXT_COLOR,
    RISK_BAR_UNKNOWN_COLOR,
)

# Database `risk` value -> row label, in the fixed order the bars are drawn.
# The order never changes with the counts so a bar never moves between refreshes.
RISK_LEVELS = [(1, "High"), (0, "Low"), (None, "Unknown")]


class RiskBarChart(QWidget):
    """A static horizontal bar chart of patient counts by familial risk.

    Horizontal bars are used because each row gets a readable text label on the
    left, and every bar starts from the same baseline so lengths compare directly.
    Drawn with QPainter like DonutChart, so no charting dependency is added.
    """

    WIDTH = 340
    LABEL_WIDTH = 78  # room for the longest label, "Unknown"
    VALUE_WIDTH = 40  # room for the count printed after each bar
    BAR_HEIGHT = 26
    RADIUS = 4  # rounds only the data end; the baseline end stays square

    def __init__(self):
        super().__init__()
        self._counts = {value: 0 for value, _ in RISK_LEVELS}
        self.set_theme("Light")
        # Same height as the donut so both charts, and their captions, line up.
        self.setFixedSize(self.WIDTH, METRIC_CHART_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def set_patients(self, patients: list[dict]) -> None:
        """Counts each risk level; any unexpected value is treated as unknown."""
        self._counts = {value: 0 for value, _ in RISK_LEVELS}
        for patient in patients:
            risk = patient.get("risk")
            self._counts[risk if risk in self._counts else None] += 1
        self.update()

    def counts(self) -> dict[str, int]:
        return {label: self._counts[value] for value, label in RISK_LEVELS}

    def set_theme(self, theme: str) -> None:
        # Colors are keyed by the risk value, not by bar position, so a level
        # keeps its color whatever the counts or filters are.
        dark = theme == "Dark"
        self._bar_colors = {
            1: DARK_RISK_BAR_HIGH_COLOR if dark else RISK_BAR_HIGH_COLOR,
            0: DARK_RISK_BAR_LOW_COLOR if dark else RISK_BAR_LOW_COLOR,
            None: DARK_RISK_BAR_UNKNOWN_COLOR if dark else RISK_BAR_UNKNOWN_COLOR,
        }
        self._text_color = DARK_RISK_BAR_TEXT_COLOR if dark else RISK_BAR_TEXT_COLOR
        self._axis_color = DARK_RISK_BAR_AXIS_COLOR if dark else RISK_BAR_AXIS_COLOR
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        font = QFont(painter.font())
        font.setPointSize(11)
        painter.setFont(font)

        bar_left = self.LABEL_WIDTH
        bar_span = self.width() - self.LABEL_WIDTH - self.VALUE_WIDTH
        # Each bar is centered in an equal share of the height, so the rows
        # spread over the full chart height instead of bunching at the top.
        row_height = self.height() / len(RISK_LEVELS)
        # Scale to the largest bar so it fills the width; max(..., 1) avoids a
        # divide-by-zero when there are no patients (all bars are then empty).
        largest = max(max(self._counts.values()), 1)

        for row, (value, label) in enumerate(RISK_LEVELS):
            top = row * row_height + (row_height - self.BAR_HEIGHT) / 2
            count = self._counts[value]

            # Labels and counts use the text color, never the bar color.
            painter.setPen(QColor(self._text_color))
            painter.drawText(
                QRectF(0, top, bar_left - 10, self.BAR_HEIGHT),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                label,
            )

            width = bar_span * count / largest
            if width > 0:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(self._bar_colors[value]))
                painter.drawPath(self._bar_path(QRectF(bar_left, top, width, self.BAR_HEIGHT)))

            painter.setPen(QColor(self._text_color))
            painter.drawText(
                QRectF(bar_left + width + 8, top, self.VALUE_WIDTH, self.BAR_HEIGHT),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                str(count),
            )

        # A thin baseline that every bar grows from keeps lengths comparable
        # even when a count is zero and its bar is not drawn.
        painter.setPen(QColor(self._axis_color))
        painter.drawLine(bar_left, 0, bar_left, self.height())
        painter.end()

    def _bar_path(self, rect: QRectF) -> QPainterPath:
        """A bar with a square baseline end and a rounded data end."""
        radius = min(self.RADIUS, rect.width() / 2)
        path = QPainterPath()
        path.moveTo(rect.left(), rect.top())
        path.lineTo(rect.right() - radius, rect.top())
        path.quadTo(rect.right(), rect.top(), rect.right(), rect.top() + radius)
        path.lineTo(rect.right(), rect.bottom() - radius)
        path.quadTo(rect.right(), rect.bottom(), rect.right() - radius, rect.bottom())
        path.lineTo(rect.left(), rect.bottom())
        path.closeSubpath()
        return path
