"""Plot the five Luna conditions against a common human GPS zero line."""
import numpy as np
import pandas as pd

from plot_reference_distances import CONDITIONS, BASELINE, LABELS, OUTPUT, body, plt

out = OUTPUT / "combined_comparison"
frame = pd.read_csv(out / "reference_distances.csv")
mse = frame[frame.reference.eq("human")].pivot(index="preference", columns="condition", values="mse")
mse = mse.reindex(index=body.base.PREFERENCES, columns=list(CONDITIONS))
delta = mse.subtract(mse[BASELINE], axis=0).drop(columns=BASELINE)
styles = [("#414c5a", "o", "--"), ("#1575a7", "s", "--"), ("#1575a7", "D", "-"),
          ("#c35e20", "s", "--"), ("#c35e20", "D", "-")]
fig, (tab, ax) = plt.subplots(1, 2, figsize=(14, 6.7), width_ratios=[1, 1.25])
fig.subplots_adjust(left=.14, right=.97, top=.79, bottom=.18, wspace=.16)
y = np.arange(len(LABELS))
for (cid, name), (color, marker, line) in zip(CONDITIONS.items(), styles):
    ax.plot(mse[cid], y, color=color, linestyle=line, marker=marker, ms=5,
            markerfacecolor="white", lw=1.5, label=name)
ax.axvline(0, color="#292c30", lw=1.5)
ax.text(0, 1.025, "Human GPS = 0", transform=ax.get_xaxis_transform(), ha="center", fontsize=10, weight="bold")
ax.set_xlim(-.15, 2.35)
ax.set_ylim(5.5, -.5)
ax.set_yticks([])
ax.set_xlabel("Distance to human GPS (individual MSE)")
ax.set_xticks(np.arange(0, 2.1, .5))
ax.grid(axis="x", alpha=.18)
ax.tick_params(axis="y", length=0)
ax.spines[["left", "top", "right"]].set_visible(False)
ax.legend(loc="lower center", bbox_to_anchor=(.53, 1.08), ncol=3, frameon=False, fontsize=9)

tab.set_title("Change in MSE vs Luna baseline", fontsize=11, pad=24, weight="bold")
tab.set_xlim(-.5, 3.5)
tab.set_ylim(ax.get_ylim())
tab.set_xticks(range(4), ["Sleep\nfixed", "Sleep\ndistributed", "Steps\nfixed", "Steps\ndistributed"])
tab.xaxis.tick_top()
tab.tick_params(length=0)
tab.set_yticks(y, LABELS)
for i, j in np.ndindex(delta.shape):
    value = delta.iloc[i, j]
    color = "#156448" if value < 0 else "#9b482b" if value > 0 else "#66717d"
    tab.text(j, i, f"{value:+.3f}" if np.isfinite(value) else "NA", color=color, ha="center", va="center")
for spine in tab.spines.values():
    spine.set_visible(False)
fig.suptitle("How close are Luna’s choices to human GPS choices?", y=.97, weight="bold", fontsize=16)
fig.text(.14, .09, "Closer to 0 means closer to human choices. A negative change means lower error than the Luna baseline.", fontsize=10)
fig.text(.14, .055, "100 matched participants. Line gaps indicate undefined scores. All 20 paired change intervals include zero.", fontsize=10)
fig.savefig(out / "human_zero_comparison.png", dpi=200, facecolor="white")
plt.close(fig)
