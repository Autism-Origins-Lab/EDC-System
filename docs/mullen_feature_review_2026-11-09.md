# Mullen feature review — November 9, 2026

Reviewed the PySide6 frontend, scoring service, SQLite persistence and migrations, guided workspace, review summary, workbook export, and backup coverage. This is a code and behavior review; no Apple design criteria were used in the findings. Application code and real patient data were not changed. All reproductions used isolated synthetic records.

There are **eight findings: three high priority and five medium priority**. Address the missing scoring band, clearing behavior, and legacy-record workflow first.

## 1. High — the advertised 4-month scoring band is missing

**Location:** `app/services/mullen_norms.py:9–63`; coverage text in `app/ui/forms/mullen_view.py:93–95`.

`C1_TABLE` contains only birth–1:30, 2:0–2:30, and 3:0–3:30. The UI and `docs/mullen_scoring_tables.md` promise coverage through 4:30, and existing regression tests expect that fourth band.

**Reproduction:** DOB `2025-01-01`, assessment `2025-05-01`, raw score `3`, confidence `90`, calendar convention. Every scale raises “No handbook age band … at 4 months 0 days.” The UI clears the derived fields and refuses to save the populated assessment. Nine existing tests fail because this band is absent, including its 4:30 endpoint.

**Address:** Restore the fourth band from the source scan and verify every row independently. Do not infer the missing table from neighboring ages or a few test expectations. If its absence is intentional, revise the advertised coverage and explicitly support how affected assessments should be recorded. The original scans were not rechecked during this review.

**Resolution — November 16, 2026:** The study owner confirmed that the 4-month
band was removed intentionally. Supported scoring ends at 3 months 30 days.
The UI and scoring documentation now reflect that limit, and regression tests
expect 4:0 and 4:30 to be rejected rather than scored. Populated out-of-scope
assessments remain blocked from saving; an untouched blank Mullen section can
be skipped without creating scores. The historical reproduction and test counts
above describe the original review, before this scope clarification.

## 2. High — clearing a saved assessment reports success but restores old answers

**Location:** `app/ui/dialogs/patient_detail_view.py:569–570,591`; `app/ui/forms/mullen_view.py:400–407`.

The workspace skips all Mullen persistence whenever `has_answers()` is false. This handles a never-entered optional section, but also skips an intentional clear of an existing assessment. Reload then restores the old database values.

**Reproduction:** Save Gross Motor raw `3` with valid context. Clear the assessment date, reset both selectors, and clear all raw scores and age equivalents. `has_answers()` returns false; `save_current_section()` returns true; raw `3` immediately reappears and remains in the database.

**Address:** Distinguish untouched empty sections from previously saved sections that were cleared. Persist clearing scores and context atomically, or provide an explicit “Clear assessment” action. Verify that save, reopen, review, and export all remain empty afterward.

**Resolution — November 16, 2026:** Replaced the single-summary workflow with
separate numbered summaries per patient. New summaries start blank; the
selector identifies each by number and completion date, and reopening selects
the most recently saved summary. A completion date is required to save. Any
or all raw scores may be blank, representing "Not administered"; saving those
blanks clears the selected summary's scores atomically with its scoring options.
Erasing the completion date blocks saving and leaves the draft visible.
An untouched optional section still creates no record. Review and export now
include every saved summary, with blank numeric export cells preserved.

## 3. High — legacy records load but cannot pass Save and Continue unchanged

**Location:** `app/ui/forms/mullen_view.py:257–280,409–427`; `app/database/migrations/versions/v008_mullen_scoring_context.py:7–21`.

Migration 8 correctly preserves historical scores without inventing dates or scoring options. The current UI nevertheless requires this context and recalculates on every save, including an unchanged historical record. The existing raw score makes the workspace call that save path instead of skipping the section.

**Reproduction:** Save a legacy Gross Motor record without context, then reopen it. The workspace has no unsaved changes, but Save and Continue fails with “Enter the assessment date …” and remains at step 7. Historical assessments outside current scoring coverage remain blocked after context is supplied.

There is a second compatibility failure: the repository and its existing tests support legacy age equivalents such as `"12 months"`. The UI loads that value, but `collect_data()` requires an integer. Even after supplying supported scoring inputs, saving fails with the generic numeric-entry warning.

**Address:** Support preserving unchanged legacy records without forced rescoring. Make conversion to automatic scoring an explicit operation with complete context and coverage checks. Define and migrate the age-equivalent representation while preserving original historical values. Add UI coverage for records created before migration 8, including out-of-coverage ages and textual age equivalents.

## 4. Medium — backend saves can persist invalid scores and stale scoring context

**Location:** `app/database/repositories/forms.py:205–281`.

The repository validates domain/field names and supplied context, but writes score values without checking their types, ranges, or consistency. Context is optional and can change independently of the stored scores.

**Reproductions:**

- A save with raw `-5`, T score `999`, percentile `500`, and error width `-3` succeeds.
- Save raw `3` with the March context above, producing T `37`. Call `save_mullen_assessment(patient_id, {}, context=...)` with assessment date changed to April 1. The stored date changes, but T stays `37`; the scoring service returns `31` for that new context.

The current Mullen UI recalculates before saving, so these reproductions exercise the repository directly. This is a backend integrity gap, not evidence that ordinary UI entry accepts those values.

**Address:** Add a validated assessment save service that owns context and derived values. Recompute or reject dependent scores when context changes, validate numeric fields, and keep a separate explicit path for preserved legacy/manual records.

## 5. Medium — missing uniqueness constraints can make saves and reads disagree

**Location:** `app/database/schema.py:142–168`; `app/database/repositories/forms.py:230–239,282–291,326–347`.

The schema does not enforce one assessment per patient or one domain score per assessment. The writer selects the oldest matching assessment and score, while the reader combines all assessments and keeps the last score for each domain. Context is read from the oldest assessment.

**Reproduction:** In a synthetic database, insert a second assessment for the same patient with Gross Motor raw `8`. Save raw `4` through the normal repository. The write updates the first assessment; `get_mullen_assessment()` still returns `8` from the second. Scores can also be paired with context from a different assessment.

This required inserting duplicate rows directly; the sequential UI save path did not itself create duplicates. No claim is made that duplicates exist in the real database.

**Address:** Establish the intended cardinality. For the current one-assessment workflow, add a migration that safely reconciles existing duplicates, then enforces `UNIQUE(patient_id)` and `UNIQUE(mullen_assessments_id, domain)`. If repeated assessments are intended, use explicit assessment IDs throughout save, read, review, and UI selection.

## 6. Medium — manual age equivalents can become stale, with no clear units or source

**Location:** `app/ui/forms/mullen_view.py:182–185,290–326,350`.

The recalculation loop clears and updates four derived fields but leaves manually entered age equivalents unchanged. Changing or removing a raw score therefore retains a value entered for the previous score. The column says only “Age Equivalent,” and the placeholder `e.g. 24` does not specify units or that entry is manual. Other calculated columns look similar.

**Reproduction:** Enter raw `3` and age equivalent `24`, then remove the raw score. Save succeeds with raw, T, percentile, category, and error all null, while age equivalent remains `24`. Changing the raw score also retains `24` without requesting confirmation.

**Address:** Label the field as manual and state its units. When the corresponding raw score changes, clear the manual value or mark it for explicit reconfirmation. If standalone manual age equivalents are intentional, make that supported mode clear and preserve their source/provenance.

## 7. Medium — nested scrolling hides most of the score table and narrow columns clip results

**Location:** `app/ui/forms/mullen_view.py:204–224`; `app/ui/dialogs/patient_detail_view.py:374–379`.

The table is placed inside a scrolling page, which is itself inside a scrolling window body. Its five rows are each 68 pixels high, but its own viewport is much shorter.

**Observed in headless renders with Segoe UI:**

- At the default `1200 × 800` window, the table viewport is 114 pixels tall: one full row and part of the next. Comparing all five scales requires scrolling inside the table.
- At the supported minimum `820 × 600`, the table starts below the initial page viewport. After scrolling the page, the table still needs its own vertical and horizontal scrolling.
- At that width, the category editor is 63 pixels wide while “Below Average” needs approximately 86 pixels before padding. The visible result is clipped; the T-score explanatory header is clipped too.

**Address:** Give the table enough height for its header and all five rows, with the surrounding page handling vertical scrolling. Set useful minimum widths for result columns, use wrapped read-only displays or full-value tooltips, and allow horizontal scrolling instead of squeezing text into unusable fields. Recheck both themes and supported window sizes on native Windows.

## 8. Medium — score editors lack accessible field names

**Location:** `app/ui/forms/mullen_view.py:66–76,152–185,436–465`.

Editors inserted with `setCellWidget()` receive no accessible name or description. The visible row and column text does not become the embedded line edit's accessible name in the tested Qt accessibility interface. The DOB editor inside the horizontal form row also lacks that association.

**Verification:** `QAccessible.queryAccessibleInterface(...).text(QAccessible.Text.Name)` returns an empty string for the Gross Motor raw-score editor and DOB editor. This confirms missing names at the Qt interface level; an end-to-end Windows screen-reader session was not performed.

**Address:** Give each editor a descriptive name such as “Gross Motor raw score” or “Gross Motor age equivalent, months, manual,” label the DOB editor explicitly, and provide appropriate accessible descriptions for calculated values. Verify keyboard focus order and Narrator or NVDA output.

## Validation and working behavior

Ran the following existing suites against temporary databases with Qt offscreen:

```text
tests/ui/test_mullen_view.py
tests/database/test_mullen_context.py
tests/services/test_mullen_scoring.py
tests/services/test_mullen_norms.py
tests/services/test_exports.py
tests/services/test_backups.py
tests/ui/test_patient_workspace.py
```

Result: **173 passed, 11 failed**. Nine failures are the missing 4-month band. The other two are existing telephone-screening workspace tests that reference the removed `view.navigation` attribute (`tests/ui/test_patient_workspace.py:619,636`); they do not establish a Mullen runtime defect.

The passing coverage verifies ordinary supported-age calculation, zero scores, live recalculation, read-only calculated fields, save/reopen, invalid-input save blocking, preserved DOB snapshots, atomic rollback of context and scores, workbook export links, and backup/restore of Mullen data. These behaviors should be retained when addressing the findings.

Additional synthetic probes reproduced findings 2–6 and queried the accessibility names. Light and dark renders were inspected at `1200 × 800` and `820 × 600`. Temporary evidence is under `.tmp/mullen-evidence-41e5cbe0/`; the reproduction script is `.tmp/mullen_review_probe.py`.

Scope limits: this review did not inspect real patient records, revalidate the handbook transcription, perform clinical validation, test a native screen reader, or implement fixes. Age-equivalent automation and Early Learning Composite scoring are documented as deferred and are not counted as defects.
