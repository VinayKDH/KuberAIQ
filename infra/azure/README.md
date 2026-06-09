# KuberAIQ Azure environments

Central naming lives in [`naming.sh`](./naming.sh). Deploy scripts source it for resource groups, app names, and public URLs.

## Resource groups

| Environment | Resource group | Azure default hostnames | Custom domains |
| --- | --- | --- | --- |
| **Development** | `rg-kuberaiq-dev` | `kuberaiq-web-dev`, `kuberaiq-api-dev` | `dev.kuberaiq.com`, `api-dev.kuberaiq.com` |
| **Production** | `rg-kuberaiq-prod` | `kuberaiq-web-prod`, `kuberaiq-api-prod` | `www.kuberaiq.com`, `api.kuberaiq.com` |

Legacy dev resources from the pre-rename stack remain in `rg-vyaparai-dev` until data is migrated and the old RG is decommissioned.

## Public URLs

| Environment | Web | API |
| --- | --- | --- |
| Dev | https://dev.kuberaiq.com | https://api-dev.kuberaiq.com |
| Prod | https://www.kuberaiq.com | https://api.kuberaiq.com |

## Common workflows

```bash
# Provision infrastructure (Bicep + first image build)
./scripts/deploy-dev.sh          # dev RG
./scripts/provision-prod.sh      # prod RG

# App deploy with secrets (.env.dev / .env.prod)
ENV_FILE=.env.dev ./scripts/deploy-prod.sh    # reuse deploy-prod for app settings + images
ENV_FILE=.env.prod ./scripts/deploy-prod.sh

# Custom domains + managed SSL (after DNS CNAMEs)
./scripts/setup-kuberaiq-dev-domains.sh
ENV_FILE=.env.prod ./scripts/setup-kuberaiq-domains.sh
```

IaC template: [`../bicep/main.bicep`](../bicep/main.bicep). Compiled ARM JSON: [`../bicep/main.json`](../bicep/main.json).
