# hotfix — test-first hotfix protocol

The `hotfix@optimiziramsi` plugin, one of the [optimiziramsi marketplace](../README.md)'s per-concern plugins — enable it in the projects that want it.

## Contents

- name: `hotfix`
  kind: skill + command
  purpose:
    Test-first hotfix for a deployed bug: reproduce as a **failing test** (committed as
    proof-of-bug), diagnose on the deployed ref, minimal fix, **cherry-pick both ways** (mainline
    ↔ release branch), all remote ops printed for the user. Deploy mechanics stay per-project.

Remote operations are printed for you to run — with [`git-guard`](../git-guard) enabled they are
blocked for the agent anyway.

## Enable

```bash
claude plugin install hotfix@optimiziramsi --scope project
```
