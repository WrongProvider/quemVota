#!/bin/bash

# ==========================================
# 1. CONFIGURAÇÕES GERAIS
# ==========================================
# Nome do container do banco de dados (descubra usando 'docker ps')
CONTAINER_NAME="nome_do_seu_container_db"

DB_USER="seu_usuario_do_banco"
DB_PASSWORD="sua_senha_do_banco"
DB_NAME="nome_do_seu_banco"

# Configurações da Nuvem
S3_BUCKET="s3://nome-do-seu-bucket/backups_diarios/"
ENDPOINT="--endpoint-url https://<ID_DA_SUA_CONTA>.r2.cloudflarestorage.com" # Deixe vazio se for AWS S3 padrão

# Gera o nome do arquivo com a data e hora atual
DATE=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="/tmp/backup_${DB_NAME}_${DATE}.sql.gz"

# ==========================================
# 2. GERAR O DUMP VIA DOCKER E COMPACTAR
# ==========================================
echo "Iniciando backup do banco ${DB_NAME} (Container: ${CONTAINER_NAME}) em ${DATE}..."

# ---> OPÇÃO A: Se você usa PostgreSQL (Descomente a linha abaixo)
# docker exec -e PGPASSWORD="${DB_PASSWORD}" "${CONTAINER_NAME}" pg_dump -U "${DB_USER}" "${DB_NAME}" | gzip > "${BACKUP_FILE}"

# ---> OPÇÃO B: Se você usa MySQL / MariaDB (Descomente a linha abaixo)
# docker exec -e MYSQL_PWD="${DB_PASSWORD}" "${CONTAINER_NAME}" mysqldump -u "${DB_USER}" "${DB_NAME}" | gzip > "${BACKUP_FILE}"

# ==========================================
# 3. ENVIAR PARA A NUVEM E LIMPAR
# ==========================================
echo "Dump gerado localmente em ${BACKUP_FILE}. Enviando para o Cloud Storage..."

# Envia o arquivo para o bucket
aws s3 cp $BACKUP_FILE $S3_BUCKET $ENDPOINT

# Verifica se o envio deu certo antes de deletar o arquivo local
if [ $? -eq 0 ]; then
  echo "Upload concluído com sucesso! Removendo arquivo local..."
  rm $BACKUP_FILE
else
  echo "ERRO: Falha ao enviar o backup para a nuvem."
fi

echo "Processo finalizado!"