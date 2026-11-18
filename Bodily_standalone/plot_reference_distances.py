"""Plot direct MSE against the archived Luna baseline and against human GPS."""
import numpy as np
import pandas as pd

from plot_error_variance import CONDITIONS, LABELS, OUTPUT, body, comparison, load_scored_conditions, plt

BASELINE = "baseline_repeat"
COLORS = ["#505965", "#147bb0", "#147bb0", "#cd6a23", "#cd6a23"]
MARKERS = ["o", "s", "D", "s", "D"]


def plot(frame, reference, out):
    selected = frame[frame.reference.eq(reference)]
    conditions = [cid for cid in CONDITIONS if reference != "baseline" or cid != BASELINE]
    fig, axes = plt.subplots(2, 3, figsize=(13, 7.5), sharex=True)
    fig.subplots_adjust(left=.19, right=.98, bottom=.15, top=.86, hspace=.45, wspace=.19)
    limit = np.ceil(selected.ci_high.max() * 2) / 2
    for i, (ax, pref, title) in enumerate(zip(axes.flat, body.base.PREFERENCES, LABELS)):
        subset = selected[selected.preference.eq(pref)].set_index("condition")
        for y, cid in enumerate(conditions):
            row = subset.loc[cid]
            style = list(CONDITIONS).index(cid)
            if pd.isna(row.mse):
                ax.text(.04 * limit, y, "NA", color="#666", va="center")
            else:
                ax.hlines(y, row.ci_low, row.ci_high, color=COLORS[style], lw=1.8)
                ax.plot(row.mse, y, MARKERS[style], color=COLORS[style], markersize=6,
                        markerfacecolor="white", markeredgewidth=1.6)
        ax.set_xlim(0, limit)
        ax.set_ylim(len(conditions)-.5, -.5)
        ax.set_yticks(range(len(conditions)), [CONDITIONS[c] for c in conditions] if i % 3 == 0 else [])
        ax.set_title(title, fontsize=12)
        ax.grid(axis="x", alpha=.22)
        ax.set_axisbelow(True)
        ax.tick_params(axis="y", length=0)
        ax.spines[["left", "top", "right"]].set_visible(False)
        if i >= 3:
            ax.set_xlabel("Individual MSE")
    title = ("Distance from the no-cue Luna baseline" if reference == "baseline"
             else "Distance from human GPS choices")
    fig.suptitle(title, fontsize=16, weight="bold", y=.96)
    fig.text(.19, .073, "Lower MSE means closer agreement. Points are means and lines are 95% bootstrap intervals.",
             fontsize=10)
    fig.text(.19, .043, "100 matched participants. Scores standardized separately by condition and reference. NA indicates an undefined score.",
             fontsize=10)
    fig.savefig(out / f"distance_to_{reference}.png", dpi=200, facecolor="white")
    plt.close(fig)


def main():
    results, benchmark, model, cohort = load_scored_conditions()
    scores = {cid: result[1].set_index("id_gallup").loc[cohort.id_gallup] for cid, result in results.items()}
    human = benchmark.set_index("id_gallup").loc[cohort.id_gallup]
    rows = []
    for cid in CONDITIONS:
        for pref in body.base.PREFERENCES:
            column = f"{pref}_{model['key']}"
            condition = comparison._z(scores[cid][column])
            for reference, target in [("baseline", scores[BASELINE][column]), ("human", human[pref])]:
                if reference == "baseline" and cid == BASELINE:
                    continue
                row = dict(condition=cid, preference=pref, reference=reference, n=len(cohort),
                           mse=np.nan, ci_low=np.nan, ci_high=np.nan)
                target = comparison._z(target)
                if condition is not None and target is not None:
                    error = (condition - target) ** 2
                    low, high = comparison._interval(error, (len(cohort), 1000, 42))
                    row.update(mse=error.mean(), ci_low=low, ci_high=high)
                rows.append(row)
    frame = pd.DataFrame(rows)
    out = OUTPUT / "combined_comparison"
    previous = pd.read_csv(out / "error_variance.csv").set_index(["condition", "preference"])
    human_results = frame[frame.reference.eq("human")].set_index(["condition", "preference"])
    assert np.allclose(human_results.mse, previous.mse.reindex(human_results.index), equal_nan=True)
    frame.to_csv(out / "reference_distances.csv", index=False)
    for reference in ("baseline", "human"):
        plot(frame, reference, out)
    print(frame.pivot(index=["reference", "preference"], columns="condition", values="mse").round(3))


if __name__ == "__main__":
    main()
