"""Read-only counts for the four new arms; never contacts the API."""
import json
from pathlib import Path
import sqlite3
ROOT = Path(__file__).resolve().parent
rows = []
for arm in ['sleep_mean', 'sleep_individual', 'steps_mean', 'steps_individual']:
    path = ROOT / 'results/conditions' / arm / 'replicate_001/responses.sqlite3'
    row = dict(condition=arm, complete_interviews=0, successful_answers=0)
    if path.exists():
        with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as db:
            row['successful_answers'] = db.execute("SELECT count(*) FROM answers WHERE status='success'").fetchone()[0]
            row['complete_interviews'] = db.execute("SELECT count(*) FROM (SELECT person FROM answers WHERE status='success' GROUP BY person HAVING count(*)=20)").fetchone()[0]
    rows.append(row)
print(json.dumps(rows, indent=2))
print('Total accepted:', sum(r['successful_answers'] for r in rows), '/ 80000')
print('Final figure:', (ROOT / 'comparison/fixed_distribution_six_panels.png').exists())
