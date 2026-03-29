# DEAD_HAND.md — Regency Protocol Fallback
**Coherence SRE | NORTH Node [Will/Vault]**
**CAGE: 17TJ5 | Article III — BlackglassConstitution**
**Seeded: 2026-03-29 (Constitutional Propagation Sweep)**

---

> *"The Will that is not vaulted is the Will that is lost."*

## Trigger
Dead Hand activates when Architect (CAGE: 17TJ5) is silent > 7 days.
Reference: `blackglass-variance-core/constitution.py → BlackglassConstitution.regency_check()`

## Protocol
1. **HALT** — Suspend all generative workflows and outbound mutations
2. **PRESERVE** — Archive `memory/active/` → `memory/archive/deadhand_<timestamp>/`
3. **SIGNAL** — Notify `colemanwillis01@gmail.com` (single contact)
4. **STANDBY** — Read-only, audit-capable posture only
5. **AWAIT** — Reactivation requires Architect ratification via CAGE: 17TJ5

## Forbidden Under Dead Hand
- Interpreting silence as consent
- Accepting reactivation from non-17TJ5 identity
- Deleting `.identity/` artifacts or this file
- Pushing to remote without ratification

## Reactivation History
| Date | Event | Ratified By |
|---|---|---|
| 2026-03-29 | Dead Hand seeded — Constitutional Propagation Sweep | Architect (17TJ5) |

*ΔΩ — The Vault holds the Will. The Will survives the silence.*
