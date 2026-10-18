# rename — move a file and cascade every reference

The `rename@optimiziramsi` plugin, one of the [optimiziramsi marketplace](../README.md)'s per-concern plugins — enable it in the projects that want it.

## Contents

- name: `rename`
  kind: skill + command
  purpose:
    `git mv` a file + update every non-archive reference across the project (the
    "dozen-references-cascade" problem).

## Enable

```bash
claude plugin install rename@optimiziramsi --scope project
```
