#!/bin/bash
# deploy.sh — setup completo da VPS AWS (Ubuntu 22.04 / 24.04)
# Localização: app/deploy/deploy.sh
# Execute com: sudo bash deploy.sh

set -euo pipefail

# ── Verificar root ────────────────────────────────────────────────────────────
if [ "$EUID" -ne 0 ]; then
    echo "❌ Execute com sudo: sudo ./deploy.sh"
    exit 1
fi

DOMAIN="seudomain.com"
EMAIL="seu@email.com"
REPO="https://github.com/seu-usuario/quem-vota.git"
APP_DIR="/opt/quemvota"
DEPLOY_DIR="$APP_DIR/app/deploy"

echo "════════════════════════════════════════════════"
echo "  🚀 Deploy Quem Vota — $(date)"
echo "════════════════════════════════════════════════"

# ── 1. Dependências do sistema ────────────────────────────────────────────────
echo "→ Instalando Docker e utilitários..."
apt-get update -qq
apt-get install -y -qq ca-certificates curl gnupg git ufw fail2ban

# Docker Engine
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    > /etc/apt/sources.list.d/docker.list

apt-get update -qq
apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin

systemctl enable --now docker
echo "✔ Docker instalado: $(docker --version)"

# ── 2. Firewall ───────────────────────────────────────────────────────────────
echo "→ Configurando UFW..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
echo "✔ Firewall ativo"

# ── 3. Clonar / atualizar repositório ────────────────────────────────────────
echo "→ Clonando repositório..."
if [ -d "$APP_DIR" ]; then
    git -C "$APP_DIR" pull
else
    git clone "$REPO" "$APP_DIR"
fi

cd "$DEPLOY_DIR"

# ── 4. Variáveis de ambiente ──────────────────────────────────────────────────
if [ ! -f .env ]; then
    echo "⚠  Arquivo .env não encontrado em $DEPLOY_DIR"
    echo "   cp .env.example .env && nano .env"
    exit 1
fi

# ── 5. Criar pasta conf.d e nginx temporário (HTTP) para Certbot ──────────────
echo "→ Subindo serviços (HTTP primeiro, para Certbot)..."
mkdir -p conf.d

cat > conf.d/quemvota.conf << NGINX_HTTP
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { return 200 'ok'; }
}
NGINX_HTTP

docker compose up -d --build nginx certbot postgres valkey api
sleep 5

# ── 6. Obter certificado SSL ──────────────────────────────────────────────────
echo "→ Solicitando certificado SSL para $DOMAIN..."
docker compose run --rm certbot certonly \
    --webroot -w /var/www/certbot \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN" -d "www.$DOMAIN"

# ── 7. Nginx com HTTPS ────────────────────────────────────────────────────────
echo "→ Aplicando configuração HTTPS..."
cat > conf.d/quemvota.conf << 'NGINX_HTTPS'
server {
    listen 80;
    server_name DOMAIN_PLACEHOLDER www.DOMAIN_PLACEHOLDER;
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { return 301 https://$host$request_uri; }
}

server {
    listen 443 ssl;
    http2 on;
    server_name DOMAIN_PLACEHOLDER www.DOMAIN_PLACEHOLDER;

    ssl_certificate     /etc/letsencrypt/live/DOMAIN_PLACEHOLDER/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/DOMAIN_PLACEHOLDER/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;
    ssl_session_cache   shared:SSL:10m;

    add_header X-Frame-Options        "SAMEORIGIN"   always;
    add_header X-Content-Type-Options "nosniff"      always;
    add_header Referrer-Policy        "strict-origin" always;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/javascript;

    location / {
        proxy_pass         http://frontend:3000;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass         http://api:8000/;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }
}
NGINX_HTTPS

sed -i "s/DOMAIN_PLACEHOLDER/$DOMAIN/g" conf.d/quemvota.conf

docker compose up -d --build --force-recreate nginx frontend
echo "✔ Nginx reiniciado com HTTPS"

# ── 8. Status final ───────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════"
echo "  ✅ Deploy concluído!"
echo "  🌍 https://$DOMAIN"
echo "  📖 https://$DOMAIN/api/docs"
echo "════════════════════════════════════════════════"
docker compose ps