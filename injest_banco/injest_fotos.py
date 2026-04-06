import os
import requests
import numpy as np
import cv2
from cv2 import dnn_superres
from injest_banco.db.database import SessionLocal
from injest_banco.db.models import Deputado

# Configurações
PASTA_DESTINO = "frontend/public/fotos_politicos" # Mude para a pasta real da sua VPS
TIMEOUT_REQUISICAO = 10
MODELO_IA_CAMINHO = "ESPCN_x4.pb" # O arquivo que você baixou no Passo 2

def configurar_pasta():
    """Garante que a pasta de destino exista."""
    if not os.path.exists(PASTA_DESTINO):
        os.makedirs(PASTA_DESTINO)
        print(f"Pasta criada: {PASTA_DESTINO}")

def inicializar_modelo_ia():
    """Carrega o modelo de Inteligência Artificial para a memória."""
    if not os.path.exists(MODELO_IA_CAMINHO):
        raise FileNotFoundError(f"Arquivo '{MODELO_IA_CAMINHO}' não encontrado. Baixe-o e coloque na pasta do script.")
    
    # Inicializa o módulo de Super Resolução
    sr = dnn_superres.DnnSuperResImpl_create()
    sr.readModel(MODELO_IA_CAMINHO)
    
    # Define o modelo e a escala. "espcn" é o algoritmo, 4 é quantas vezes vai aumentar.
    sr.setModel("espcn", 4) 
    return sr

def baixar_e_converter_fotos():
    configurar_pasta()
    
    print("🧠 Carregando modelo de IA (ESPCN_x4)...")
    sr = inicializar_modelo_ia()
    
    with SessionLocal() as db:
        # Busca apenas quem tem URL cadastrados
        politicos = db.query(Deputado.id, Deputado.urlFoto).filter(Deputado.urlFoto.isnot(None)).all()
        
        print(f"Encontrados {len(politicos)} políticos para processar.")

        for politico_id, url in politicos:
            caminho_arquivo = os.path.join(PASTA_DESTINO, f"{politico_id}.jpg")
            
            # Pula se a foto já foi baixada
            if os.path.exists(caminho_arquivo):
                print(f"[{politico_id}] Já existe, pulando...")
                continue
                
            print(f"[{politico_id}] Baixando e aplicando IA: {url}")
            
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                resposta = requests.get(url, headers=headers, timeout=TIMEOUT_REQUISICAO)
                resposta.raise_for_status()

                # 1. Converte os bytes da requisição para um Array do Numpy na memória
                nparr = np.frombuffer(resposta.content, np.uint8)
                
                # 2. Decodifica o Array para uma imagem que o OpenCV entende (BGR)
                img_cv2 = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if img_cv2 is None:
                    print(f"[{politico_id}] ERRO: A imagem baixada está corrompida ou é inválida.")
                    continue

                # 3. MÁGICA DA IA: Aplica o Upscaling 
                imagem_melhorada = sr.upsample(img_cv2)
                
                # 4. Salva na VPS com alta qualidade (95)
                cv2.imwrite(caminho_arquivo, imagem_melhorada, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
                print(f"[{politico_id}] Sucesso! Foto ampliada e salva.")
                
            except requests.exceptions.RequestException as e:
                print(f"[{politico_id}] ERRO de rede: {e}")
            except Exception as e:
                print(f"[{politico_id}] ERRO interno: {e}")

        print("\nProcesso ETL de fotos finalizado com sucesso!")

if __name__ == "__main__":
    baixar_e_converter_fotos()