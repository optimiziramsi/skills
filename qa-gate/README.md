# qa-gate — the done-gate

The `qa-gate@optimiziramsi` plugin, one of the [optimiziramsi marketplace](../README.md)'s per-concern plugins — enable it in the projects that want it.

## Contents

- name: `qa-gate`
  kind: skill + command
  purpose:
    The done-gate — typecheck → unit → e2e → **visual (read the screenshots)** before claiming
    done. Commands stay per-project; the loop and "a red gate reported green is the one
    unforgivable sin" don't.

## Enable

```bash
claude plugin install qa-gate@optimiziramsi --scope project
```
