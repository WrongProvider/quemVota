#!/bin/bash
set -e

echo "=========================================================="
echo " INICIANDO PIPELINE DE INGESTÃO EM BULK PARA PROD "
echo "=========================================================="

export PYTHONPATH=$(pwd)
export HSA_OVERRIDE_GFX_VERSION=10.3.0
export PYTORCH_HIP_ALLOC_CONF=expandable_segments:True

# 1. Atualizar schema
#echo ">>> [1/11] Atualizando schema do banco (Alembic)..."
.venv/bin/alembic -c backend/alembic.ini upgrade head

# 2. Carga Histórica Completa (ETL)
#echo ">>> [2/11] Executando ETL com carga histórica completa..."
#.venv/bin/python -m injest_banco.etl_camara --full --workers 8

# 3. Backfill de Deputados
#echo ">>> [3/11] Executando Backfill de Deputados via API REST..."
#.venv/bin/python injest_banco/etl_camara.py --backfill-deputados --backfill-force --backfill-workers 8

# 4. Backfill de Proposições
#echo ">>> [4/11] Executando Backfill de Proposições faltantes..."
#.venv/bin/python injest_banco/backfill_proposicoes.py

# 5. Reconciliação de Votações Órfãs
#echo ">>> [5/11] Executando reconciliação de votações órfãs..."
#.venv/bin/python injest_banco/etl_camara.py --reconcile-orfas

# 6. Ingestão de Fotos e Upscaling
#echo ">>> [6/11] Baixando fotos e executando upscaling de IA..."
#.venv/bin/python injest_banco/injest_fotos.py

# 7. Sincronização do Grafo AGE
#echo ">>> [7/11] Sincronizando dados para o grafo Apache AGE (Todas Legislaturas)..."
#.venv/bin/python tasks/sync_graph.py --todas-legislaturas

# 8. Geração de Embeddings
echo ">>> [8/11] Gerando Embeddings (Pré-2026 e Legislatura 57)..."
.venv/bin/python embeddings/gerar_embeddings.py --pre-2026 --batch-size 4
.venv/bin/python embeddings/gerar_embeddings.py --legislatura 57 --batch-size 4

# 9. Seed de Temas de Atuação
echo ">>> [9/11] Executando seed da taxonomia de temas de atuação..."
.venv/bin/python tasks/seed_temas_atuacao.py

# 10. Classificação de Temas
echo ">>> [10/11] Classificando perfil temático (Legislaturas 57 56 55)..."
.venv/bin/python tasks/classificar_temas.py --legislaturas 57 56 55

# 11. Dump do banco
echo ">>> [11/11] Gerando dump completo do banco (schema e dados)..."
DUMP_FILE="dump_prod_$(date +%Y%m%d_%H%M%S).sql.gz"
echo "Gerando dump e comprimindo..."
docker exec quemvota_postgres pg_dump -U caneta_azul -d quemvota -F p | gzip > $DUMP_FILE

echo "=========================================================="
echo " BULK INGESTION FINALIZADO COM SUCESSO! "
echo " Arquivo de dump salvo na raiz: ./$DUMP_FILE "
echo "=========================================================="
