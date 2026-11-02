# The marketplace ships the system — a project's commands live in the project, never in a skill

A plugin skill states the **protocol** and **points** at a project-owned rules file for everything
concrete. It never carries one project's commands, flags, tool names, state files or stack — not
"as an example", and not when a spec handed over by a consuming project asks for it.

## What bit us (2026-11-02)

A consuming project asked for its local-env hub model in the `worktree` and `relay` skills; its
paste-ready spec said to let the project's commands "stand as the example". The first draft followed
it: the skill taught that project's hub CLI (subcommands, flags, a state file, hostnames, stack
tools). The user's correction: the marketplace is repo/project-agnostic by itself — it provides the
system and infra for skills and dev tools, and anything repo-specific lives in the repo. The rework
kept only the protocol side (register instead of reserve, heavy work through the hub, the hub queue is
the cap, end of life) and deferred every command to the repo's own `.agent/hub/README.md`.

## The rule

- Concrete commands, flags, file names and stack/product terms of one project belong in **that
  project's** file (`.agent/<topic>/README.md`, or the file its CLAUDE.md names). The skill refers
  to it by path.
- A skill may name the general kind of repo support ("a local-env hub") and say "follow the rules
  the repo sets in `.agent/hub/README.md`"; it fixes only what the protocol itself needs from it.
- A delegating spec ("use my commands as the example") does not waive this. Apply its intent, strip
  the specifics, and tell the project what to put in its own file.
- Before the commit, grep the shipped files for the delegating spec's own vocabulary (tool names,
  flags, hostnames) — if the spec's words appear, they leaked.
