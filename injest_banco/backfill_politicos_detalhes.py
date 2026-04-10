"""
backfill_deputados_detalhes.py
──────────────────────────────
Preenche os campos de detalhe da tabela `deputados` que não estão disponíveis
no CSV/listagem paginada e precisam ser buscados um a um via:

    GET /deputados/{id}

Campos preenchidos por este script:
  - nomeCivil
  - dataNascimento
  - siglaSexo         (vem como "sexo" na raiz do JSON)
  - escolaridade
  - situacao          (ultimoStatus.situacao)
  - condicaoEleitoral (ultimoStatus.condicaoEleitoral)
  - siglaUF           (ultimoStatus.siglaUf  — atualiza caso tenha mudado)
  - siglaPartido      (ultimoStatus.siglaPartido — idem)
  - urlFoto           (ultimoStatus.urlFoto   — idem)
  - emailGabinete     (ultimoStatus.gabinete.email)
  - telefoneGabinete  (ultimoStatus.gabinete.telefone)

Estratégia de execução:
  - Processa TODOS os deputados por padrão (--force) ou apenas os incompletos
  - Commits em lotes de BATCH_SIZE para não perder progresso em caso de falha
  - Rate limit respeitado via SLEEP_BETWEEN_REQUESTS
  - Retry automático já tratado dentro de camara_get()

Uso:
    # Apenas quem está incompleto (padrão)
    python backfill_deputados_detalhes.py

    # Força atualização de todos (útil após uma legislatura nova)
    python backfill_deputados_detalhes.py --force
"""
import argparse
import logging
import re
import time
import os
from datetime import date
import unicodedata

# 1. Novos imports do SQLAlchemy Core (Substituindo o ORM)
from sqlalchemy import create_engine, Table, MetaData, select, update

# Mantém a importação da sua API
from api_camara import camara_get

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Configuração
# ─────────────────────────────────────────────────────────────────────────────
BATCH_SIZE = 50
SLEEP_BETWEEN_REQUESTS = 0.25

# Usando a mesma lógica de URL do seu etl_camara.py
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/quemvota_teste")

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _parse_date(valor: str | None) -> date | None:
    if not valor:
        return None
    try:
        return date.fromisoformat(valor[:10])
    except ValueError:
        logger.debug("Data inválida ignorada: %s", valor)
        return None

def generate_slug(text):
    if not text: return None
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8').lower()
    text = re.sub(r'[^a-z0-9]+', '-', text).strip('-')
    return text

def _is_incompleto(dep_row: dict) -> bool:
    """Verifica um dicionário de linha do banco, em vez de um objeto ORM."""
    return any([
        not dep_row.get("urlFoto"),
        not dep_row.get("nomeCivil"),
        not dep_row.get("escolaridade"),
        not dep_row.get("situacao"),
        not dep_row.get("emailGabinete"),
        not dep_row.get("slug"), 
        not dep_row.get("cpf")
    ])

# ─────────────────────────────────────────────────────────────────────────────
# Entrypoint e Core Logic
# ─────────────────────────────────────────────────────────────────────────────
def run_backfill(force: bool):
    engine = create_engine(DATABASE_URL)
    metadata = MetaData()
    
    # Reflete a tabela do banco de dados direto
    metadata.reflect(bind=engine, only=['deputados'])
    tabela_deputados = metadata.tables['deputados']
    
    processados = 0
    atualizados = 0
    erros = 0
    sem_dados = 0
    
    # Usando with engine.connect() para gerenciar transações
    with engine.connect() as conn:
        # Busca os deputados existentes no banco
        query = select(tabela_deputados)
        resultados = conn.execute(query).mappings().all()
        
        # Filtra os alvos com base nos argumentos
        alvo = [dep for dep in resultados if force or _is_incompleto(dep)]
        
        logger.info("═" * 60)
        logger.info(f"Iniciando Backfill: {len(alvo)} deputados na fila.")
        
        # Buffer para o update em lotes (batch)
        batch_updates = []
        
        for dep in alvo:
            try:
                # Cuidado para passar a coluna ID correta (verifique se chama 'id' ou 'idCamara' no seu schema)
                dep_id = dep.get("idCamara") or dep.get("id") 
                
                resposta_api = camara_get(f"/deputados/{dep_id}")
                processados += 1
                
                if not resposta_api or "dados" not in resposta_api:
                    sem_dados += 1
                    continue
                    
                dados = resposta_api["dados"]
                status = dados.get("ultimoStatus") or {}
                gabinete = status.get("gabinete") or {}
                
                # Monta o dicionário com os campos para realizar o UPDATE.
                # A chave primária (id) é passada junto, o SQLAlchemy usa ela como critério do WHERE.
                valores_update = {
                    "id": dep["id"],  # Fundamental ter a PK mapeada aqui!
                    "nomeCivil": dados.get("nomeCivil"),
                    "dataNascimento": _parse_date(dados.get("dataNascimento")),
                    "siglaSexo": dados.get("sexo"),
                    "escolaridade": dados.get("escolaridade"),
                    "situacao": status.get("situacao"),
                    "condicaoEleitoral": status.get("condicaoEleitoral"),
                    "siglaUF": status.get("siglaUf"),
                    "siglaPartido": status.get("siglaPartido"),
                    "urlFoto": status.get("urlFoto"),
                    "emailGabinete": gabinete.get("email"),
                    "telefoneGabinete": gabinete.get("telefone"),
                    "cpf": dados.get("cpf"),
                    "slug": generate_slug(dados.get("nomeCivil"))
                }
                
                batch_updates.append(valores_update)
                
                # Descarrega pro banco ao atingir o BATCH_SIZE
                if len(batch_updates) >= BATCH_SIZE:
                    # Executando a transação via Statement 
                    conn.execute(update(tabela_deputados), batch_updates)
                    conn.commit()
                    atualizados += len(batch_updates)
                    batch_updates = []
                
            except Exception as e:
                logger.error(f"Erro ao processar deputado {dep.get('id')}: {e}")
                erros += 1
                
            time.sleep(SLEEP_BETWEEN_REQUESTS)
            
        # Garante que as sobras finais do buffer também sejam commitadas
        if batch_updates:
            conn.execute(update(tabela_deputados), batch_updates)
            conn.commit()
            atualizados += len(batch_updates)

    # Relatório final
    logger.info("═" * 60)
    logger.info("🏁 Backfill concluído")
    logger.info("   Deputados no alvo  : %d", len(alvo))
    logger.info("   Processados        : %d", processados)
    logger.info("   Atualizados        : %d", atualizados)
    logger.info("   Sem dados na API   : %d", sem_dados)
    logger.info("   Erros              : %d", erros)
    logger.info("═" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill dos campos de detalhe.")
    parser.add_argument("--force", action="store_true", default=False, help="Atualiza todos.")
    args = parser.parse_args()
    
    run_backfill(force=args.force)
