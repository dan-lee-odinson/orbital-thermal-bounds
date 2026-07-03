# Biswas / Suncatcher - author-provided clarifications (R0)

> **These values are `author-provided clarification`, NOT independently reproduced.** They are
> recorded here as the author's stated baseline for a *future* reproduction target (R1/R2).
> `orbital-thermal-bounds` makes **no** reproduction, ranking, or endorsement claim about them
> in R0. No private-message text is quoted; only the technical values the author provided are
> recorded, and these values are also derivable from the public `v1.2` repository.

## Stated thermal baseline (author-provided)

Dr. Samarjith Biswas states that the Part-I thermal baseline is unchanged at `v1.2`:

| Quantity | Author-provided value | Status |
|---|---|---|
| Radiator temperature `T_rad` | `21.3 C` | author-provided; unreproduced |
| Junction temperature `T_j` | `111.3 C` | author-provided; unreproduced |
| `T_j`, single heat-pipe failure | `114.8 C` | author-provided; unreproduced |
| Resistance chain `R_th` (before optimization) | `0.350 K/W` | author-provided; unreproduced |
| Resistance chain `R_th` (after optimization) | `0.300 K/W` | author-provided; unreproduced |

Consistency note (observational only): the pinned standalone script
`report-1/report_one_thermal.py` carries matching input assumptions (four `300 W` TPUs =
`1.2 kW` compute, `4.0 m^2` single-sided radiator, `eps = 0.85` EOL, `650 km` dawn-dusk SSO,
`125 C` junction limit). This is noted for orientation; **the script was not run and the above
outputs were not reproduced in R0.**

## Contextual mass / lifetime (author-provided; not a thermal result)

Recorded as context for Track R (R7), kept separate from the thermal baseline and **not**
reproduced:

- integrated dry mass ~ `220 kg` (older bus figure `375 kg`); launch mass `233 kg`;
- corrected moderate-solar natural-decay lifetime ~ `12 years` (earlier figure ~`19.6 years`);
- full solar-cycle band roughly `2.4 to 175 years`;
- passive-disposal conclusion unchanged: active deorbit is still needed.

The pinned commit subject ("Reconcile satellite mass to the integrated model
(220 kg dry / 233 kg launch)") is consistent with this mass reconciliation.

## Handling rules

- Do **not** present any value above as locally reproduced or validated.
- Any public-documentation summary of these values requires the project director's approval
  and must retain the `author-provided clarification` label.
- Reproduction (R1 standalone, R2 package-level) and harmonization (R4/R5) are future work;
  the author cross-check (R7) is `source-author review`, not independent external validation.
