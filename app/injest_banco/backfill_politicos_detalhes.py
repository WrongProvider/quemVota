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
import time
from datetime import date

from injest_banco.db.database import SessionLocal
from injest_banco.db.models import Deputado
from injest_banco.api_camara import camara_get

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Configuração
# ─────────────────────────────────────────────────────────────────────────────

BATCH_SIZE              = 50    # commits parciais a cada N deputados
SLEEP_BETWEEN_REQUESTS  = 0.25  # segundos entre chamadas à API (rate limit)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _parse_date(valor: str | None) -> date | None:
    """Converte string ISO para date. Aceita 'YYYY-MM-DD' e 'YYYY-MM-DDTHH:MM:SS'."""
    if not valor:
        return None
    try:
        return date.fromisoformat(valor[:10])
    except ValueError:
        logger.debug("Data inválida ignorada: %s", valor)
        return None


def _is_incompleto(dep: Deputado) -> bool:
    """Retorna True se o deputado ainda não tem os campos de detalhe preenchidos."""
    return any([
        not dep.urlFoto,
        not dep.nomeCivil,
        not dep.escolaridade,
        not dep.situacao,
        not dep.emailGabinete,
    ])


def _aplicar_detalhes(dep: Deputado, dados: dict) -> bool:
    """
    Aplica os campos de detalhe retornados pela API no objeto ORM.
    Retorna True se algum campo foi alterado.
    """
    status = dados.get("ultimoStatus") or {}
    gabinete = status.get("gabinete") or {}

    # Mapeamento: campo_modelo → valor_da_api
    updates = {
        "nomeCivil":         dados.get("nomeCivil"),
        "dataNascimento":    _parse_date(dados.get("dataNascimento")),
        "siglaSexo":         dados.get("sexo"),           # API retorna "sexo" na raiz
        "escolaridade":      dados.get("escolaridade"),
        "situacao":          status.get("situacao"),
        "condicaoEleitoral": status.get("condicaoEleitoral"),
        # Campos que também existem na listagem — atualiza caso tenham mudado
        "siglaUF":           status.get("siglaUf"),
        "siglaPartido":      status.get("siglaPartido"),
        "urlFoto":           status.get("urlFoto"),
        # Gabinete
        "emailGabinete":     gabinete.get("email") or status.get("email"),
        "telefoneGabinete":  gabinete.get("telefone"),
    }

    alterado = False
    for campo, valor in updates.items():
        if valor is not None and getattr(dep, campo) != valor:
            setattr(dep, campo, valor)
            alterado = True

    return alterado


# ─────────────────────────────────────────────────────────────────────────────
# Função principal
# ─────────────────────────────────────────────────────────────────────────────

def rodar_backfill(force: bool = False) -> None:
    """
    Percorre todos os deputados (ou apenas os incompletos) e preenche
    os campos de detalhe via GET /deputados/{id_camara}.

    Args:
        force: Se True, processa todos independentemente do estado atual.
    """
    logger.info("🚀 Backfill de detalhes de deputados iniciado  [force=%s]", force)

    with SessionLocal() as db:
        todos = db.query(Deputado).order_by(Deputado.id).all()

        if not force:
            alvo = [d for d in todos if _is_incompleto(d)]
            logger.info(
                "🔍 %d/%d deputados com dados incompletos",
                len(alvo), len(todos),
            )
        else:
            alvo = todos
            logger.info("⚡ Modo --force: atualizando todos os %d deputados", len(alvo))

        if not alvo:
            logger.info("✅ Nada a fazer. Todos os deputados já estão completos.")
            return

        processados = 0
        atualizados = 0
        erros = 0
        sem_dados = 0

        for dep in alvo:
            try:
                resposta = camara_get(f"/deputados/{dep.idCamara}")
                dados = (resposta or {}).get("dados") or {}

                if not dados:
                    logger.warning(
                        "⚠️  Sem dados para deputado idCamara=%s (%s)",
                        dep.idCamara, dep.nome,
                    )
                    sem_dados += 1
                    continue

                houve_alteracao = _aplicar_detalhes(dep, dados)
                if houve_alteracao:
                    atualizados += 1

                processados += 1

                # Commit parcial a cada BATCH_SIZE
                if processados % BATCH_SIZE == 0:
                    db.commit()
                    logger.info(
                        "🔄 Progresso: %d/%d processados, %d atualizados, %d erros",
                        processados, len(alvo), atualizados, erros,
                    )

                time.sleep(SLEEP_BETWEEN_REQUESTS)

            except Exception:
                erros += 1
                db.rollback()
                logger.exception(
                    "❌ Erro ao processar deputado idCamara=%s (%s)",
                    dep.idCamara, dep.nome,
                )
                # Continua para o próximo — não aborta o backfill inteiro

        # Commit final do lote restante
        try:
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("❌ Falha no commit final")

    # ── Relatório ────────────────────────────────────────────────────────────
    logger.info("═" * 60)
    logger.info("🏁 Backfill concluído")
    logger.info("   Deputados no alvo  : %d", len(alvo))
    logger.info("   Processados        : %d", processados)
    logger.info("   Atualizados        : %d", atualizados)
    logger.info("   Sem dados na API   : %d", sem_dados)
    logger.info("   Erros              : %d", erros)
    logger.info("═" * 60)

    if erros > 0:
        logger.warning(
            "⚠️  %d erros ocorreram. Rode novamente sem --force para tentar "
            "apenas os que ainda estão incompletos.",
            erros,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Entrypoint
# ─────────────────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill dos campos de detalhe da tabela deputados.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Atualiza todos os deputados, não só os incompletos.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    rodar_backfill(force=args.force)