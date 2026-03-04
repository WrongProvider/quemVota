import os
import requests
from io import BytesIO
from PIL import Image
from injest_banco.db.database import SessionLocal
from injest_banco.db.models import Politico

# Configurações
PASTA_DESTINO = "../frontend/public/fotos_politicos" # Mude para a pasta real da sua VPS
TIMEOUT_REQUISICAO = 10 # Segundos antes de desistir de uma foto demorada

def configurar_pasta():
    """Garante que a pasta de destino exista."""
    if not os.path.exists(PASTA_DESTINO):
        os.makedirs(PASTA_DESTINO)
        print(f"Pasta criada: {PASTA_DESTINO}")

def baixar_e_converter_fotos():
    configurar_pasta()
    with SessionLocal() as db:
        # Busca apenas quem tem URL cadastrados
        politicos = db.query(Politico.id, Politico.url_foto).filter(Politico.url_foto.isnot(None)).all()
        
        print(f"Encontrados {len(politicos)} políticos para processar.")

        for politico_id, url in politicos:
            caminho_arquivo = os.path.join(PASTA_DESTINO, f"{politico_id}.jpg")
            
            # Pula se a foto já foi baixada (útil caso o script pare no meio e você precise rodar de novo)
            if os.path.exists(caminho_arquivo):
                print(f"[{politico_id}] Já existe, pulando...")
                continue
                
            print(f"[{politico_id}] Baixando: {url}")
            
            try:
                # Faz o download da imagem fingindo ser um navegador (evita bloqueios básicos)
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                resposta = requests.get(url, headers=headers, timeout=TIMEOUT_REQUISICAO)
                resposta.raise_for_status() # Lança erro se der 404, 500, etc.

                # Abre a imagem em memória e converte para JPG padrão
                imagem = Image.open(BytesIO(resposta.content))
                
                # Converte para RGB (necessário se a imagem original for PNG com transparência)
                if imagem.mode in ("RGBA", "P"):
                    imagem = imagem.convert("RGB")
                    
                # Salva na VPS
                imagem.save(caminho_arquivo, "JPEG", quality=85)
                print(f"[{politico_id}] Sucesso!")
                
            except Exception as e:
                # Captura qualquer erro (site fora do ar, link quebrado) e continua o loop
                print(f"[{politico_id}] ERRO ao processar: {e}")

        print("\nProcesso finalizado!")

if __name__ == "__main__":
    baixar_e_converter_fotos()