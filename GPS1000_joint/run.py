"""Run only the three added GPS1000 arms, with the archived no-cue reference."""
import argparse
import json
from pathlib import Path
import sys

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "Bodily_standalone"))
import run_fig2_bodily as body
from run_distribution_comparison import curl_open

base = body.base
ARCHIVE = HERE / "archive/GPS1000_four_groups"
OUTPUT = HERE / "results"
ARMS = ("joint_mean", "joint_levels", "individual_draw")
MODEL = {"id": "gpt-6-luna", "key": "gpt6_luna"}


def prepare():
    options = {"dtype": {"id_gallup": str}}
    frozen = pd.read_csv(ARCHIVE / "cohort.csv", **options)
    levels = pd.read_csv(ARCHIVE / "assignments.csv", **options)
    draws = pd.read_csv(HERE / "distribution_source.csv", **options)
    columns = ["id_gallup", "sleep_percentile", "sleep_level", "steps_percentile", "steps_level"]
    pd.testing.assert_frame_equal(levels[columns], draws[columns])
    assert len(frozen) == frozen.id_gallup.nunique() == 1000
    assert levels.id_gallup.tolist() == frozen.id_gallup.tolist()
    assert len(levels.groupby(["sleep_percentile", "steps_percentile"])) == 25
    assert levels.groupby(["sleep_percentile", "steps_percentile"]).size().eq(40).all()
    assert draws.sleep_draw.between(5, 10).all() and draws.steps_draw.gt(0).all()
    assignments = draws.assign(sleep_mean=7, steps_mean=4961)
    records = assignments.set_index("id_gallup")
    for arm, suffix in zip(ARMS, ("mean", "level", "draw")):
        pairs = zip(records["sleep_" + suffix], records["steps_" + suffix])
        passages = {pid: f"Last night you slept for {h} hours. You have walked {k:,} steps today."
                    for pid, (h, k) in zip(records.index, pairs)}
        body.CONDITIONS.append(dict(id=arm, cue="sleep_and_steps", owner="self", value=None,
                                    unit=None, purpose="joint", passage="{}", assigned_values=passages))
    catalog = body.condition_catalog(["baseline_repeat", *ARMS])
    conditions = [catalog[key] for key in ("baseline_repeat", *ARMS)]
    archived = json.loads((ARCHIVE / "results/experiment.json").read_text())
    spec, cohort, gps = body.build_standalone_suite_spec(
        base.DEFAULT_GPS, conditions, [MODEL], archived["temperature"],
        participants="1000", seed=2026, calibration=None, replicates=1,
        order_seed=archived["order_seed"])
    for key in ("gps_sha256", "cohort_sha256", "base_protocol_sha256", "scoring_sha256",
                "models", "model_request_parameters", "api_endpoint", "calibration"):
        if spec[key] != archived[key]:
            raise ValueError(f"Archived setting differs: {key}")
    pd.testing.assert_frame_equal(cohort, frozen, check_dtype=False)
    first = base.next_question({}, spec["calibration"])
    people = {p["id_gallup"]: p for p in cohort.to_dict("records")}
    seen = set()
    for line in (ARCHIVE / "prompts.jsonl").read_text().splitlines():
        row = json.loads(line)
        pid, arm = row["id_gallup"], row["condition"]
        expected = base.persona_messages(people[pid], first)
        if arm == "sleep_levels":
            expected[0]["content"] += f"\n\nLast night you slept for {records.loc[pid, 'sleep_level']} hours."
        if arm == "steps_levels":
            expected[0]["content"] += f"\n\nYou have walked {records.loc[pid, 'steps_level']:,} steps today."
        assert row["messages_first_item"] == expected
        seen.add((pid, arm))
    assert len(seen) == 3000
    prompts = [
        dict(id_gallup=pid, condition=arm, messages_first_item=body.condition_messages(person, first, catalog[arm]))
        for pid, person in people.items() for arm in ARMS
    ]
    for row in prompts:
        original = base.persona_messages(people[row["id_gallup"]], first)
        modified = row["messages_first_item"]
        assert modified[1] == original[1]
        assert modified[0]["content"] == original[0]["content"] + "\n\n" + catalog[row["condition"]]["assigned_values"][row["id_gallup"]]
    return spec, cohort, gps, archived, assignments, prompts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "run", "analyze"))
    parser.add_argument("--arms", nargs="+", choices=ARMS, default=ARMS)
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--max-requests", type=int)
    parser.add_argument("--answer-attempts", type=int, default=4)
    args = parser.parse_args()
    spec, cohort, gps, archived, assignments, prompts = prepare()
    if args.command == "check":
        assignments.to_csv(HERE / "assignments.csv", index=False)
        (HERE / "prompts.jsonl").write_text("".join(json.dumps(r) + "\n" for r in prompts))
        print("Verified 1,000 archived IDs and 3,000 archived prompts. Exported 3,000 joint prompts.")
        return
    if args.command == "run":
        body.initialize_suite(OUTPUT, spec, cohort)
        spec, cohort, _ = body.validate_saved_suite(OUTPUT, base.DEFAULT_GPS)
        body.generate_suite(OUTPUT, cohort, spec, [MODEL], condition_ids=args.arms,
                                     workers=args.workers, answer_attempts=args.answer_attempts,
                                     max_requests=args.max_requests, defer_invalid=True,
                                     client_factory=lambda settings: base.ChatClient(settings, opener=curl_open))
    from compare import analyze
    analyze(spec, cohort, gps, archived)


if __name__ == "__main__":
    main()
