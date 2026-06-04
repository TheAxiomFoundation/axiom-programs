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

Deployment note: YAML files under `uk/`, `us-*`, and `us/` are compose
specs, not direct `axiom-rules-engine` inputs. Deployments that do not have
`axiom-compose` available should consume a precomposed RuleSpec file or a
precompiled engine artifact from `artifacts/`.

## Layout

One YAML file per (jurisdiction, program, period). Subdirectories scope by jurisdiction:

```
axiom-programs/
  us/
    fiit/
      fy-2026.yaml
    payroll/
      oasdi-wage-tax/
        fy-2026.yaml
    snap/
      fy-2026.yaml
  us-co/
    snap/
      fy-2026.yaml
  us-ca/
    snap/
      fy-2026.yaml
  us-al/
    snap/
      fy-2026.yaml
  us-ma/
    snap/
      fy-2026.yaml
  us-ny/
    snap/
      fy-2026.yaml
  us-tn/
    snap/
      fy-2026.yaml
  uk/
    universal-credit/
      fy-2026-27.yaml
  artifacts/
    uk/
      universal-credit/
        fy-2026-27.rulespec.yaml
        fy-2026-27.compiled.json
        fy-2026-27.manifest.json
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

## Deployment artifacts

`artifacts/` contains generated outputs for deployment environments that should
not depend on private composer access at runtime:

- `*.rulespec.yaml` is the composed `format: rulespec/v1` file accepted by
  `axiom-rules-engine compile`.
- `*.compiled.json` is the compiled engine artifact accepted by
  `axiom-rules-engine run-compiled`.
- `*.manifest.json` records the source spec, tool commits, hashes, and
  regeneration commands.

For UK Universal Credit, deployments can use
`artifacts/uk/universal-credit/fy-2026-27.compiled.json` directly. The source
spec remains `uk/universal-credit/fy-2026-27.yaml`.

## Status

Bootstrap, but the active FY 2026 SNAP specs are real compose inputs. The
current AL, CA, CO, MA, NC, NY, SC, and TN SNAP specs can be composed with
`axiom-compose` and compiled with `axiom-rules-engine` into end-to-end
`snap_eligible` and `snap_benefit` calculators. The US payroll OASDI wage-tax
spec composes the employee Social Security tax rule from `rulespec-us`. Some
state specs still carry known policy coverage gaps, but they are executable
program assemblies, not placeholders.

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
