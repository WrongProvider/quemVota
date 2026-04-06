# Deploy — Quem Vota na AWS (VPS)

## Estrutura de arquivos

```
quem-vota/
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── ...código Python...
├── frontend/
│   ├── Dockerfile
│   ├── nginx-spa.conf
│   └── ...código React...
├── nginx/
│   └── conf.d/
│       └── quemvota.conf
├── docker-compose.yml
├── .env.example
└── deploy.sh
```

## Pré-requisitos na AWS

1. **EC2** Ubuntu 22.04/24.04, tipo `t3.small` ou maior
2. **Security Group** liberando portas **22, 80 e 443**
3. **Elastic IP** associado à instância (IP fixo)
4. **DNS** com registros A apontando para o Elastic IP:
   - `quemvota.com.br → <Elastic IP>`
   - `www.quemvota.com.br → <Elastic IP>`

## Passo a passo

```bash
# 1. Acesse a VPS
ssh -i sua-chave.pem ubuntu@<ip-da-vps>

# 2. Vire root (ou use sudo em cada comando)
sudo -i

# 3. Edite deploy.sh com seu domínio, e-mail e URL do repo
nano deploy.sh

# 4. Dê permissão e execute
chmod +x deploy.sh
./deploy.sh
```

O script:
- Instala Docker automaticamente
- Configura UFW (firewall)
- Faz o build de todos os containers
- Obtém e renova SSL via Let's Encrypt / Certbot

## Variáveis de ambiente (.env)

```bash
cp .env.example .env
nano .env   # preencha as senhas antes de rodar deploy.sh
```

Gere uma SECRET_KEY segura com:
```bash
openssl rand -hex 32
```

## Comandos úteis pós-deploy

```bash
# Ver logs de todos os serviços
docker compose logs -f

# Ver logs de um serviço específico
docker compose logs -f api

# Reiniciar um serviço
docker compose restart api

# Fazer update da aplicação
git pull && docker compose up -d --build api frontend

# Backup do banco
docker compose exec postgres pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup.sql
```

## Atualizar a aplicação (CI manual)

```bash
cd /opt/quemvota
git pull
docker compose up -d --build api frontend
docker compose restart nginx
```

## Observações importantes

- O `main.py` atual conecta ao Valkey em `redis://localhost:6379`.
  **Você deve alterar para `redis://valkey:6379`** (nome do serviço no Docker).
- O `DATABASE_URL` deve ser injetado via variável de ambiente e lido no `politico_repository.py`.
- Certbot renova o certificado automaticamente a cada 12h via container dedicado.
