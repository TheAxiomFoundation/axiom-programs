# axiom-programs

Declarative compose specs that assemble atomic RuleSpec rules into runnable benefit and tax programs.

## What this is

A program — `us-co/snap` for FY 2026, `us/fiit` for tax year 2026, etc. — is an *assembly* of atomic rules drawn from one or more `rulespec-*` corpora. The assembly itself is **not law**: the law is the source statute / regulation, encoded into atomic RuleSpec files in the appropriate rulespec repo. This repository holds the *declarative specs* describing how those atomic rules combine into a runnable program for a given (jurisdiction, program, fiscal period).

The split:

| Layer | Where |
|---|---|
| Atomic encoded law | `rulespec-us`, `rulespec-us-co`, `rulespec-us-ca`, `rulespec-uk`, … |
| **Program compose specs** | **this repo** |
| Composer (consumes specs, produces compiled artifacts) | `axiom-compose` |
| Microsimulation runtime (executes compiled artifacts over a population) | `axiom-microsim` |
| Oracle comparison harness | `axiom-oracles` |

## Layout

One YAML file per (jurisdiction, program, period). Subdirectories scope by jurisdiction:

```
axiom-programs/
  us/
    fiit/
      fy-2026.yaml
    snap/
      fy-2026.yaml
  us-co/
    snap/
      fy-2026.yaml
  us-ca/
    snap/
      fy-2026.yaml
  us-ny/
    snap/
      fy-2026.yaml
  uk/
    universal-credit/
      fy-2026-27.yaml
```

Naming: the file path mirrors the program identifier (`us-co/snap` → `us-co/snap/fy-2026.yaml`).

## Spec shape (provisional)

The format is whatever `axiom-compose` consumes. The current shape from `axiom-compose#1`'s test fixtures:

```yaml
program: us-co/snap
period: 2026-01
outputs:
  - snap_benefit
  - snap_eligible
scope:
  federal:
    - regulations/7-cfr/273/4
    - regulations/7-cfr/273/6
    # … atomic rule paths in rulespec-us
  state:
    - regulations/10-ccr-2506-1/4.402
    # … atomic rule paths in rulespec-us-co
```

`axiom-compose` resolves the `scope` entries against the relevant rulespec repos, links them via declared `outputs`, and produces a compiled program ready for `axiom-microsim`.

## Why a separate repo

- **Specs are not law.** They belong outside the rulespec corpora, which contain only atomic encoded law.
- **Specs are not the composer.** They belong outside `axiom-compose`, which is the tool.
- **Specs need their own release cycle.** A new fiscal year spec or a new jurisdiction shouldn't require a composer release.
- **The repo isn't US-specific.** UK and Canada programs land here too as those rulespec repos mature.

## Status

Bootstrap. The composer (`axiom-compose#1`) is still draft; specs landed here today document the intended composition but cannot yet be compiled end-to-end. Once the composer graduates, these specs become the canonical inputs.

## Migration backlog

Existing composition that needs to move *into* this repo:

- `rulespec-us-co/policies/cdhs/snap/fy-2026-benefit-calculation.yaml` — bucket-E composition currently lives in the atomic-law repo and needs to come out
- `axiom-microsim/axiom_microsim/project/{co_snap,federal_ctc,federal_income_tax}.py` — per-program Python adapters that should become declarative YAML once the composer can replace them

## Related

- `axiom-compose` — declarative composer (consumer of these specs)
- `axiom-microsim` — microsim runtime
- `axiom-oracles` — oracle comparison harness
- `axiom-encode` — encoder that produces the atomic RuleSpec files
- `axiom-rules-engine` — runtime
