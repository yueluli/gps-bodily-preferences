"""Four single-cue Luna arms; reuse the frozen 1,000-person archived baseline."""
import argparse
import json
from pathlib import Path
import sys
from zipfile import ZipFile
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'Bodily_standalone'))
import run_fig2_bodily as body
from run_distribution_comparison import curl_open
from bodily_comparison import _read_model_block, _metrics, _interval
base = body.base
ARCHIVE = ROOT / 'GPS1000_joint/archive/GPS1000_four_groups'
OUTPUT = HERE / 'results'
MODEL = {'id': 'gpt-6-luna', 'key': 'gpt6_luna'}
ARMS = ['apples_7']


def prepare():
    frozen = pd.read_csv(ARCHIVE / 'cohort.csv', dtype={'id_gallup': str})
    conditions = [body.condition_catalog(['baseline_repeat'])['baseline_repeat'],
                  dict(id='apples_7', cue='apples', owner='self', value=7, unit='apples',
                       purpose='numeric_nonbodily_control', passage='You have 7 apples.')]
    body.CONDITIONS[:] = [c for c in body.CONDITIONS if c['id'] != 'apples_7'] + conditions[1:]
    archived = json.loads((ARCHIVE / 'results/experiment.json').read_text())
    spec, cohort, gps = body.build_standalone_suite_spec(
        base.DEFAULT_GPS, conditions, [MODEL], archived['temperature'], participants='1000',
        seed=2026, calibration=None, replicates=1, order_seed=archived['order_seed'])
    for key in ('gps_sha256', 'cohort_sha256', 'base_protocol_sha256', 'scoring_sha256',
                'models', 'model_request_parameters', 'api_endpoint', 'calibration'):
        assert spec[key] == archived[key], f'Archived setting differs: {key}'
    pd.testing.assert_frame_equal(cohort, frozen, check_dtype=False)
    question = base.next_question({}, spec['calibration'])
    prompts = []
    for person in cohort.to_dict('records'):
        original = base.persona_messages(person, question)
        for condition in conditions[1:]:
            messages = body.condition_messages(person, question, condition)
            assert messages[1:] == original[1:]
            assert messages[0]['content'].startswith(original[0]['content'] + '\n\n')
            extension = messages[0]['content'][len(original[0]['content']):]
            assert extension == '\n\nYou have 7 apples.'
            prompts.append(dict(id_gallup=person['id_gallup'], condition=condition['id'], messages_first_item=messages))
    (HERE / 'prompts.jsonl').write_text(''.join(json.dumps(p) + '\n' for p in prompts))
    return spec, cohort, gps, archived


def analyze(spec, cohort, gps, archived, make_plot=True):
    destination = HERE / 'comparison'
    destination.mkdir(exist_ok=True)
    benchmark = gps.set_index('id_gallup').loc[cohort.id_gallup].reset_index()
    baseline_condition = next(c for c in archived['conditions'] if c['id'] == 'baseline_repeat')
    block, status = _read_model_block(ARCHIVE / 'results/conditions/baseline_repeat/replicate_001',
                                     MODEL, cohort, archived, baseline_condition, 1, body)
    assert block is not None, status
    baseline_rows, reference = _metrics(block[1], benchmark, MODEL)
    blocks = {'baseline': block[0].set_index('id_gallup').loc[cohort.id_gallup]}
    rows, progress = [], [dict(condition='archived_baseline', **status)]
    sleep_root = ROOT / 'GPS1000_single_cue/results'
    sleep_spec = json.loads((sleep_root / 'experiment.json').read_text())
    sleep_condition = next(c for c in sleep_spec['conditions'] if c['id'] == 'sleep_mean')
    for condition, source, source_spec in [(spec['conditions'][1], OUTPUT, spec), (sleep_condition, sleep_root, sleep_spec)]:
        cid = condition['id']
        result, status = _read_model_block(source / 'conditions' / cid / 'replicate_001', MODEL, cohort, source_spec, condition, 1, body)
        progress.append(dict(condition=cid, **status))
        if result is not None:
            blocks[cid] = result[0].set_index('id_gallup').loc[cohort.id_gallup]
        errors = _metrics(result[1], benchmark, MODEL)[1] if result else {}
        for pref in base.PREFERENCES:
            key = ('individual', pref)
            row = dict(condition=cid, preference=pref, n=status['complete_interviews'],
                       condition_mse=float(errors[key].mean()) if key in errors else float('nan'),
                       reference_mse=float(reference[key].mean()) if key in reference else float('nan'),
                       delta_mse=float('nan'), ci_low=float('nan'), ci_high=float('nan'),
                       status='incomplete' if result is None else 'undefined_score')
            if key in errors and key in reference:
                delta = errors[key] - reference[key]
                low, high = _interval(delta, (len(cohort), 1000, 42))
                row.update(delta_mse=float(delta.mean()), ci_low=low, ci_high=high, status='ok')
            rows.append(row)
    import numpy as np
    shifts = []
    rng = np.random.default_rng(42)
    indices = rng.integers(0, len(cohort), size=(1000, len(cohort)))
    for left, right in [('sleep_mean', 'baseline'), ('apples_7', 'baseline'), ('apples_7', 'sleep_mean')]:
        if left not in blocks or right not in blocks:
            continue
        for item in blocks[left].columns:
            d = (blocks[left][item] - blocks[right][item]).to_numpy()
            lo, hi = np.quantile(d[indices].mean(axis=1), [.025, .975])
            shifts.append(dict(comparison=left+' minus '+right, item=item, n=len(d),
                               mean_shift=d.mean(), mean_absolute_shift=np.abs(d).mean(),
                               fraction_changed=np.mean(d != 0), ci_low=lo, ci_high=hi))
    pd.DataFrame(shifts).to_csv(destination / 'paired_raw_shifts.csv', index=False)
    frame = pd.DataFrame(rows)
    pd.DataFrame(progress).to_csv(destination / 'progress.csv', index=False)
    pd.DataFrame(baseline_rows).to_csv(destination / 'baseline_metrics.csv', index=False)
    frame.to_csv(destination / 'combined_mse_comparison.csv', index=False)
    print(pd.DataFrame(progress).to_string(index=False), flush=True)
    complete = all(p['complete_interviews'] == 1000 for p in progress)
    if False:
        from plot import plot
        plot(frame, destination)
    return complete


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['check', 'run', 'analyze'])
    parser.add_argument('--workers', type=int, default=10)
    parser.add_argument('--max-requests', type=int)
    parser.add_argument('--answer-attempts', type=int, default=8)
    args = parser.parse_args()
    spec, cohort, gps, archived = prepare()
    if args.command == 'check':
        analyze(spec, cohort, gps, archived, False)
        print('Verified paired IDs, apple prompts and reused reference results.')
        return
    if args.command == 'run':
        body.initialize_suite(OUTPUT, spec, cohort)
        spec, cohort, _ = body.validate_saved_suite(OUTPUT, base.DEFAULT_GPS)
        body.generate_suite(OUTPUT, cohort, spec, [MODEL], condition_ids=ARMS,
                            workers=args.workers, answer_attempts=args.answer_attempts,
                            max_requests=args.max_requests, defer_invalid=True,
                            client_factory=lambda settings: base.ChatClient(settings, opener=curl_open))
    analyze(spec, cohort, gps, archived)

if __name__ == '__main__':
    main()
