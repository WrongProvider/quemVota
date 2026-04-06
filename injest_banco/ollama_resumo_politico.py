import psycopg2
import requests
import time
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO_IA = "deepseek-r1:14b"

CONFIG = {'host':'localhost',
          'dbname':'quemvota',
          'user':'postgres',
          'password':'postgres'}



def gerar_resumo(prompt):
    payload = {
            "model": MODELO_IA,
            "prompt": prompt,
            "stream": True
            }
    complete_text = ""
    try:
        with requests.post(OLLAMA_URL, json=payload) as response:
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    chunk_text = chunk.get("response", "")
                    print(chunk_text, end="", flush=True)
                    complete_text += chunk_text
    except Exception as e:
        print(f"erro ao conectar com o OLLAMA: {e}")
        return None

    return complete_text

def processar_resumos(db):
        db.execute('SELECT "idDeputado" FROM  "resumoIa" WHERE "resumoFeitos" is NULL')
        records = db.fetchall()
        dic_politicos = {}

        if not records:
            return 0
        
        for deputado_id in records:
            # view que mostra idDeputado idVotacao data ultimaApresentacaoProposicao_descricao voto
            db.execute('SELECT * FROM view_detalhes_votacao WHERE "idDeputado" = %s', (deputado_id[0],))
            votacoes = db.fetchall()

            db.execute(f'SELECT nome FROM deputados WHERE id = {deputado_id[0]}')
            
            nome = str(db.fetchall()[0][0])
            dic_politicos[nome] = ""
            for descricoes in votacoes:
                dic_politicos[nome] += str(descricoes)

            # Montar o Prompt
            prompt = f"""
            Você é um analista político estritamente neutro, factual e direto. Seu objetivo é resumir a atuação do deputado {nome}.
            
            DADOS FORNECIDOS (Votos e Histórico):
            {dic_politicos[nome]}
            
            REGRAS OBRIGATÓRIAS:
            1. IDIOMA: Responda EXCLUSIVAMENTE em Português do Brasil. Nenhuma palavra em outro idioma ou caractere estrangeiro.
            2. FIDELIDADE: Use APENAS as informações presentes na seção "DADOS FORNECIDOS". NÃO invente números de projetos, não invente temas e não suponha nada.
            3. FORMATAÇÃO: NÃO use formatação Markdown (proibido usar asteriscos, hashtags ou marcadores de lista). Gere apenas texto puro.
            
            FORMATO DE SAÍDA EXIGIDO:
            Resumo: [Escreva aqui 1 parágrafo resumindo as tendências de votação e temas principais do deputado]
            
            Projetos Relevantes: [Liste os projetos de autoria dele que estejam expressamente citados nos dados. Se os dados não mencionarem projetos de autoria dele, escreva exatamente: "Não há projetos de autoria listados nos dados de votação."]
            """
            print("gerando resumo com IA")
            start_time = time.time()
            resumo = gerar_resumo(prompt)
        return resumo
if __name__ == "__main__":
    conn = psycopg2.connect(**CONFIG)
    with conn.cursor() as cur:
        resumo = processar_resumos(cur)
        print(resumo)
    


    
