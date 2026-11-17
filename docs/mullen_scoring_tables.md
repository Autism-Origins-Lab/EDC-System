# Mullen scoring tables

The scoring service uses the user's scans of Appendix C. Data is in
`app/services/mullen_norms.py`; date validation and lookup are in
`app/services/mullen_scoring.py`.

## Sources and coverage

- `Adobe Scan Oct 13, 2026.pdf`, PDF page 1, Table C.1: T scores by raw
  score and scale, plus 90%/95% bands of error. Supported age bands are birth
  through 1 month 30 days, 2:0-2:30, and 3:0-3:30, inclusive.
  Their printed raw-score rows are respectively 0-9, 0-10, and 0-11.
  The 4-month band was intentionally removed because the study only assesses
  infants through the 3-month band (ending at 3 months 30 days).
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
interpolated, or assigned a neighboring row. Ages from 4 months 0 days onward
are outside the study's scoring scope. Entered raw scores at these ages
cannot be scored or saved in the Mullen form. A dated summary with no raw
scores may be saved as not administered; an untouched blank section can be
skipped without creating a summary. Do not change the assessment date or use a younger
age band to record an out-of-scope assessment. Supporting older assessments
would require an explicit scope change and verified handbook norms.
The original scans remain in Downloads and are not copied into the repository.

## UI integration

Run `python -m app.main`, open a participant, save their date of birth in
Overview, and advance to Mullen assessment with Save and Continue. Enter the assessment date using the
displayed date format in Date completed, select 90% or 95% confidence, and choose the handbook's
age convention. Raw-score edits automatically update the four C1/C2 fields.
Invalid inputs clear calculated results and show an explanation; saving is
blocked until populated rows can be scored. Date completed is required for
every saved summary and is the date used for scoring. Any or all raw scores
may be blank: these scales display "Not administered", and their calculated
fields remain empty. A raw score of zero is an entered score. DOB, confidence,
and age convention are required when raw scores are entered; a date-only
summary does not require scoring options.

Migration 8 adds the assessment date, DOB used for scoring, confidence level,
and age convention. These are saved atomically with scores. Existing records
retain their scores without invented context. If Overview DOB later changes,
the assessment retains its saved DOB until the user selects Use Overview DOB.
Age equivalents remain available for separate manual entry.

Migration 9 gives each existing assessment a permanent number per patient,
without changing its dates or scores. Use the Summary dropdown to select a
saved assessment, labeled with its number and completion date. Legacy summaries
without a date show "Date not recorded"; supply a date before saving changes.
New summary starts with empty assessment fields and the patient's Overview DOB.
The first save creates a separate summary; subsequent saves update only that
selected summary. Numbers stay fixed when dates change. Reopening a patient
selects the summary most recently saved, including edits to older summaries.

Switching summaries or starting another with unsaved edits offers Save,
Discard, or Cancel. Erasing saved scores and saving with a valid completion
date persists the empty scores; it retains the dated summary. Erasing its
date blocks saving rather than silently restoring answers. Scores and scoring
context are written together in one transaction. Review includes every saved
summary and shows missing raw scores as "Not administered". Workbook export
includes all summaries and adds patient, summary number, and completion date
to score rows; empty numeric values remain empty cells.

In the guided workspace, an untouched Mullen section can be continued past
without creating a summary; its empty answers appear as N/A on the final
review. Clicking New summary explicitly starts a draft that requires Date
completed before saving. A new draft is preserved when moving between workspace
sections. Existing saved summaries always undergo date validation on save,
including after all their scores and options have been erased.
