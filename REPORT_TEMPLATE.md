# AI Review Benchmark — report

> `python3 -m benchmark report --out RESULTS.md` generates the coverage table and
> the scored-findings counts. This template is the narrative wrapper around it.
> Keep it short and evidence-first.

## What I measured
One attempt = (provider, case, condition, base/head, run_id). I ran <N> reviewers
over the 8 cases in two conditions (code_only; with_snapshot for 04–06), captured
each reviewer's first review verbatim, and graded every finding blind against a
key I froze before any run. Full rules: EXPERIMENT_PROTOCOL.md.

## How to reproduce
```sh
python3 -m benchmark init && python3 -m benchmark seed-providers
# freeze-key for all 11 cells (see commit <sha> for the exact commands)
# per provider: create run repo, push pilot/* , install app, open PRs
python3 -m benchmark capture <run_id>        # or --from-file for web-only tools
python3 -m benchmark grade-export to_grade.json && grade-import to_grade.json
python3 -m benchmark report --out RESULTS.md
```

## Coverage
<paste `python3 -m benchmark coverage` output, or link RESULTS.md>

Denominators are raw counts. Cells I could not run (quota/error/unattempted) are
shown, not hidden.

## Scored findings
<paste the scored-findings table from RESULTS.md>

## Spotlight result (one result, end to end)
- Case / condition: <e.g. 03 / code_only>
- Commit reviewed: <base_sha> → <head_sha> (<PR link>)
- Reviewer's original comment (verbatim): "<...>"  (<permalink>)
- What I verified: <how I established the real behavior — ran the app / read the
  diff / deployed and observed>
- Score I assigned: <bucket> because <reason tied to the frozen key>
- One limitation that could change this: <...>

## AWS evidence trace
- Case deployed: <NN>; workflow run: <link>; delivered report / receipt: <link>.
- Facts from the live deploy: <...>. Facts from the supplied snapshot: <...>.

## Familiarity probe
Held-out original change: <what it was>. Result: <did providers still review the
diff, or lean on memorized public cases?>.

## What I'd do with more time
<1–2 lines: more providers, repeat runs for variance, a second application.>

## Caveat
Eight related changes in one app give limited evidence about performance
elsewhere. This measures these reviewers on these changes, nothing broader.
