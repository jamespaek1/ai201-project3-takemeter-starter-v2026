"""Import the student's completed local worksheet, without inventing answers.

Usage: .venv/bin/python scripts/import_review.py /path/to/takemeter-review.json
Use --check to validate an export without writing anything. After importing,
commit criteria.md and labels.csv BEFORE running the training notebook.
"""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
AREAS = {'Overall accuracy', 'Per-label performance', 'Balance', 'Consistency', 'Confidence'}


def validate(payload, original, taxonomy):
    submitted = payload.get('items', [])
    if len(submitted) != len(original):
        raise ValueError('The export must contain all 200 original comments.')
    by_id = {str(row['id']): row for row in submitted}
    if len(by_id) != len(original):
        raise ValueError('Duplicate or missing comment IDs.')
    output = []
    for row in original:
        answer = by_id.get(str(row['id']))
        if not answer or answer.get('text') != row['text'] or answer.get('cold') is not row['cold']:
            raise ValueError(f"Original text or cold designation changed: {row['id']}")
        if answer.get('label') not in taxonomy:
            raise ValueError(f"Missing/unknown label: {row['id']}")
        if answer.get('reviewed') is not True:
            raise ValueError(f"Student review is incomplete: {row['id']}")
        status = 'cold; student_labeled_unaided' if row['cold'] else 'AI pre-labeled; student_reviewed'
        note = status + '; source=' + row['source_url']
        if not row['cold']:
            note += '; original_ai_label=' + row['label']
            note += '; corrected=' + str(answer['label'] != row['label']).lower()
        student_note = str(answer.get('note', '')).replace('pending_human_review;', '').replace('pending_cold;', '').strip()
        if student_note:
            note += '; worksheet_note=' + student_note
        output.append({'text': row['text'], 'label': answer['label'], 'note': note})
    counts = Counter(row['label'] for row in output)
    if len(counts) != len(taxonomy) or max(counts.values()) / len(output) > .70:
        raise ValueError(f'Class counts need attention before training (70% cap): {dict(counts)}')
    criteria = payload.get('criteria', [])
    if len(criteria) != 5:
        raise ValueError('Write all five acceptance criteria.')
    areas = set()
    for i, entry in enumerate(criteria, 1):
        target = entry.get('target')
        if isinstance(target, (int, float)) and not isinstance(target, bool) and math.isfinite(target):
            entry['target'] = str(target)
        for field in ('area', 'criterion', 'target', 'reason'):
            if not isinstance(entry.get(field), str) or not entry[field].strip():
                raise ValueError(f'Criterion {i} needs {field}.')
        if entry['area'] not in AREAS:
            raise ValueError(f'Unknown criterion area: {entry["area"]}')
        if not re.search(r'\d', entry['target']):
            raise ValueError(f'Criterion {i} needs a numeric target.')
        areas.add(entry['area'])
    if len(areas) < 3:
        raise ValueError('Criteria must cover at least three areas.')
    hours = payload.get('hours_spent')
    if hours not in (None, ''):
        try:
            hours = float(hours)
        except (TypeError, ValueError) as exc:
            raise ValueError('Hours spent must be a nonnegative number.') from exc
        if not math.isfinite(hours) or hours < 0:
            raise ValueError('Hours spent must be a nonnegative finite number.')
    return output, criteria, hours


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('export', type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    payload = json.loads(args.export.read_text())
    original = json.loads((ROOT/'data/review_items.json').read_text())
    taxonomy = json.loads((ROOT/'data/taxonomy.json').read_text())
    try:
        rows, criteria, hours = validate(payload, original, taxonomy)
    except (ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    print(f'Validated {len(rows)} student-reviewed rows and five student-written criteria.')
    if args.check:
        return
    if (ROOT/'data/review_completed.json').exists():
        parser.error('A review was already imported. Preserve the original before revising it.')
    if (ROOT/'results.json').exists():
        parser.error('Results already exist; do not rewrite the preregistered criteria.')
    buffer = io.StringIO(newline='')
    writer = csv.DictWriter(buffer, fieldnames=['text', 'label', 'note'], lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    csv_text = buffer.getvalue()
    parts = ['# Acceptance criteria — TakeMeter\n',
             'Student-written criteria imported verbatim from the completed review worksheet before assignment training. '
             'Targets are evaluated in Unit 6; model-performance targets must hold across seeds 42, 7, and 2024.\n']
    for i, entry in enumerate(criteria, 1):
        parts.append(f"## {i}. {entry['area']}\n\n{entry['criterion']}\n\n**Target:** {entry['target']}\n\n**Why this target:** {entry['reason']}\n")
    criteria_text = '\n'.join(parts)
    (ROOT/'labels.csv').write_bytes(csv_text.encode())
    (ROOT/'criteria.md').write_text(criteria_text)
    record = {'completed': True, 'imported_at': datetime.now(timezone.utc).isoformat(),
              'labels_sha256': hashlib.sha256((ROOT/'labels.csv').read_bytes()).hexdigest(),
              'criteria_sha256': hashlib.sha256((ROOT/'criteria.md').read_bytes()).hexdigest(),
              'cold_count': 20, 'student_reviewed_ai_count': 180,
              'label_counts': dict(Counter(r['label'] for r in rows)), 'hours_spent': hours}
    (ROOT/'data/review_completed.json').write_text(json.dumps(record, indent=2)+'\n')
    print('Imported labels.csv and criteria.md. Commit both before training; update README counts and workflow.')


if __name__ == '__main__':
    main()
