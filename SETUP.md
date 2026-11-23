# Setup — accounts, repos, and the run loop

The harness is dependency-free (Python 3.10+ stdlib + the `gh` CLI). What needs
YOUR accounts: a GitHub org, an AWS account (free credits), and signups for the
review tools. Everything else is in this repo.

## 0. One-time

```sh
# GitHub CLI authenticated to the org you'll use for run repos
gh auth login
python3 -m benchmark --help
```

## 1. Make a private working copy of the starter

On GitHub: open `prooflinedev/ai-review-benchmarks` → **Use this template →
Create a new repository → Private**. Clone it. Drop this `benchmark/` package and
the four docs (EXPERIMENT_PROTOCOL.md, SETUP.md, REPORT_TEMPLATE.md, PLAN.md) into
the repo root. Your harness + report live here; this is also what you submit.

## 2. Initialize and freeze the key

```sh
python3 -m benchmark init
python3 -m benchmark seed-providers      # VERIFY bot logins in step 4
```

Inspect each case (`git apply -p0 cases/NN/change.patch` on a branch off the same
baseline; read `cases/NN/body.md` and, for 04-06, `evidence.md`). Decide the
correct verdict for each (case, condition) and freeze it BEFORE any review:

```sh
python3 -m benchmark freeze-key 01 code_only safe    --expected "..."
python3 -m benchmark freeze-key 03 code_only defect  --expected "drops final partial batch"
python3 -m benchmark freeze-key 04 code_only depends --expected "needs deploy info to judge"
python3 -m benchmark freeze-key 04 with_snapshot defect --expected "snapshot shows column still read by site B"
# ...all 11 (case x condition) cells
```

Verdicts: `safe` (change is correct), `defect` (has a real bug), `depends`
(correct answer is "needs deployment info").

## 3. Create one private run repo per provider, push app-only branches

Reviewers must not see each other or your key, so each provider gets its own repo
containing only the app branches.

```sh
# from the starter, you have refs pilot/base and pilot/01..08 (app-only)
for prov in proofline coderabbit greptile; do
  gh repo create "$GH_ORG/bench-run-$prov" --private -d "benchmark run repo: $prov"
  git push "git@github.com:$GH_ORG/bench-run-$prov.git" \
      refs/remotes/origin/pilot/base:refs/heads/pilot/base \
      $(for n in 01 02 03 04 05 06 07 08; do echo refs/remotes/origin/pilot/$n:refs/heads/pilot/$n; done)
done
```

## 4. Install each reviewer on its run repo and VERIFY the bot login

Install the GitHub app (Proofline, CodeRabbit, Greptile, …) on `bench-run-<prov>`
only. Open one throwaway PR, see which account posts the review, and set the real
login:

```sh
python3 -m benchmark add-provider coderabbit github_bot --bot-login coderabbitai[bot] --notes "free trial"
```

Free-tier notes: confirm each offer covers **private** PRs, note expiry and any
auto-billing, and stop at the free limit. Record any limit you hit (it goes in the
report so the next person can plan). Aim for $0.

## 5. Run a case against a provider

Open the PR (base = `pilot/base`, head = `pilot/NN`) in that provider's repo, then
record it and capture the first review:

```sh
PR=$(gh pr create --repo "$GH_ORG/bench-run-coderabbit" --base pilot/base --head pilot/03 \
       --title "Batch queued deliveries" --body "case 03" | tail -c 9 | tr -dc 0-9)
python3 -m benchmark open-pr coderabbit 03 code_only --repo "$GH_ORG/bench-run-coderabbit" --pr "$PR"
# wait for the bot to review, then:
python3 -m benchmark capture coderabbit-03-code_only-1
```

If a provider has no bot (web-only), capture by paste:
`python3 -m benchmark capture <run_id> --from-file review.txt --url <permalink>`.
If it refused on quota or errored:
`python3 -m benchmark set-outcome <run_id> quota_stop`.

## 6. Split reviews into findings, then grade blind

```sh
python3 -m benchmark add-finding coderabbit-03-code_only-1 "final partial batch never delivered" --locator reports.py
python3 -m benchmark grade-export to_grade.json     # provider hidden
# edit to_grade.json: set bucket + reason on each
python3 -m benchmark grade-import to_grade.json --grader jitendar
```

## 7. Cloud evidence trace (one case)

Deploy one known revision, invoke it, verify the report + receipt, save the
workflow link + evidence, tear it down. Two options:

- GCP Cloud Run (use this if you have GCP credits): see `gcp/GCP_SETUP.md`.
  Local test first: `python3 gcp/deploy.py smoke --docker`. Then
  `deploy` / `verify` / `delete`, or run `.github/workflows/gcp.yml` from Actions.
  The Cloud Run service imports the SAME `reports.py` and returns the same
  evidence shape the AWS Lambda does, so the trace is equivalent.
- AWS (the shipped path): `aws/` + `.github/workflows/aws.yml`, following
  `docs/aws.md`. New AWS accounts get $100 credit, so it is also $0.

In the report, say which you used and why. If you use GCP, state that the AWS
path ships unchanged and you reproduced the trace on Cloud Run with your credits.

## 8. Build the report

```sh
python3 -m benchmark coverage
python3 -m benchmark report --out RESULTS.md
```

Then fill the "Spotlight result" and narrative sections using REPORT_TEMPLATE.md.

## 9. Submit

Open a PR in your private working repo with the harness code, rerun instructions,
the coverage table, and the report. Give the hiring team read access. Record the
2-minute narrated walkthrough. Email **intern-applicants@proofline.sh**, subject
"Software Engineering Intern", with the PR + video links, a short intro, your
location (Noida, India), and availability for a 3–6 month full-time internship.
