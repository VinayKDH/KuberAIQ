# GCP Cloud Run custom domains (kuberaiq.com)

Map **www.kuberaiq.com** and **api.kuberaiq.com** to KuberAIQ on GCP Cloud Run (`asia-south1`).

| Service | Cloud Run name | Custom domain |
|---------|----------------|---------------|
| Web (Next.js) | `kuberaiq-web-gcp` | `www.kuberaiq.com` |
| API (FastAPI) | `kuberaiq-api-gcp` | `api.kuberaiq.com` |

Use GCP account **testkuberqi@gmail.com** (`gcloud config set account testkuberqi@gmail.com`).

## Current status checklist

1. **DNS** — Hostinger CNAMEs still point to disabled Azure App Services (`kuberaiq-*-prod.azurewebsites.net`). Update to `ghs.googlehosted.com`.
2. **Domain verification** — `kuberaiq.com` must be verified in Google Search Console for the GCP account before mappings can be created.
3. **Cloud Run mappings** — None created until verification completes (`gcloud beta run domain-mappings list`).
4. **Cloud Run URLs** — Work today without custom DNS:
   - Web: `https://kuberaiq-web-gcp-zu3hk22ncq-el.a.run.app`
   - API: `https://kuberaiq-api-gcp-zu3hk22ncq-el.a.run.app`

## Step 1 — Verify domain in GCP

```bash
gcloud config set account testkuberqi@gmail.com
gcloud config set project bharatfreight-os-prod
gcloud domains verify kuberaiq.com --project=bharatfreight-os-prod
```

Or open [Google Search Console](https://search.google.com/search-console/welcome?new_domain_name=kuberaiq.com) as **testkuberqi@gmail.com**, add domain property `kuberaiq.com`, choose **DNS TXT** verification, and add the record in Hostinger.

Confirm:

```bash
gcloud domains list-user-verified --project=bharatfreight-os-prod
# must include: kuberaiq.com
```

## Step 2 — Hostinger DNS records

**DNS Zone** (Hostinger → Domains → kuberaiq.com → DNS):

| Action | Type | Name | Value | Notes |
|--------|------|------|-------|-------|
| **Change** | CNAME | `www` | `ghs.googlehosted.com` | Was `kuberaiq-web-prod.azurewebsites.net` |
| **Change** | CNAME | `api` | `ghs.googlehosted.com` | Was `kuberaiq-api-prod.azurewebsites.net` |
| **Add** (if Search Console asks) | TXT | `@` | `google-site-verification=...` | One-time domain verification |
| **Delete** (if present) | TXT | `asuid.www` | *(any)* | Old Azure SSL verification |
| **Delete** (if present) | TXT | `asuid.api` | *(any)* | Old Azure SSL verification |
| **Keep** | TXT | `@` | `v=spf1 include:_spf.mail.hostinger.com ~all` | Mail — do not remove |

**Redirects** (Hostinger → Redirects):

| From | To | Type |
|------|-----|------|
| `kuberaiq.com` | `https://www.kuberaiq.com` | 301 permanent |

Print a copy anytime:

```bash
./scripts/setup-gcp-domains.sh --dns-only
```

## Step 3 — Create Cloud Run domain mappings

After verification + DNS update:

```bash
ENV_FILE=.env.gcp ./scripts/setup-gcp-domains.sh
```

Check status:

```bash
gcloud beta run domain-mappings list --region=asia-south1 --project=bharatfreight-os-prod
gcloud beta run domain-mappings describe www.kuberaiq.com --region=asia-south1 --project=bharatfreight-os-prod
```

Google provisions managed TLS once DNS resolves to `ghs.googlehosted.com` (typically 15–60 minutes).

## Step 4 — Verify DNS and HTTPS

```bash
./scripts/check-kuberaiq-dns-gcp.sh
curl -sI https://www.kuberaiq.com | head -5
curl -s https://api.kuberaiq.com/health
```

Expect `x-cloud-trace-context` or Cloud Run headers (not `ARRAffinity` Azure cookies).

## Step 5 — OAuth and redeploy

`.env.gcp` should include:

```bash
PUBLIC_WEB_URL=https://www.kuberaiq.com
PUBLIC_API_URL=https://api.kuberaiq.com
GOOGLE_REDIRECT_URI=https://www.kuberaiq.com/auth/callback
NEXT_PUBLIC_OAUTH_COOKIE_DOMAIN=.kuberaiq.com
```

In [Google Cloud Console → APIs & Credentials → OAuth client](https://console.cloud.google.com/apis/credentials), add **Authorized redirect URI**:

- `https://www.kuberaiq.com/auth/callback`

Redeploy so the web image bakes in the canonical URL:

```bash
ENV_FILE=.env.gcp ./scripts/deploy-gcp.sh
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `403 Site Disabled` | DNS still on Azure | Change CNAMEs to `ghs.googlehosted.com` |
| `domain does not appear to be verified` | Search Console step skipped | Verify `kuberaiq.com` (Step 1) |
| SSL pending / certificate error | DNS not propagated | Wait; re-run check script |
| OAuth redirect mismatch | Console missing URI | Add callback URL (Step 5) |
