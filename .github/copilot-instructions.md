# Copilot Instructions for SRS Vocab Tracker Add-on

## Overview
This codebase implements a Spaced Repetition System (SRS) add-on for vocabulary tracking, primarily in a single file: `# vocab_tracker.py (SRS add-on).txt`. It manages vocabulary review scheduling, event logging, and export for TTS (text-to-speech) or review.

## Key Components
- **SRSState**: Tracks review count, interval, easiness factor (SM-2), and next review date for each vocab entry.
- **VocabTracker**: Main class for managing vocab entries, review events, and SRS state calculations. Handles:
  - Loading vocab entries from a JSONL journal
  - Logging review events (append-only, JSONL)
  - Calculating SRS state per entry using a simplified SM-2 algorithm
  - Exporting vocab lists for TTS/review, including SRS metadata
  - Listing due vocab for today

## Data & File Conventions
- **Data files**: Default to `vocab_journal.jsonl` (entries) and `reviewed_ids.jsonl` (review logs), both in JSONL format.
- **Append-only logs**: All review events are appended, never overwritten.
- **Minimal required entry fields**: `id`, `word`, `context`, `definition`.
- **SRS metadata**: Calculated on-the-fly, not stored in entries.

## Patterns & Practices
- **No external dependencies**: Only standard Python libraries are used.
- **Date handling**: All dates are UTC, ISO format.
- **SM-2 algorithm**: Used for SRS interval calculation, with gentle EF adjustment for quality ratings 3/4.
- **Export logic**: `export_for_tts` includes SRS metadata and can filter for new or reviewed words.
- **Due logic**: `due_today` returns entries whose `next_review` is today or earlier, sorted by oldest due first.

## Usage & Workflows
- **Add vocab**: Append to `vocab_journal.jsonl` (not shown in this file, but expected pattern).
- **Mark reviewed**: Use `mark_reviewed(entry_ids, quality)` to log review events.
- **Export for TTS/review**: Use `export_for_tts()` for a list of vocab with SRS state.
- **Get due words**: Use `due_today()` for today's review list.

## Project Structure
- All logic is in a single file. No build or test scripts are present.
- No external configuration or environment variables required.

## Example Usage
```python
tracker = VocabTracker()
due = tracker.due_today()
tracker.mark_reviewed([e['id'] for e in due], quality=4)
```

## When Contributing
- Maintain append-only log pattern for review events.
- Do not introduce non-standard dependencies.
- Keep all date handling in UTC/ISO format.
- Preserve minimal entry schema for vocab items.

---
If you add new files or workflows, update this document to reflect new conventions or patterns.
