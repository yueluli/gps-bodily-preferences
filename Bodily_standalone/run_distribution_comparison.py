"""Resume only the two GPS distribution arms and compare against the archived Luna baseline."""
import argparse
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from zipfile import ZipFile

import pandas as pd

import bodily_comparison as comparison
import run_fig2_bodily as body

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "gps100_luna_distribution"
ARMS = {"sleep_distribution": "Participant-specific sleep",
        "steps_distribution": "Participant-specific steps"}
LABELS = ["Risk taking", "Patience", "Negative reciprocity", "Positive reciprocity", "Altruism", "Trust"]


def curl_open(request, timeout):
    headers = "".join(f"{k}: {v}\n" for k, v in request.header_items())
    # Pass authorization through a private file, keeping it out of process arguments.
    with TemporaryDirectory() as tmp:
        header_file = Path(tmp) / "headers"
        header_file.write_text(headers)
        result = subprocess.run(
            ["curl", "-q", "-sS", "--max-time", str(timeout), "--header", f"@{header_file}",
             "--data-binary", "@-", "--write-out", "\n%{http_code}", request.full_url],
            input=request.data, capture_output=True, check=False,
        )
    if result.returncode:
        raise OSError(f"curl transport error {result.returncode}")
    content, status = result.stdout.rsplit(b"\n", 1)
    if int(status) >= 300:
        raise HTTPError(request.full_url, int(status), "Gateway response", {}, BytesIO(content))
    return BytesIO(content)


def archived_baseline(spec, cohort, model):
    member = "results/conditions/baseline_repeat/replicate_001/"
    with ZipFile(ROOT / "results.zip") as archive, TemporaryDirectory() as tmp:
        saved = json.loads(archive.read("results/experiment.json"))
        if archive.read(member + "cohort.csv") != (OUTPUT / "cohort.csv").read_bytes():
            raise ValueError("Archived baseline cohort differs from the distribution cohort.")
        for field in ("gps_sha256", "base_protocol_sha256", "model_request_parameters", "calibration"):
            if saved[field] != spec[field]:
                raise ValueError(f"Archived baseline differs in {field}.")
        condition = next(c for c in saved["conditions"] if c["id"] == "baseline_repeat")
        if condition != next(c for c in spec["conditions"] if c["id"] == "baseline_repeat"):
            raise ValueError("Archived no-cue condition differs.")
        folder = Path(tmp)
        (folder / "responses.sqlite3").write_bytes(archive.read(member + "responses.sqlite3"))
        return comparison._read_model_block(folder, model, cohort, saved, condition, 1, body)


def analyze(spec, cohort, gps, model):
    baseline, _ = archived_baseline(spec, cohort, model)
    if baseline is None:
        raise ValueError("Archived Luna baseline is incomplete.")
    benchmark = gps.set_index("id_gallup").loc[cohort.id_gallup].reset_index()
    baseline_rows, reference = comparison._metrics(baseline[1], benchmark, model)
    rows = []
    for pref, label in zip(body.base.PREFERENCES, LABELS):
        rows.append(dict(condition="human_gps", preference=pref, domain=label,
                         participants=len(cohort), individual_mse=0, status="human_reference"))
        metric = next(r for r in baseline_rows if r["level"] == "individual" and r["preference"] == pref)
        rows.append(dict(condition="luna_baseline", preference=pref, domain=label,
                         participants=len(cohort), individual_mse=metric["mse"], status=metric["status"]))
    for condition in spec["conditions"]:
        cid = condition["id"]
        if cid not in ARMS:
            continue
        result, progress = comparison._read_model_block(
            body.leaf_dir(OUTPUT, cid, 1), model, cohort, spec, condition, 1, body
        )
        print(f"{cid}: {progress}", flush=True)
        errors = comparison._metrics(result[1], benchmark, model)[1] if result else {}
        for pref, label in zip(body.base.PREFERENCES, LABELS):
            key = ("individual", pref)
            row = dict(condition=cid, preference=pref, domain=label,
                       participants=progress["complete_interviews"],
                       status="undefined_score" if result else "incomplete")
            if key in errors:
                row["individual_mse"] = float(errors[key].mean())
                row["status"] = "undefined_baseline_score"
            if key in errors and key in reference:
                delta = errors[key] - reference[key]
                lo, hi = comparison._interval(delta, (len(cohort), 1000, 42))
                row.update(delta_mse=float(delta.mean()), ci_low=lo, ci_high=hi, status="ok")
            rows.append(row)
    frame = pd.DataFrame(rows).reindex(columns=[
        "condition", "preference", "domain", "participants", "individual_mse",
        "delta_mse", "ci_low", "ci_high", "status",
    ])
    destination = OUTPUT / "four_way_comparison"
    destination.mkdir(exist_ok=True)
    frame.to_csv(destination / "individual_mse.csv", index=False)
    plot(frame, destination)


def plot(frame, destination):
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/gps-luna-mpl")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 5.3))
    fig.subplots_adjust(left=.24, right=.96, top=.80, bottom=.21)
    for (cid, label), color, offset in zip(ARMS.items(), ("#206c96", "#cd793c"), (-.14, .14)):
        arm = frame[frame.condition.eq(cid)]
        ax.plot([], [], "o-", color=color, label=label)
        for index, row in enumerate(arm.itertuples()):
            if row.status == "ok":
                ax.hlines(index + offset, row.ci_low, row.ci_high, color=color, linewidth=2)
                ax.plot(row.delta_mse, index + offset, "o", color=color)
    ax.set_yticks(range(len(LABELS)), LABELS)
    ax.set_ylim(len(LABELS)-.5, -.5)
    ax.axvline(0, color="#626262", linestyle="--", linewidth=1)
    ax.grid(axis="x", alpha=.18)
    ax.spines[["left", "top", "right"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("Change in individual MSE vs archived Luna baseline (95% paired bootstrap interval)")
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1), ncol=2, frameon=False)
    fig.suptitle("Do participant-specific bodily cues improve agreement with GPS participants?",
                 fontsize=14, weight="bold", y=.96)
    complete = frame[frame.condition.isin(ARMS)].groupby("condition").participants.max()
    if (complete < 100).any():
        progress = "  ·  ".join(f"{label}: {complete[cid]}/100 complete" for cid, label in ARMS.items())
        if not frame.delta_mse.notna().any():
            ax.set_xlim(-1, 1)
            ax.text(.5, .5, "Awaiting complete Luna interviews", transform=ax.transAxes,
                    ha="center", va="center", bbox={"facecolor": "white", "edgecolor": "none"})
    else:
        progress = "100 paired GPS participants per arm. Altruism has no baseline score (constant donation responses)."
    fig.text(.24, .08, progress, fontsize=9, color="#555")
    fig.text(.24, .043, "Negative values indicate closer agreement with human GPS scores.", fontsize=9, color="#555")
    fig.savefig(destination / "paired_mse.png", dpi=180)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--curl", action="store_true")
    parser.add_argument("--max-requests", type=int)
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--answer-attempts", type=int, default=4)
    args = parser.parse_args()
    spec, cohort, gps = body.validate_saved_suite(OUTPUT, body.base.DEFAULT_GPS)
    model, = spec["models"]
    if args.run:
        factory = body.base.ChatClient
        if args.curl:
            def factory(settings):
                return body.base.ChatClient(settings, opener=curl_open)
        try:
            body.generate_suite(OUTPUT, cohort, spec, [model], workers=args.workers,
                                answer_attempts=args.answer_attempts, max_requests=args.max_requests,
                                retry_failed=True, client_factory=factory, condition_ids=ARMS)
        finally:
            analyze(spec, cohort, gps, model)
    else:
        analyze(spec, cohort, gps, model)


if __name__ == "__main__":
    main()
