"""Compare complete, protocol-validated arms with the archived baseline and GPS."""
from html import escape
import numpy as np
import pandas as pd
from bodily_comparison import _metrics, _read_model_block
from run import ARCHIVE, ARMS, MODEL, OUTPUT, base, body

LABELS = dict(zip(
    ("baseline_repeat", "sleep_levels", "steps_levels", *ARMS),
    ("Baseline", "Sleep levels", "Step levels", "Joint mean", "Joint levels", "Individual draws"),
))


def analyze(spec, cohort, gps, archived):
    destination = OUTPUT.parent / "comparison"
    destination.mkdir(parents=True, exist_ok=True)
    reference = pd.read_csv(ARCHIVE / "human_reference.csv", dtype={"id_gallup": str})
    columns = ["id_gallup", *base.PREFERENCES]
    pd.testing.assert_frame_equal(
        reference[columns].set_index("id_gallup").loc[cohort.id_gallup].reset_index(),
        gps[columns].set_index("id_gallup").loc[cohort.id_gallup].reset_index(),
        check_dtype=False,
    )
    benchmark = cohort[["id_gallup", "isocode", "wgt"]].merge(reference[columns], on="id_gallup", validate="one_to_one")
    blocks, metrics, errors, progress = {}, [], {}, []
    for arm in LABELS:
        new = arm in ARMS
        folder = (OUTPUT if new else ARCHIVE / "results") / "conditions" / arm / "replicate_001"
        condition = next((c for c in spec["conditions"] if c["id"] == arm), None)
        block, status = _read_model_block(folder, MODEL, cohort, spec if new else archived,
                                          condition if new else None, 1, body)
        progress.append(dict(condition=arm, **status))
        if block is not None:
            blocks[arm] = block[0].set_index("id_gallup").loc[cohort.id_gallup]
            rows, errors[arm] = _metrics(block[1], benchmark, MODEL)
            metrics.extend(dict(condition=arm, **row) for row in rows)
    rng = np.random.default_rng(42)
    bootstrap = {n: rng.integers(0, n, size=(1000, n)) for n in (len(cohort), cohort.isocode.nunique())}
    shifts, delta = [], []
    baseline = blocks["baseline_repeat"]
    for arm, raw in blocks.items():
        if arm == "baseline_repeat":
            continue
        for item in raw.columns:
            change = (raw[item] - baseline[item]).to_numpy()
            low, high = np.quantile(change[bootstrap[len(change)]].mean(axis=1), [.025, .975])
            shifts.append(dict(condition=arm, item=item, n=len(change), mean_shift=change.mean(),
                               ci_low=low, ci_high=high, mean_absolute_shift=np.abs(change).mean(),
                               fraction_changed=np.mean(change != 0)))
        for key, error in errors[arm].items():
            if key not in errors["baseline_repeat"]:
                continue
            change = error - errors["baseline_repeat"][key]
            low, high = np.quantile(change[bootstrap[len(change)]].mean(axis=1), [.025, .975])
            delta.append(dict(condition=arm, level=key[0], preference=key[1], delta_mse=change.mean(),
                              ci_low=low, ci_high=high))
    frames = {"progress": pd.DataFrame(progress), "gps_metrics": pd.DataFrame(metrics),
              "paired_raw_shifts": pd.DataFrame(shifts), "paired_delta_mse": pd.DataFrame(delta)}
    for name, frame in frames.items():
        frame.to_csv(destination / f"{name}.csv", index=False)
    ranking = frames["gps_metrics"].query("level == 'individual' and preference == 'all_six_equal' and status == 'ok'").sort_values("mse")
    bars = []
    max_mse = max(ranking.mse, default=1)
    for row in ranking.itertuples():
        width = 100 * row.mse / max_mse
        bars.append(f'<div class="bar"><span>{LABELS[row.condition]}</span>'
                    f'<div><b style="width:{width:.2f}%"></b></div><span>{row.mse:.4f}</span></div>')
    panels = []
    domains = frames["gps_metrics"].query("level == 'individual' and preference != 'all_six_equal' and status == 'ok'")
    scale = max(domains.mse, default=1)
    for pref, label in zip(base.PREFERENCES, base.LABELS):
        panel = []
        for row in domains[domains.preference.eq(pref)].itertuples():
            panel.append(f'<div class="bar"><span>{LABELS[row.condition]}</span>'
                         f'<div><b style="width:{100 * row.mse / scale:.2f}%"></b></div><span>{row.mse:.3f}</span></div>')
        panels.append(f'<section><h3>{label}</h3>{"".join(panel)}</section>')
    sections = []
    for name, frame in frames.items():
        sections.append(f"<h2>{escape(name.replace('_', ' ').title())}</h2>" +
                        frame.to_html(index=False, float_format=lambda v: f"{v:.4f}"))
    complete = all(arm in blocks for arm in ARMS)
    status = "All six AI conditions complete." if complete else "Interim report. Joint arms appear in the comparisons only after all 1,000 interviews in that arm finish."
    document = f"""<!doctype html><meta charset="utf-8"><title>GPS1000 bodily cues</title>
<style>body{{font:16px system-ui;max-width:1100px;margin:40px auto;padding:0 24px;color:#182c37}}
.bar{{display:grid;grid-template-columns:145px 1fr 75px;gap:12px;margin:10px 0;align-items:center}}
.bar b{{display:block;height:18px;background:#247b85}}
.panels{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,400px),1fr));gap:22px}}table{{border-collapse:collapse;font-size:14px}}
td,th{{padding:6px 9px;border-bottom:1px solid #dce4e7;text-align:left}}</style>
<h1>GPS1000 bodily cues</h1><p>{status}</p>
<h2>Which prompt is closest to GPS humans?</h2>
<p>Individual MSE averaged equally across the six preferences. Lower is closer. Undefined domains prevent a condition from entering the overall ranking.</p>
{''.join(bars)}
<div class="panels">{''.join(panels)}</div>
<p>Paired change in MSE uses the archived no-cue baseline. Negative values indicate improved fit to GPS.
Country-level results use weighted means and are reported separately.</p>
<h2>How did responses change from baseline?</h2>
<p>Paired raw shifts show direction, size and the fraction of people whose answer changed.
Adaptive choice sequences are compared through their final staircase categories.
Intervals use 1,000 paired bootstrap draws conditional on the observed generations and fixed scoring.</p>
<p>Individual draws are simulated from external marginal distributions. They represent fixed GPS-ID assignments.
The archived baseline was generated in a separate run, and sampling noise can contribute to observed differences.</p>
{''.join(sections)}
"""
    (destination / "report.html").write_text(document)
    print(destination / "report.html")


