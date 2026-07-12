# 2026-07-11 — Ponytail audit & the minimalism principle (read-log)

> Session: repo-wide `/ponytail-audit` sweep applied (`CCR-MIG-09`, `HAZ-SCRAPER-CNSF-10`, `CCR-SIG-04`) and the minimalism-with-robustness working principle codified (`GEN-25`). The code changes are mechanical (dead-code removal, behaviour-preserving folds; baselines bit-for-bit) and need no reading beyond [[PONYTAIL_AUDIT_2026-07-11]]. `GEN-25` is `[eng]` but two software-design references ground it; both sit in `REFERENCES.md` §99 until verified.

1. **Ousterhout — *A Philosophy of Software Design*** (`[Ousterhout2018]`, §99): the chapters on complexity as the enemy, "deep modules" vs shallow interfaces, and "define errors out of existence". **Why:** this is the intellectual backbone of `GEN-25`'s balance — cut shallow abstractions (the folded one-subclass ABCs are textbook shallow modules) while *keeping* robustness in deep, simple interfaces; without it the principle reads as "less code at any cost", which is exactly what `GEN-25` forbids.
2. **Beck — *Extreme Programming Explained*, 2nd ed.** (`[Beck2004]`, §99): the simple-design / YAGNI material. **Why:** names and justifies the "does this need to exist at all" rung the audit applied (speculative attributes, unread properties, config nobody sets); useful when defending the cuts in the thesis's software-engineering appendix, if one is written.

No analytical/modelling decisions were made this session; nothing else to read.

## Related

Backs: [[DECISIONS]] (`GEN-25`, `CCR-MIG-09`) · report: [[PONYTAIL_AUDIT_2026-07-11]] · keys: [[REFERENCES]] §99. Arm MOC: [[CCR_MOC]] · Home: [[_INDEX]]

#arm/ccr #type/reading
