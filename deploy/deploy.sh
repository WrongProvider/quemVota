#!/bin/bash
# deploy.sh — Deploy contínuo, chamado pelo GitHub Actions a cada push na main
# Localização: deploy/deploy.sh
# Pré-requisito: setup.sh já foi executado uma vez na VPS

set -euo pipefail

APP_DIR="/opt/quemVota"
DEPLOY_DIR="$APP_DIR/deploy"

echo "════════════════════════════════════════════════"
echo "  🚀 Deploy — $(date)"
echo "════════════════════════════════════════════════"

# ── 1. Atualizar código ───────────────────────────────────────────────────────
echo "→ Atualizando repositório..."
git -C "$APP_DIR" pull origin main
echo "✔ Código atualizado"

# ── 2. Build e restart dos serviços ──────────────────────────────────────────
echo "→ Rebuilding e subindo serviços..."
cd "$DEPLOY_DIR"

# Rebuild apenas das imagens que mudaram, sem derrubar postgres e valkey
docker compose up -d --build --no-deps api frontend nginx

echo "✔ Serviços no ar"

# ── 3. Status final ───────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════"
echo "  ✅ Deploy concluído — $(date)"
echo "════════════════════════════════════════════════"
docker compose ps
