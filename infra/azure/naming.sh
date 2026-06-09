#!/usr/bin/env bash
# KuberAIQ Azure resource naming — source from deploy scripts (do not commit secrets).
# shellcheck disable=SC2034

# Resource groups
export KUBERAIQ_RG_DEV="${KUBERAIQ_RG_DEV:-rg-kuberaiq-dev}"
export KUBERAIQ_RG_PROD="${KUBERAIQ_RG_PROD:-rg-kuberaiq-prod}"

# Container images (ACR)
export KUBERAIQ_IMAGE_API="${KUBERAIQ_IMAGE_API:-kuberaiq-api}"
export KUBERAIQ_IMAGE_WEB="${KUBERAIQ_IMAGE_WEB:-kuberaiq-web}"

# Database
export KUBERAIQ_DB_NAME="${KUBERAIQ_DB_NAME:-kuberaiq}"
export KUBERAIQ_DB_ADMIN_LOGIN="${KUBERAIQ_DB_ADMIN_LOGIN:-kuberaiqadmin}"

# App Service hostnames (globally unique; suffix added in Bicep when needed)
export KUBERAIQ_WEB_APP_DEV="${KUBERAIQ_WEB_APP_DEV:-kuberaiq-web-dev}"
export KUBERAIQ_API_APP_DEV="${KUBERAIQ_API_APP_DEV:-kuberaiq-api-dev}"
export KUBERAIQ_WEB_APP_PROD="${KUBERAIQ_WEB_APP_PROD:-kuberaiq-web-prod}"
export KUBERAIQ_API_APP_PROD="${KUBERAIQ_API_APP_PROD:-kuberaiq-api-prod}"

# Public URLs
export KUBERAIQ_PUBLIC_WEB_PROD="${KUBERAIQ_PUBLIC_WEB_PROD:-https://www.kuberaiq.com}"
export KUBERAIQ_PUBLIC_API_PROD="${KUBERAIQ_PUBLIC_API_PROD:-https://api.kuberaiq.com}"
export KUBERAIQ_PUBLIC_APEX_PROD="${KUBERAIQ_PUBLIC_APEX_PROD:-kuberaiq.com}"
export KUBERAIQ_PUBLIC_WEB_DEV="${KUBERAIQ_PUBLIC_WEB_DEV:-https://dev.kuberaiq.com}"
export KUBERAIQ_PUBLIC_API_DEV="${KUBERAIQ_PUBLIC_API_DEV:-https://api-dev.kuberaiq.com}"

# Integrations
export KUBERAIQ_WHATSAPP_VERIFY_TOKEN="${KUBERAIQ_WHATSAPP_VERIFY_TOKEN:-kuberaiq-verify}"

# Legacy resource group (pre-rename; decommission after prod cutover)
export KUBERAIQ_LEGACY_RG_DEV="${KUBERAIQ_LEGACY_RG_DEV:-rg-vyaparai-dev}"
