import requests
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configurações de conexão (ajuste com seus dados)
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/quemvota_teste"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

def backfill_proposicoes():
    print("🔍 Identificando IDs de proposições faltantes...")
    
    # 1. Busca IDs no idCamara das votações que não existem em proposicoes
    query_missing = text("""
        SELECT DISTINCT split_part("idCamara", '-', 1) as id_externo
        FROM public.votacoes v
        WHERE v."idProposicao" IS NULL
          AND NOT EXISTS (
              SELECT 1 FROM public.proposicoes p 
              WHERE p.id = CAST(split_part(v."idCamara", '-', 1) AS INTEGER)
          );
    """)
    
    missing_ids = [row[0] for row in session.execute(query_missing) if row[0]]
    
    if not missing_ids:
        print("✅ Nenhuma proposição faltante encontrada.")
        return

    print(f"📦 Encontrados {len(missing_ids)} IDs para baixar. Iniciando coleta...")

    for prop_id in missing_ids:
        try:
            # 2. Consulta a API da Câmara
            url = f"https://dadosabertos.camara.leg.br/api/v2/proposicoes/{prop_id}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()['dados']
                
                # 3. Insere na tabela proposicoes (ajuste as colunas conforme seu modelo)
                # Usei um SQL raw aqui para simplificar, mas você pode usar o objeto Proposicao
                insert_stmt = text("""
                    INSERT INTO public.proposicoes (id, "idCamara", uri, "siglaTipo", numero, ano, ementa)
                    VALUES (:id, :idCamara, :uri, :siglaTipo, :numero, :ano, :ementa)
                    ON CONFLICT ("idCamara") DO NOTHING;
                """)
                
                session.execute(insert_stmt, {
                    "id": int(data['id']),
                    "idCamara": str(data['id']),
                    "uri": data['uri'],
                    "siglaTipo": data['siglaTipo'],
                    "numero": data['numero'],
                    "ano": data['ano'],
                    "ementa": data['ementa']
                })
                # Commit individual para garantir que o registro seja salvo e a transação limpa
                session.commit()
                print(f"✔️ Proposição {prop_id} processada.")
            else:
                print(f"⚠️ Falha ao buscar {prop_id}: Status {response.status_code}")

        except Exception as e:
            session.rollback()
            print(f"❌ Erro ao processar ID {prop_id}: {e}")

    # Finalização: Atualiza a FK nas votações
    print("⚙️ Vinculando votações às proposições existentes...")
    try:
        # A mágica está no EXISTS: ele garante que só mexemos no que tem par correspondente
        update_query = text("""
            UPDATE public.votacoes v
            SET "idProposicao" = CAST(split_part(v."idCamara", '-', 1) AS INTEGER)
            WHERE v."idProposicao" IS NULL 
              AND v."idCamara" IS NOT NULL
              AND EXISTS (
                  SELECT 1 FROM public.proposicoes p 
                  WHERE p.id = CAST(split_part(v."idCamara", '-', 1) AS INTEGER)
              );
        """)
        result = session.execute(update_query)
        session.commit()
        print(f"✅ Sucesso! {result.rowcount} votações foram vinculadas.")
    except Exception as e:
        session.rollback()
        print(f"❌ Erro ao atualizar votações: {e}")
if __name__ == "__main__":
    backfill_proposicoes()