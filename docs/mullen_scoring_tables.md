# Mullen scoring tables

The scoring service uses the user's scans of Appendix C. Data is in
`app/services/mullen_norms.py`; date validation and lookup are in
`app/services/mullen_scoring.py`.

## Sources and coverage

- `Adobe Scan Oct 13, 2026.pdf`, PDF page 1, Table C.1: T scores by raw
  score and scale, plus 90%/95% bands of error. Supplied age bands are birth
  through 1 month 30 days, 2:0-2:30, 3:0-3:30, and 4:0-4:30, inclusive.
  Their printed raw-score rows are respectively 0-9, 0-10, 0-11, and 0-12.
- `Adobe Scan Oct 13, 2026 (1).pdf`, PDF page 1, Table C.2: percentile
  ranks and descriptive categories for integer T scores 20-80.
- `Adobe Scan Oct 13, 2026 (2).pdf`, PDF page 1, Table C.3: Early Learning
  Composite scores. Reviewed for identification; outside the present scope.
- `Adobe Scan Oct 13, 2026 (3).pdf`, PDF page 1, Table C.4: age equivalents.
  Reviewed for identification; deferred at the user's request.

All C1/C2 numeric cells were visually reviewed, with enlarged inspection of
C1's shaded raw-score labels. No unresolved transcription cells remain.
The first C1 band's lower boundary is explicitly printed as birth.
The scans do not specify the date-subtraction convention. `AGE_CALCULATION`
remains unset; configure it from the handbook or pass `age_calculation`
explicitly. No prematurity correction or age rounding is applied.

## Calling the service

```python
scores = auto_score(
    3,
    date_of_birth="2025-01-01",
    domain="gross_motor",
    assessment_date="2025-03-01",
    confidence_level=90,
    age_calculation="calendar",  # Select only if the handbook specifies it.
)
```

For this example the result is T score 37, band-of-error magnitude 9
(printed as +/-9 at 90%), percentile 10, category "Below Average", and
`age_equivalence=None`.

Both printed confidence levels are supported and callers must select one.
Changing confidence changes only the band-of-error width. Preserve the selected
confidence level alongside saved scores when connecting this service to the UI.

Unlisted ages and raw scores raise `MullenScoringError`; they are never clamped,
interpolated, or assigned a neighboring row. C1 pages for ages beyond 4:30
are needed before scoring those ages. The original scans remain in Downloads
and are not copied into the repository.

## UI integration

Run `python -m app.main`, open a participant, save their date of birth in
Overview, and select Mullen assessment. Enter the assessment date using the
displayed date format, select 90% or 95% confidence, and choose the handbook's
age convention. Raw-score edits automatically update the four C1/C2 fields.
Invalid inputs clear calculated results and show an explanation; saving is
blocked until populated rows can be scored.

Migration 8 adds the assessment date, DOB used for scoring, confidence level,
and age convention. These are saved atomically with scores. Existing records
retain their scores without invented context. If Overview DOB later changes,
the assessment retains its saved DOB until the user selects Use Overview DOB.
Age equivalents remain available for separate manual entry.
