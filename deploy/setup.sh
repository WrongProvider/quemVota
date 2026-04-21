#!/bin/bash
# setup.sh — Provisionamento inicial da VPS (roda UMA vez)
# Localização: deploy/setup.sh
# Execute com: sudo bash setup.sh

set -euo pipefail

# ── Verificar root ────────────────────────────────────────────────────────────
if [ "$EUID" -ne 0 ]; then
    echo "❌ Execute com sudo: sudo ./setup.sh"
    exit 1
fi

DOMAIN="quemvota.com.br"
EMAIL="seu@email.com"
REPO="https://github.com/seu-usuario/quemVota.git"
APP_DIR="/opt/quemVota"
DEPLOY_DIR="$APP_DIR/deploy"
UBUNTU_USER="${SUDO_USER:-ubuntu}"

echo "════════════════════════════════════════════════"
echo "  🔧 Setup inicial — $(date)"
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

# Permite que o usuário ubuntu rode docker sem sudo
usermod -aG docker "$UBUNTU_USER"
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

# ── 3. Clonar repositório ─────────────────────────────────────────────────────
echo "→ Clonando repositório..."
if [ -d "$APP_DIR" ]; then
    echo "   Repositório já existe em $APP_DIR — pulando clone"
else
    git clone "$REPO" "$APP_DIR"
    chown -R "$UBUNTU_USER:$UBUNTU_USER" "$APP_DIR"
fi

cd "$DEPLOY_DIR"

# ── 4. Verificar .env ─────────────────────────────────────────────────────────
if [ ! -f .env ]; then
    echo "⚠  Arquivo .env não encontrado em $DEPLOY_DIR"
    echo "   Crie o arquivo antes de continuar:"
    echo "   cp .env.example .env && nano .env"
    exit 1
fi

# ── 5. Subir banco e cache ────────────────────────────────────────────────────
echo "→ Subindo postgres e valkey..."
docker compose up -d postgres valkey
echo "→ Aguardando healthchecks..."
sleep 15

# ── 6. Certificado SSL ────────────────────────────────────────────────────────
echo "→ Solicitando certificado SSL para $DOMAIN..."
mkdir -p certbot_certs certbot_www

docker run --rm \
    -p 80:80 \
    -v "$DEPLOY_DIR/certbot_certs:/etc/letsencrypt" \
    -v "$DEPLOY_DIR/certbot_www:/var/www/certbot" \
    certbot/certbot certonly \
    --standalone \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --force-renewal \
    -d "$DOMAIN" -d "www.$DOMAIN"

echo "✔ Certificado obtido!"

# ── 7. Configuração Nginx ─────────────────────────────────────────────────────
echo "→ Aplicando configuração Nginx..."
mkdir -p conf.d

cat > conf.d/quemvota.conf << 'NGINX_CONF'
server {
    listen 80;
    server_name DOMAIN_PLACEHOLDER www.DOMAIN_PLACEHOLDER;
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
NGINX_CONF

sed -i "s/DOMAIN_PLACEHOLDER/$DOMAIN/g" conf.d/quemvota.conf
echo "✔ Nginx configurado"

# ── 8. Crons ──────────────────────────────────────────────────────────────────
echo "→ Configurando crons..."

# Renovação do certificado SSL (todo dia às 2h)
SSL_CRON="0 2 * * * docker run --rm -p 80:80 \
  -v $DEPLOY_DIR/certbot_certs:/etc/letsencrypt \
  -v $DEPLOY_DIR/certbot_www:/var/www/certbot \
  certbot/certbot renew --standalone --quiet \
  && docker compose -f $DEPLOY_DIR/docker-compose.yml restart nginx"

# ETL de ingestão (todo dia às 3h)
INGEST_CRON="0 3 * * * cd $DEPLOY_DIR && docker compose --profile ingest run --rm ingest >> /var/log/quemvota-ingest.log 2>&1"

(crontab -l 2>/dev/null | grep -v "certbot\|quemvota-ingest"; \
  echo "$SSL_CRON"; \
  echo "$INGEST_CRON") | crontab -

echo "✔ Crons configurados (SSL às 2h, ingest às 3h)"

# ── 9. Primeiro deploy ────────────────────────────────────────────────────────
echo "→ Subindo todos os serviços..."
docker compose up -d --build

echo ""
echo "════════════════════════════════════════════════"
echo "  ✅ Setup concluído!"
echo "  🌍 https://$DOMAIN"
echo "  📖 https://$DOMAIN/api/docs"
echo ""
echo "  ⚠️  Faça logout e login novamente para usar"
echo "     docker sem sudo (grupo docker aplicado)"
echo "════════════════════════════════════════════════"
docker compose ps#!/bin/bash
# setup.sh — Provisionamento inicial da VPS (roda UMA vez)
# Localização: deploy/setup.sh
# Execute com: sudo bash setup.sh

set -euo pipefail

# ── Verificar root ────────────────────────────────────────────────────────────
if [ "$EUID" -ne 0 ]; then
    echo "❌ Execute com sudo: sudo ./setup.sh"
    exit 1
fi

DOMAIN="quemvota.com.br"
EMAIL="seu@email.com"
REPO="https://github.com/seu-usuario/quemVota.git"
APP_DIR="/opt/quemVota"
DEPLOY_DIR="$APP_DIR/deploy"
UBUNTU_USER="${SUDO_USER:-ubuntu}"

echo "════════════════════════════════════════════════"
echo "  🔧 Setup inicial — $(date)"
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

# Permite que o usuário ubuntu rode docker sem sudo
usermod -aG docker "$UBUNTU_USER"
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

# ── 3. Clonar repositório ─────────────────────────────────────────────────────
echo "→ Clonando repositório..."
if [ -d "$APP_DIR" ]; then
    echo "   Repositório já existe em $APP_DIR — pulando clone"
else
    git clone "$REPO" "$APP_DIR"
    chown -R "$UBUNTU_USER:$UBUNTU_USER" "$APP_DIR"
fi

cd "$DEPLOY_DIR"

# ── 4. Verificar .env ─────────────────────────────────────────────────────────
if [ ! -f .env ]; then
    echo "⚠  Arquivo .env não encontrado em $DEPLOY_DIR"
    echo "   Crie o arquivo antes de continuar:"
    echo "   cp .env.example .env && nano .env"
    exit 1
fi

# ── 5. Subir banco e cache ────────────────────────────────────────────────────
echo "→ Subindo postgres e valkey..."
docker compose up -d postgres valkey
echo "→ Aguardando healthchecks..."
sleep 15

# ── 6. Certificado SSL ────────────────────────────────────────────────────────
echo "→ Solicitando certificado SSL para $DOMAIN..."
mkdir -p certbot_certs certbot_www

docker run --rm \
    -p 80:80 \
    -v "$DEPLOY_DIR/certbot_certs:/etc/letsencrypt" \
    -v "$DEPLOY_DIR/certbot_www:/var/www/certbot" \
    certbot/certbot certonly \
    --standalone \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --force-renewal \
    -d "$DOMAIN" -d "www.$DOMAIN"

echo "✔ Certificado obtido!"

# ── 7. Configuração Nginx ─────────────────────────────────────────────────────
echo "→ Aplicando configuração Nginx..."
mkdir -p conf.d

cat > conf.d/quemvota.conf << 'NGINX_CONF'
server {
    listen 80;
    server_name DOMAIN_PLACEHOLDER www.DOMAIN_PLACEHOLDER;
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
NGINX_CONF

sed -i "s/DOMAIN_PLACEHOLDER/$DOMAIN/g" conf.d/quemvota.conf
echo "✔ Nginx configurado"

# ── 8. Crons ──────────────────────────────────────────────────────────────────
echo "→ Configurando crons..."

# Renovação do certificado SSL (todo dia às 2h)
SSL_CRON="0 2 * * * docker run --rm -p 80:80 \
  -v $DEPLOY_DIR/certbot_certs:/etc/letsencrypt \
  -v $DEPLOY_DIR/certbot_www:/var/www/certbot \
  certbot/certbot renew --standalone --quiet \
  && docker compose -f $DEPLOY_DIR/docker-compose.yml restart nginx"

# ETL de ingestão (todo dia às 3h)
INGEST_CRON="0 3 * * * cd $DEPLOY_DIR && docker compose --profile ingest run --rm ingest >> /var/log/quemvota-ingest.log 2>&1"

(crontab -l 2>/dev/null | grep -v "certbot\|quemvota-ingest"; \
  echo "$SSL_CRON"; \
  echo "$INGEST_CRON") | crontab -

echo "✔ Crons configurados (SSL às 2h, ingest às 3h)"

# ── 9. Primeiro deploy ────────────────────────────────────────────────────────
echo "→ Subindo todos os serviços..."
docker compose up -d --build

echo ""
echo "════════════════════════════════════════════════"
echo "  ✅ Setup concluído!"
echo "  🌍 https://$DOMAIN"
echo "  📖 https://$DOMAIN/api/docs"
echo ""
echo "  ⚠️  Faça logout e login novamente para usar"
echo "     docker sem sudo (grupo docker aplicado)"
echo "════════════════════════════════════════════════"
docker compose ps
