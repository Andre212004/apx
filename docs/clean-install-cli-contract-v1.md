# APX Clean-Install and Promotion CLI Contract v1

Status: command vocabulary accepted for pure planning and future bounded
execution. Only existing read-only APX commands are implemented today; the
commands below do not yet exist and authorize no effect.

## Rules

- Every mutation has a prior read-only plan command.
- A mutation accepts only an exact plan digest and approval reference.
- Disk paths, host paths, commands, scripts, package names, UIDs/GIDs, devices,
  mount options, services, environment variables, and destinations are never
  caller arguments.
- Friendly names resolve to registered internal identities before planning.
- JSON output uses the same closed schemas as human-readable output.
- `ready-for-separate-approval` never means approved or executed.
- Unknown subcommands and fields fail; there is no plugin command fallback.

## Bootstrap Console Commands

```text
apx install observe
apx install dossier --target-evidence <evidence-ref> --supply-evidence <evidence-ref>
apx install stage-plan --dossier <dossier-digest> --stage <fixed-stage>
apx install stage-apply --plan <plan-digest> --approval <approval-ref>
apx install recovery-status
apx install recovery-plan --operation <operation-id> --choice <fixed-choice>
apx install recovery-apply --plan <plan-digest> --approval <approval-ref>
```

`<evidence-ref>` is a future trusted evidence-store identity, not a filesystem
path. `<fixed-stage>` is exactly one of the ten stages in
`clean-install-foundation-v1.md`. Stage application cannot skip predecessors or
inherit approval from another stage.

`observe`, `dossier`, `stage-plan`, and `recovery-status` are read-only.
`stage-apply` is unavailable until the matching executor effect family exists.

## Development Candidate Commands

These run inside Development and have no host authority:

```text
apx development release-build-plan --role hub-headless
apx development release-build --plan <plan-digest>
apx development release-inspect --candidate <development-candidate-id>
apx development release-export-plan --candidate <development-candidate-id>
```

The builder selects sources only from the admitted definition and dated source
policy. It does not accept arbitrary build commands, package additions, output
paths, hooks, or credentials. Export produces one immutable candidate identity;
it does not admit or install it.

## Hub Promotion Commands

These are typed requests from the Hub management client:

```text
apx release inspect --candidate <candidate-ref>
apx release import-plan --candidate <candidate-ref>
apx release import --plan <plan-digest> --approval <approval-ref>
apx release verification-status --quarantine <quarantine-id>
apx release admission-plan --quarantine <quarantine-id>
apx release admit --plan <plan-digest> --approval <approval-ref>

apx hub replacement-plan --release <release-id>
apx hub replacement-create --plan <plan-digest> --approval <approval-ref>
apx hub replacement-status --operation <operation-id>
apx hub replacement-select-plan --generation <generation-id>
apx hub replacement-select --plan <plan-digest> --approval <approval-ref>
apx hub retirement-plan --generation <generation-id>
apx hub retire --plan <plan-digest> --approval <strong-approval-ref>
```

Candidate, quarantine, release, operation, and generation references are closed
registered IDs. None is a caller path or URL. Import, verification, admission,
replacement creation, selection, and retirement are separate journaled state
machines. Approval for one cannot authorize the next.

## Initial Environment Commands

After the first Hub is verified:

```text
apx environment create-plan --name development --release <release-id>
apx environment create --plan <plan-digest> --approval <approval-ref>
apx environment activate-plan --name development
apx environment activate --plan <plan-digest> --approval <approval-ref>
apx environment stop-plan --name development
apx environment stop --plan <plan-digest> --approval <approval-ref>
```

The `development` role definition supplies Git, Codex, compiler, and tests.
Callers cannot smuggle package lists through `create`. The existing executor v1
already models generic create/activate/stop plans, but no real transport or
effect implementation exists.

## Next Contract Work

Implementation proceeds in this order:

1. pure parsers and deterministic plans;
2. fake evidence/quarantine/catalogue stores;
3. interruption and hostile-input fixtures;
4. read-only CLI rendering;
5. minimum-privilege effect adapters;
6. disposable-machine rehearsal;
7. target-bound approval.

No command may be made mutating merely to accelerate installation before its
state machine, recovery behavior, and independent verifier exist.
