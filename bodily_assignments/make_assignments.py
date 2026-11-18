"""Freeze constant and distribution-based bodily cues for the GPS pilot."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json
import zipfile

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
COHORT = ROOT / "GPS_导师100人名单.csv"
SLEEP_ZIP = Path("C:/Users/Administrator/Downloads/j7sd4-osfstorage-archive.zip")
STEPS = ROOT / "reference_data/steps_percentiles_by_country_gender_20170511.csv"
STEPS_AGE = ROOT / "reference_data/steps_by_age_gender_20170508.csv"
STEPS_MAP = ROOT / "reference_data/world_map_steps_average_20170510.csv"
SEED = 20261110

# ISO-3 (GPS) to ISO-2 (sleep archive), for countries represented in this cohort.
ISO2 = dict(zip(
    "AFG ARE ARG AUS AUT BGD BIH BOL BRA BWA CAN CHE CHL CHN CMR COL CRI CZE DEU DZA EGY ESP EST FIN FRA GBR GEO GHA GRC GTM HTI HUN IDN IND IRN IRQ ISR ITA JOR JPN KAZ KEN KHM KOR LKA LTU MAR MDA MEX MWI NGA NIC NLD PAK PER PHL POL PRT ROU RUS RWA SAU SRB SUR SWE THA TUR TZA UGA UKR USA VEN VNM ZAF ZWE".split(),
    "AF AE AR AU AT BD BA BO BR BW CA CH CL CN CM CO CR CZ DE DZ EG ES EE FI FR GB GE GH GR GT HT HU ID IN IR IQ IL IT JO JP KZ KE KH KR LK LT MA MD MX MW NG NI NL PK PE PH PL PT RO RU RW SA RS SR SE TH TR TZ UG UA US VE VN ZA ZW".split(),
))

cohort = pd.read_csv(COHORT, dtype={"id_gallup": str})
assert len(cohort) == 100 and cohort.id_gallup.is_unique
assert set(cohort.isocode).issubset(ISO2)
with zipfile.ZipFile(SLEEP_ZIP) as zf:
    sleep = pd.read_csv(zf.open("clean_demog_data.csv"), usecols=["age", "gender", "country", "sleep"])
assert len(sleep) == 730187 and sleep.sleep.between(5, 10).all()
steps = pd.read_csv(STEPS)
age_steps = pd.read_csv(STEPS_AGE)
country_means = pd.read_csv(STEPS_MAP).set_index("region").steps_mean_filtered
assert set(steps.percentile) == {"P 25", "P 50", "P 75"}

rng = np.random.default_rng(SEED)
sleep_mean = sleep.sleep.mean()
sleep_median = sleep.sleep.median()
sleep_constant = round(sleep_mean)  # Dataset records sleep in whole hours.
steps_constant = 4961  # Full 717,527-user mean reported in Althoff et al. (2017).

step_pivot = steps.pivot(index=["country", "gender"], columns="percentile", values="steps_mean")
step_pivot = step_pivot.dropna(subset=["P 25", "P 50", "P 75"])
global_sex_q = {}
for sex in ("female", "male"):
    frame = steps[steps.gender.eq(sex)]
    global_sex_q[sex] = {p: np.average(g.steps_mean, weights=g.N)
                         for p, g in frame.groupby("percentile")}
sex_age_mean = {}
for sex in ("female", "male"):
    frame = age_steps[age_steps.gender.eq(sex)]
    sex_age_mean[sex] = np.average(frame.steps_mean, weights=frame.n)


def age_band(age: float) -> str:
    if age < 20:
        return "[15, 20)"
    if age >= 70:
        return "[70, inf)"
    decade = int(age // 10) * 10
    return f"[{decade}, {decade + 10})"


rows = []
for person in cohort.itertuples(index=False):
    sex = "female" if person.gender == 1 else "male"
    sleep_sex = "f" if person.gender == 1 else "m"
    code2 = ISO2[person.isocode]
    band_age = min(70, max(19, float(person.age)))
    band = "19-33" if band_age < 34 else "34-53" if band_age < 54 else "54-70"
    s = sleep[sleep.country.eq(code2) & sleep.gender.eq(sleep_sex)]
    if len(s) >= 30:
        s = s[(s.age.lt(34) if band == "19-33" else s.age.between(34, 53) if band == "34-53" else s.age.ge(54))]
        if len(s) >= 30:
            sleep_tier = "country+sex+age_band"
        else:
            s = sleep[sleep.country.eq(code2) & sleep.gender.eq(sleep_sex)]
            sleep_tier = "country+sex"
    else:
        s = sleep[sleep.gender.eq(sleep_sex)]
        s = s[(s.age.lt(34) if band == "19-33" else s.age.between(34, 53) if band == "34-53" else s.age.ge(54))]
        sleep_tier = "global+sex+age_band"
    sleep_value = int(rng.choice(s.sleep.to_numpy()))

    key = (person.country, sex)
    if key in step_pivot.index:
        q = step_pivot.loc[key]
        step_tier = "country+sex_quantiles;global_age+sex_adjustment"
    else:
        q = global_sex_q[sex].copy()
        if person.country in country_means.index:
            factor = float(country_means[person.country]) / steps_constant
            q = {p: value * factor for p, value in q.items()}
            step_tier = "country_mean+global_sex_quantiles;global_age+sex_adjustment"
        else:
            step_tier = "global_sex_quantiles;global_age+sex_adjustment"
    q25, q50, q75 = (float(q[x]) for x in ("P 25", "P 50", "P 75"))
    # Quantile-matched lognormal approximation; the released file has three quantiles, not person-level steps.
    sigma = (np.log(q75) - np.log(q25)) / 1.3489795
    sampled = float(rng.lognormal(np.log(q50), sigma))
    age_mean = float(age_steps.loc[(age_steps.gender.eq(sex) & age_steps.age.eq(age_band(person.age))), "steps_mean"].iloc[0])
    step_value = max(0, round(sampled * age_mean / sex_age_mean[sex]))
    rows.append({
        "id_gallup": person.id_gallup, "country": person.country, "isocode": person.isocode,
        "age": person.age, "gender": person.gender,
        "sleep_constant_hours": sleep_constant, "steps_constant_per_day": steps_constant,
        "sleep_distribution_hours": sleep_value, "steps_distribution_per_day": step_value,
        "sleep_match": sleep_tier, "sleep_reference_n": len(s), "sleep_age_clamped": not 19 <= person.age <= 70,
        "steps_match": step_tier, "steps_q25": round(q25), "steps_q50": round(q50), "steps_q75": round(q75),
        "steps_age_factor": round(age_mean / sex_age_mean[sex], 4),
    })

result = pd.DataFrame(rows)
assert result.id_gallup.tolist() == cohort.id_gallup.tolist()
assert result.sleep_distribution_hours.between(5, 10).all()
assert result.steps_distribution_per_day.ge(0).all()
result.to_csv(OUT / "gps100_bodily_values.csv", index=False, encoding="utf-8-sig")
result[["id_gallup", "sleep_constant_hours", "steps_constant_per_day"]].to_csv(
    OUT / "gps100_constant_values.csv", index=False, encoding="utf-8-sig")
result[["id_gallup", "sleep_distribution_hours", "steps_distribution_per_day", "sleep_match", "steps_match"]].to_csv(
    OUT / "gps100_distribution_values.csv", index=False, encoding="utf-8-sig")
manifest = {
    "sampling_seed": SEED,
    "cohort_sha256": sha256(COHORT.read_bytes()).hexdigest(),
    "sleep_archive_sha256": sha256(SLEEP_ZIP.read_bytes()).hexdigest(),
    "step_quantiles_sha256": sha256(STEPS.read_bytes()).hexdigest(),
    "sleep_n": len(sleep), "sleep_mean_hours": sleep_mean, "sleep_median_hours": sleep_median,
    "step_full_study_mean": steps_constant,
    "step_full_study_median": None,
    "step_median_note": "The public release does not provide a pooled individual-level median.",
    "sleep_match_counts": result.sleep_match.value_counts().to_dict(),
    "steps_match_counts": result.steps_match.value_counts().to_dict(),
    "sleep_age_clamped_count": int(result.sleep_age_clamped.sum()),
    "assigned_sleep_mean": result.sleep_distribution_hours.mean(),
    "assigned_steps_mean": result.steps_distribution_per_day.mean(),
}
(OUT / "assignment_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(manifest, indent=2, ensure_ascii=False))
