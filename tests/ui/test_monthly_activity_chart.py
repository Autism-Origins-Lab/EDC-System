from datetime import date

from app.ui.components.monthly_activity_chart import MonthlyActivityChart, recent_months


def test_recent_months_cross_the_year_boundary():
    assert recent_months(3, date(2026, 2, 14)) == ["2025-12", "2026-01", "2026-02"]


def test_counts_screenings_by_screening_date_and_risk_by_created_month(qtbot):
    chart = MonthlyActivityChart()
    qtbot.addWidget(chart)
    chart.set_patients(
        [
            {"risk": 1, "created_at": "2026-10-03 09:00:00", "screening_date": "2026-11-02"},
            {"risk": 0, "created_at": "2026-10-20 09:00:00", "screening_date": ""},
            {"risk": None, "created_at": "2026-11-01 09:00:00", "screening_date": "2026-10-05"},
            # Older than the six months shown, so it is left out.
            {"risk": 1, "created_at": "2025-01-01 09:00:00", "screening_date": None},
        ],
        today=date(2026, 11, 4),
    )

    counts = chart.counts()
    assert list(counts) == recent_months(6, date(2026, 11, 4))
    assert counts["2026-10"] == {"screened": 1, "high": 1, "low": 1}
    assert counts["2026-11"] == {"screened": 1, "high": 0, "low": 0}
    assert sum(sum(month.values()) for month in counts.values()) == 4
