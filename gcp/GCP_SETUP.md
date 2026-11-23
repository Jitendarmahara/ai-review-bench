# GCP Cloud Run evidence trace (alternative to AWS)

The starter ships an AWS Lambda trace (`aws/`). This `gcp/` path reproduces the
**same evidence chain** on Google Cloud Run — build the checked-out commit, deploy,
invoke, verify the returned report + receipt, tear down — for when you have GCP
credits instead of AWS. The AWS path is untouched; this is additive.

In the report, state plainly: "I reproduced the starter's deploy→verify→receipt
trace on Cloud Run because I had GCP credits. The AWS path ships unchanged." That
is honest and shows systems range. If you can open an AWS account, the AWS free
tier ($100 new-account credit) runs the shipped path at $0 too — your call.

## What's here

- `gcp/main.py` — Cloud Run entrypoint. Imports the SAME `reports.py` under test
  and returns the same shape the Lambda does: `commit`, `request_id`, `report`,
  `delivered_this_run`, `receipt_at`, `summary`. Dependency-free (stdlib HTTP server).
- `gcp/Dockerfile` — python:3.12-slim (matches the Lambda runtime), non-root.
- `gcp/cloudbuild.yaml` — builds the image from `gcp/Dockerfile` with the repo
  root as context so `reports.py` + `migrations/` are included.
- `gcp/deploy.py` — `package | smoke | deploy | verify | delete` (mirrors
  `aws/deploy.py`).
- `gcp/gcp.yml` — copy to `.github/workflows/gcp.yml`; keyless (Workload Identity
  Federation) deploy/verify/delete, mirrors `aws.yml`.

## Local test (no GCP needed)

```sh
python3 gcp/deploy.py package           # inputs present?
python3 gcp/deploy.py smoke             # runs the experiment in-process, asserts the report
python3 gcp/deploy.py smoke --docker    # builds the image, hits the container, asserts
```

## One-time GCP setup

```sh
gcloud auth login
gcloud config set project YOUR_PROJECT
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
gcloud artifacts repositories create bench --repository-format=docker --location=us-central1
```

## Deploy, verify, tear down

```sh
python3 gcp/deploy.py deploy  --project YOUR_PROJECT --region us-central1 --repo bench --service ai-review-bench
python3 gcp/deploy.py verify  --project YOUR_PROJECT --region us-central1 --service ai-review-bench
# ... save the printed commit + request_id + receipt_at, and the Cloud Run revision URL, as your evidence ...
python3 gcp/deploy.py delete  --project YOUR_PROJECT --region us-central1 --service ai-review-bench
```

`verify` calls the service with an identity token (the service is deployed
`--no-allow-unauthenticated`), checks the deployed commit comes back with a
receipt, and prints the evidence to capture in the report.

## Keyless CI (recommended)

Set up Workload Identity Federation between GitHub and GCP, grant the deployer
service account `run.admin`, `cloudbuild.builds.editor`, `artifactregistry.writer`,
and `iam.serviceAccountUser`. Put `GCP_PROJECT`, `GCP_REGION`, `GCP_WIF_PROVIDER`,
`GCP_SERVICE_ACCOUNT`, `AR_REPO` in repo Variables, copy `gcp/gcp.yml` to
`.github/workflows/`, and run it from the Actions tab (deploy / verify / delete).

## Cost control ($0)

Cloud Run scales to zero and the free tier covers this tiny workload. Delete the
service after capturing the receipt. Delete the Artifact Registry image if you
want zero storage. Check your credit balance before and after.
