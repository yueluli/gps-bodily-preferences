"""Compare individual squared-error variance and precision of paired MSE changes."""
import json
import os
from tempfile import TemporaryDirectory
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd

from run_distribution_comparison import OUTPUT, ROOT, LABELS, archived_baseline, body, comparison

os.environ.setdefault("MPLCONFIGDIR", "/tmp/gps-luna-mpl")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CONDITIONS = {
    "baseline_repeat": "Luna baseline",
    "sleep_7h": "Sleep · fixed 7 h",
    "sleep_distribution": "Sleep · distributed",
    "steps_4961": "Steps · fixed 4,961",
    "steps_distribution": "Steps · distributed",
}


def load_scored_conditions():
    spec, cohort, gps = body.validate_saved_suite(OUTPUT, body.base.DEFAULT_GPS)
    model, = spec["models"]
    benchmark = gps.set_index("id_gallup").loc[cohort.id_gallup].reset_index()
    baseline, _ = archived_baseline(spec, cohort, model)
    results = {"baseline_repeat": baseline}
    with ZipFile(ROOT / "results.zip") as archive, TemporaryDirectory() as tmp:
        saved = json.loads(archive.read("results/experiment.json"))
        for condition in saved["conditions"]:
            cid = condition["id"]
            if cid in ("sleep_7h", "steps_4961"):
                member = f"results/conditions/{cid}/replicate_001/"
                if archive.read(member + "cohort.csv") != (OUTPUT / "cohort.csv").read_bytes():
                    raise ValueError(f"Cohort differs for {cid}.")
                folder = Path(tmp) / cid
                folder.mkdir()
                (folder / "responses.sqlite3").write_bytes(archive.read(member + "responses.sqlite3"))
                results[cid], _ = comparison._read_model_block(folder, model, cohort, saved, condition, 1, body)
    for condition in spec["conditions"]:
        cid = condition["id"]
        if cid.endswith("_distribution"):
            results[cid], _ = comparison._read_model_block(
                body.leaf_dir(OUTPUT, cid, 1), model, cohort, spec, condition, 1, body
            )

    return results, benchmark, model, cohort


def main():
    results, benchmark, model, cohort = load_scored_conditions()
    errors = {cid: comparison._metrics(result[1], benchmark, model)[1] for cid, result in results.items()}
    reference = errors["baseline_repeat"]
    previous = pd.read_csv(OUTPUT / "combined_comparison/combined_mse_comparison.csv").set_index(["condition", "preference"])
    rows = []
    n = len(cohort)
    resamples = np.random.default_rng(42).choice(n, size=(n, 1000), replace=True)
    for cid in CONDITIONS:
        for pref in body.base.PREFERENCES:
            key = ("individual", pref)
            error = errors[cid].get(key)
            base_error = reference.get(key)
            row = dict(condition=cid, preference=pref, n=n)
            if error is not None:
                row.update(mse=error.mean(), squared_error_variance=error.var(ddof=1))
            if cid != "baseline_repeat" and error is not None and base_error is not None:
                delta = error - base_error
                draws = delta[resamples].mean(axis=0)
                low, high = np.quantile(draws, [.025, .975])
                assert np.allclose([delta.mean(), low, high], previous.loc[(cid, pref), ["delta_mse", "ci_low", "ci_high"]].to_numpy(float))
                row.update(delta_mse=delta.mean(), paired_change_variance=delta.var(ddof=1),
                           bootstrap_se=draws.std(ddof=1), ci_low=low, ci_high=high)
            rows.append(row)

    frame = pd.DataFrame(rows)
    out = OUTPUT / "combined_comparison"
    frame.to_csv(out / "error_variance.csv", index=False)
    fig, axes = plt.subplots(1, 2, figsize=(13, 6.3))
    fig.subplots_adjust(left=.17, right=.93, bottom=.20, top=.78, wspace=.36)
    for ax, metric, title, cmap, conditions in [
        (axes[0], "squared_error_variance", "a   Variance of individual squared errors", "Blues", list(CONDITIONS)),
        (axes[1], "bootstrap_se", "b   Bootstrap SE of mean ΔMSE", "Oranges", list(CONDITIONS)[1:]),
    ]:
        table = frame.pivot(index="preference", columns="condition", values=metric).reindex(
            index=body.base.PREFERENCES, columns=conditions
        )
        matrix = table.to_numpy()
        maximum = np.nanmax(matrix)
        heatmap = ax.imshow(matrix, cmap=plt.get_cmap(cmap).with_extremes(bad="#edf0f2"),
                            aspect="auto", vmin=0, vmax=maximum, extent=(-.5, len(conditions)-.5, 5.5, -.5))
        ax.set_xticks(range(len(conditions)), [CONDITIONS[c] for c in conditions], rotation=28, ha="left")
        ax.xaxis.tick_top()
        ax.set_yticks(range(len(LABELS)), LABELS if ax is axes[0] else [])
        ax.tick_params(length=0)
        ax.set_title(title, loc="left", pad=64, weight="bold")
        for i, j in np.ndindex(matrix.shape):
            value = matrix[i, j]
            ax.text(j, i, f"{value:.2f}" if np.isfinite(value) else "NA",
                    ha="center", va="center", color="white" if value > maximum*.6 else "#15212b")
        for spine in ax.spines.values():
            spine.set_visible(False)
        fig.colorbar(heatmap, ax=ax, fraction=.048, pad=.035)
    fig.suptitle("How variable is Luna’s agreement with human GPS choices?", y=.98, weight="bold", fontsize=17)
    fig.text(.17, .10, "100 matched participants. Panel a shows how unevenly error is spread across people.",
             fontsize=10)
    fig.text(.17, .063, "Panel b uses 1,000 paired resamples of people. Altruism ΔMSE is undefined because baseline donation is constant.",
             fontsize=10)
    fig.savefig(out / "error_variance.png", dpi=200, facecolor="white")
    plt.close(fig)
    print(frame.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
