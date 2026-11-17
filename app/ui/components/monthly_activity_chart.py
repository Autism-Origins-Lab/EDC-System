from datetime import date, datetime

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath
from PySide6.QtWidgets import QSizePolicy, QToolTip, QWidget

from app.ui.theme import (
    DARK_RISK_BAR_AXIS_COLOR,
    DARK_RISK_BAR_TEXT_COLOR,
    METRIC_CHART_HEIGHT,
    MONTHLY_SCREENINGS_COLOR,
    RISK_BAR_AXIS_COLOR,
    RISK_BAR_HIGH_COLOR,
    RISK_BAR_LOW_COLOR,
    RISK_BAR_TEXT_COLOR,
)

# (key, legend label, tooltip label, color), in the fixed order the bars are
# drawn in every month. High and Low reuse the risk chart's colors so a risk
# level looks the same in both charts.
SERIES = [
    ("screened", "Screened", "Patients screened", MONTHLY_SCREENINGS_COLOR),
    ("high", "High risk", "High risk added", RISK_BAR_HIGH_COLOR),
    ("low", "Low risk", "Low risk added", RISK_BAR_LOW_COLOR),
]


def recent_months(count: int, today: date | None = None) -> list[str]:
    """The last `count` months as "YYYY-MM", oldest first, ending this month."""
    today = today or datetime.now().astimezone().date()  # local calendar month
    # Counting months from year 0 turns "step back one month" into plain subtraction.
    current = today.year * 12 + today.month - 1
    return [
        f"{index // 12:04d}-{index % 12 + 1:02d}"
        for index in range(current - count + 1, current + 1)
    ]


class MonthlyActivityChart(QWidget):
    """Grouped bars per month: patients screened, high risk and low risk added.

    - Screened counts a patient in the month of their telephone screening date.
    - High/Low risk counts a patient in the month their record was created.
    Months with nothing still get a slot, so the time axis never has gaps.
    Hovering a month shows its exact counts.
    """

    MONTHS = 6
    WIDTH = 320
    AXIS_WIDTH = 26  # room for the y-axis value labels
    LEGEND_HEIGHT = 18
    LABEL_HEIGHT = 18  # room for the month names under the bars
    BAR_WIDTH = 12
    BAR_GAP = 2  # surface gap between the bars of one month
    RADIUS = 4  # rounds only the top (data) end of each bar

    def __init__(self):
        super().__init__()
        self._months = recent_months(self.MONTHS)
        self._counts = {key: [0] * self.MONTHS for key, *_ in SERIES}
        self.set_theme("Light")
        # Same height as the donut and risk chart so the row lines up.
        self.setFixedSize(self.WIDTH, METRIC_CHART_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)  # hover tooltips without holding a button

    def set_patients(self, patients: list[dict], today: date | None = None) -> None:
        self._months = recent_months(self.MONTHS, today)
        position = {month: index for index, month in enumerate(self._months)}
        self._counts = {key: [0] * self.MONTHS for key, *_ in SERIES}

        def add(key: str, stored_date) -> None:
            # Dates are stored ISO ("YYYY-MM-DD", created_at adds a time), so the
            # first 7 characters are the month. Blank or older dates are skipped.
            index = position.get(str(stored_date or "")[:7])
            if index is not None:
                self._counts[key][index] += 1

        for patient in patients:
            add("screened", patient.get("screening_date"))
            risk = {1: "high", 0: "low"}.get(patient.get("risk"))
            if risk:
                add(risk, patient.get("created_at"))
        self.update()

    def counts(self) -> dict[str, dict[str, int]]:
        """{"YYYY-MM": {"screened": n, "high": n, "low": n}}, for tests and tooltips."""
        return {
            month: {key: self._counts[key][index] for key, *_ in SERIES}
            for index, month in enumerate(self._months)
        }

    def set_theme(self, theme: str) -> None:
        # Bar colors are the same in both themes; only text and axis change.
        dark = theme == "Dark"
        self._text_color = DARK_RISK_BAR_TEXT_COLOR if dark else RISK_BAR_TEXT_COLOR
        self._axis_color = DARK_RISK_BAR_AXIS_COLOR if dark else RISK_BAR_AXIS_COLOR
        self.update()

    def _plot_rect(self) -> QRectF:
        return QRectF(
            self.AXIS_WIDTH,
            self.LEGEND_HEIGHT + 8,
            self.width() - self.AXIS_WIDTH,
            self.height() - self.LEGEND_HEIGHT - 8 - self.LABEL_HEIGHT,
        )

    def _month_at(self, x: float) -> int | None:
        plot = self._plot_rect()
        if not plot.left() <= x < plot.right():
            return None
        return int((x - plot.left()) / (plot.width() / self.MONTHS))

    @staticmethod
    def _month_name(month: str, with_year: bool = False) -> str:
        parsed = date(int(month[:4]), int(month[5:]), 1)
        return parsed.strftime("%b %Y" if with_year else "%b")

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        font = QFont(painter.font())
        font.setPointSize(9)
        painter.setFont(font)
        text = QColor(self._text_color)
        plot = self._plot_rect()

        # Legend across the top: a color square beside each name, so identity
        # is never carried by color alone.
        x = float(self.AXIS_WIDTH)
        for _key, label, _tooltip, color in SERIES:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(color))
            painter.drawRoundedRect(QRectF(x, 4, 10, 10), 2, 2)
            painter.setPen(text)
            label_width = painter.fontMetrics().horizontalAdvance(label)
            painter.drawText(QRectF(x + 14, 0, label_width + 2, self.LEGEND_HEIGHT),
                             Qt.AlignmentFlag.AlignVCenter, label)
            x += 14 + label_width + 16

        # One shared y-scale. The top is at least 1 so empty months don't divide
        # by zero; only 0 and the top value are labelled to keep the axis quiet.
        top_value = max(max(max(values) for values in self._counts.values()), 1)
        painter.setPen(QColor(self._axis_color))
        painter.drawLine(QPointF(plot.left(), plot.top()), QPointF(plot.right(), plot.top()))
        painter.drawLine(QPointF(plot.left(), plot.bottom()), QPointF(plot.right(), plot.bottom()))
        painter.setPen(text)
        for value, y in ((top_value, plot.top()), (0, plot.bottom())):
            painter.drawText(QRectF(0, y - 8, self.AXIS_WIDTH - 6, 16),
                             Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                             str(value))

        slot_width = plot.width() / self.MONTHS
        group_width = len(SERIES) * self.BAR_WIDTH + (len(SERIES) - 1) * self.BAR_GAP
        for index, month in enumerate(self._months):
            slot_left = plot.left() + index * slot_width
            bar_left = slot_left + (slot_width - group_width) / 2
            for key, _label, _tooltip, color in SERIES:
                height = plot.height() * self._counts[key][index] / top_value
                if height > 0:
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QColor(color))
                    painter.drawPath(self._bar_path(
                        QRectF(bar_left, plot.bottom() - height, self.BAR_WIDTH, height)))
                bar_left += self.BAR_WIDTH + self.BAR_GAP

            painter.setPen(text)
            painter.drawText(QRectF(slot_left, plot.bottom() + 2, slot_width, self.LABEL_HEIGHT),
                             Qt.AlignmentFlag.AlignCenter, self._month_name(month))
        painter.end()

    def mouseMoveEvent(self, event) -> None:
        # The whole month column is the hover target, which is much easier to
        # hit than a 12px bar, and the tooltip lists all three counts.
        index = self._month_at(event.position().x())
        if index is None:
            QToolTip.hideText()
            return
        month = self._months[index]
        lines = [self._month_name(month, with_year=True)] + [
            f"{tooltip}: {self._counts[key][index]}" for key, _label, tooltip, _color in SERIES
        ]
        QToolTip.showText(event.globalPosition().toPoint(), "\n".join(lines), self)

    def _bar_path(self, rect: QRectF) -> QPainterPath:
        """A bar with a square baseline end and a rounded top (data) end."""
        radius = min(self.RADIUS, rect.height() / 2, rect.width() / 2)
        path = QPainterPath()
        path.moveTo(rect.left(), rect.bottom())
        path.lineTo(rect.left(), rect.top() + radius)
        path.quadTo(rect.left(), rect.top(), rect.left() + radius, rect.top())
        path.lineTo(rect.right() - radius, rect.top())
        path.quadTo(rect.right(), rect.top(), rect.right(), rect.top() + radius)
        path.lineTo(rect.right(), rect.bottom())
        path.closeSubpath()
        return path
