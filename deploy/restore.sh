#!/bin/bash

# ==========================================
# 1. CONFIGURAÇÕES
# ==========================================
CONTAINER_NAME="nome_do_seu_container_db"
DB_USER="seu_usuario_do_banco"
DB_PASSWORD="sua_senha_do_banco"
DB_NAME="nome_do_seu_banco"

# Onde o backup está na nuvem (Exemplo: backup_nome_2026-03-03.sql.gz)
S3_PATH="s3://nome-do-seu-bucket/backups_diarios/NOME_DO_ARQUIVO.sql.gz"
ENDPOINT="--endpoint-url https://<ID_DA_SUA_CONTA>.r2.cloudflarestorage.com"

LOCAL_FILE="/tmp/restore_backup.sql.gz"

# ==========================================
# 2. DOWNLOAD E RESTORE
# ==========================================
echo "📥 Baixando backup da nuvem..."
aws s3 cp $S3_PATH $LOCAL_FILE $ENDPOINT

if [ $? -ne 0 ]; then
    echo "❌ Erro ao baixar o arquivo. Verifique o caminho no S3."
    exit 1
fi

echo "🔄 Restaurando banco de dados (isso pode demorar...)"

# O comando 'zcat' lê o arquivo compactado e o pipe '|' joga o texto pro Docker
# ---> OPÇÃO A: Se for PostgreSQL
# zcat $LOCAL_FILE | docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME

# ---> OPÇÃO B: Se for MySQL / MariaDB
# zcat $LOCAL_FILE | docker exec -i $CONTAINER_NAME mysql -u $DB_USER -p"$DB_PASSWORD" $DB_NAME

if [ $? -eq 0 ]; then
    echo "✅ Restauração concluída com sucesso!"
    rm $LOCAL_FILE
else
    echo "❌ Erro durante a restauração."
fi