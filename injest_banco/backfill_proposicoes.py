import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configurações de conexão (ajuste com seus dados)
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/quemvota_teste"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

def backfill_proposicoes():
    print("🔍 Identificando IDs de proposições faltantes...")
    
    # Busca na tabela votacoes os idCamara_proposicao que NÃO existem na tabela proposicoes (comparando com p."idCamara")
    query_missing = text("""
        SELECT DISTINCT split_part(v."idCamara", '-', 1) as id_camara_faltante
        FROM public.votacoes v
        WHERE v."idProposicao" IS NULL
          AND split_part(v."idCamara", '-', 1) ~ '^[0-9]+$' -- Garante que extraímos apenas números válidos
          AND NOT EXISTS (
              SELECT 1 FROM public.proposicoes p 
              WHERE p."idCamara" = CAST(split_part(v."idCamara", '-', 1) AS INTEGER)
          );
    """)
    
    missing_ids = [row[0] for row in session.execute(query_missing) if row[0]]
    
    if not missing_ids:
        print("✅ Nenhuma proposição faltante encontrada.")
    else:
        print(f"📦 Encontrados {len(missing_ids)} IDs da Câmara. Iniciando coleta na API...")

        for camara_id in missing_ids:
            try:
                url = f"https://dadosabertos.camara.leg.br/api/v2/proposicoes/{camara_id}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()['dados']
                    
                    # Inserção na tabela proposicoes. 
                    # Deixamos o banco gerar o 'id' local (PK) automaticamente.
                    insert_stmt = text("""
                        INSERT INTO public.proposicoes ("idCamara", uri, "siglaTipo", numero, ano, ementa)
                        VALUES (:idCamara, :uri, :sigla, :num, :ano, :ementa)
                        ON CONFLICT ("idCamara") DO NOTHING;
                    """)
                    
                    session.execute(insert_stmt, {
                        "idCamara": int(data['id']), # O id da API é o nosso idCamara
                        "uri": data['uri'],
                        "sigla": data['siglaTipo'],
                        "num": data['numero'],
                        "ano": data['ano'],
                        "ementa": data['ementa']
                    })
                    
                    session.commit()
                    print(f"✔️ Proposição idCamara={camara_id} processada.")
                
                elif response.status_code == 404:
                    print(f"⚠️ Proposição idCamara={camara_id} não encontrada na API (404).")
                    session.rollback()

            except Exception as e:
                session.rollback()
                print(f"❌ Erro ao processar idCamara={camara_id}: {e}")

    # =====================================================================
    # A MÁGICA DO VÍNCULO ACONTECE AQUI
    # =====================================================================
    print("⚙️ Vinculando votações às proposições usando o ID local...")
    try:
        # 1. Fazemos um JOIN entre a string extraída da votação e a coluna idCamara da proposição.
        # 2. Pegamos o p.id (ID local gerado pelo banco) e injetamos em v."idProposicao".
        update_query = text("""
            UPDATE public.votacoes v
            SET "idProposicao" = p.id
            FROM public.proposicoes p
            WHERE p."idCamara" = CAST(split_part(v."idCamara", '-', 1) AS INTEGER)
              AND v."idProposicao" IS NULL;
        """)
        
        result = session.execute(update_query)
        session.commit()
        print(f"✅ Sucesso! {result.rowcount} votações foram vinculadas corretamente com os IDs locais.")
    except Exception as e:
        session.rollback()
        print(f"❌ Erro ao atualizar votações: {e}")

if __name__ == "__main__":
    backfill_proposicoes()