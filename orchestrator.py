import subprocess
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO_ROOT = Path("/home/smok1ng_sn4ke/Documents/2026/quemVota")
BASE_WORKTREES = Path("/tmp/qv_agents_worktrees")

PARALLEL_AGENTS = [
    {
        "id": "backend",
        "branch": "agent/backend",
        "scope": "backend/",
        "prompt": "Trabalhe exclusivamente em backend/. Crie endpoints FastAPI consumindo proposições e votos. Não edite outras pastas."
    },
    {
        "id": "frontend",
        "branch": "agent/frontend",
        "scope": "frontend/",
        "prompt": "Trabalhe exclusivamente em frontend/. Crie os componentes de visualização de alinhamento e votos. Respeite os contratos da API."
    },
    {
        "id": "etl",
        "branch": "agent/etl",
        "scope": "injest_banco/",
        "prompt": "Você é o Engenheiro Especialista em ETL da Câmara. Trabalhe exclusivamente em injest_banco/. Siga a spec specs/006-etl_camara.md: refatore scripts monolíticos em módulos coesos (client, schemas_camara, loaders), valide dados com Pydantic V2, trate dados órfãos e garanta idempotência total nos upserts em lote."
    },
    {
        "id": "ai",
        "branch": "agent/ai",
        "scope": "embeddings/",
        "prompt": "Trabalhe exclusivamente em embeddings/. Ajuste a geração de embeddings com BAAI/bge-m3 tratando textoHash e ON CONFLICT."
    }
]

def create_worktree(branch: str, path: Path):
    """Cria uma Git Worktree isolada a partir da HEAD de main."""
    if path.exists():
        subprocess.run(["git", "worktree", "remove", "--force", str(path)], cwd=REPO_ROOT, check=False)
        shutil.rmtree(path, ignore_errors=True)

    subprocess.run(["git", "branch", "-D", branch], cwd=REPO_ROOT, check=False)
    subprocess.run(["git", "worktree", "add", "-b", branch, str(path), "main"], cwd=REPO_ROOT, check=True)

def run_antigravity(agent_cfg: dict) -> dict:
    agent_id = agent_cfg["id"]
    worktree_path = BASE_WORKTREES / agent_id

    create_worktree(agent_cfg["branch"], worktree_path)
    print(f"🚀 [WORKER INICIADO] {agent_id.upper()} em {worktree_path}")

    # Sintaxe corrigida de acordo com o help do agy
    cmd = [
        "agy",
        "--dangerously-skip-permissions",       # Auto-aprova execuções sem prompt interativo
        "--add-dir", str(worktree_path),        # Adiciona a worktree ao workspace
        "--print-timeout", "20m",               # Evita o timeout padrão de 5m
        "-p", agent_cfg["prompt"]               # Executa o prompt em modo não-interativo
    ]

    proc = subprocess.run(
        cmd,
        cwd=worktree_path,
        capture_output=True,
        text=True,
        timeout=1500
    )

    if proc.returncode != 0:
        print(f"\n[FALHA - {agent_id.upper()}] Detalhe:")
        print(proc.stderr or proc.stdout)

    return {
        "id": agent_id,
        "branch": agent_cfg["branch"],
        "success": proc.returncode == 0,
        "stdout": proc.stdout,
        "stderr": proc.stderr
    }
def run_qa_gatekeeper(merged_branch: str):
    """Agente final que roda no código integrado para executar testes e corrigir bugs."""
    qa_path = BASE_WORKTREES / "qa"
    create_worktree("agent/qa-validation", qa_path)

    print("🔍 [QA AGENT] Iniciando validação cruzada...")
    qa_prompt = (
        "Você é o QA Specialist. Valide o repositório completo:\n"
        "1. Rode 'pytest' no backend e em injest_banco.\n"
        "2. Valide o build do frontend ('npm run build' ou 'npm test').\n"
        "3. Se encontrar inconsistências entre contratos de backend e frontend, faça os ajustes e comite."
    )

    cmd = [
        "agy",
        "--workspace", str(qa_path),
        "--prompt", qa_prompt,
        "--auto-approve"
    ]
    subprocess.run(cmd, cwd=qa_path, check=False)

def orchestrate():
    BASE_WORKTREES.mkdir(parents=True, exist_ok=True)
    results = []

    # Fase 1: Execução Paralela dos 4 Especialistas
    print("=== FASE 1: EXECUÇÃO DOS AGENTES DE DOMÍNIO EM PARALELO ===")
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(run_antigravity, agent) for agent in PARALLEL_AGENTS]
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            status = "✔ CONCLUÍDO" if res["success"] else "❌ FALHA"
            print(f"[{status}] Agente: {res['id']}")

    # Fase 2: Validação / Integração com QA
    failed = [r["id"] for r in results if not r["success"]]
    if failed:
        print(f"⚠️ Abortando integração. Falha nos agentes: {failed}")
        return

    print("\n=== FASE 2: INTEGRAÇÃO E DISPARO DO AGENTE DE QA ===")
    # Merge das branches isoladas em uma staging branch
    staging_branch = "staging/multiagent-build"
    subprocess.run(["git", "checkout", "-B", staging_branch, "main"], cwd=REPO_ROOT, check=True)
    for agent in PARALLEL_AGENTS:
        subprocess.run(["git", "merge", agent["branch"], "--no-edit"], cwd=REPO_ROOT, check=True)

    run_qa_gatekeeper(staging_branch)
    print("🎉 Pipeline multiagente finalizada!")

if __name__ == "__main__":
    orchestrate()
