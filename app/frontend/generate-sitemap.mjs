import fs from "fs"
import path from "path"
import { fileURLToPath } from "url"

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// ─── Configuração ────────────────────────────────────────────────────────────
const API_URL   = process.env.API_URL  || "http://localhost:8000"
const PUBLIC_DIR = path.resolve(__dirname, "public")

// ─── Helpers ─────────────────────────────────────────────────────────────────
function ensurePublicDir() {
  if (!fs.existsSync(PUBLIC_DIR)) {
    fs.mkdirSync(PUBLIC_DIR, { recursive: true })
    console.log(`📁 Pasta criada: ${PUBLIC_DIR}`)
  }
}

async function fetchAndSave(endpoint, filename) {
  const url = `${API_URL}/${endpoint}`
  console.log(`⬇️  Buscando ${url} ...`)

  const res = await fetch(url)

  if (!res.ok) {
    throw new Error(`Falha ao buscar ${url} — status ${res.status} ${res.statusText}`)
  }

  const content = await res.text()
  const dest    = path.join(PUBLIC_DIR, filename)

  fs.writeFileSync(dest, content, "utf-8")
  console.log(`✅ Salvo em: ${dest}`)
}

// ─── Main ─────────────────────────────────────────────────────────────────────
async function main() {
  ensurePublicDir()

  await Promise.all([
    fetchAndSave("robots.txt",  "robots.txt"),
    fetchAndSave("sitemap.xml", "sitemap.xml"),
  ])

  console.log("\n🎉 robots.txt e sitemap.xml atualizados com sucesso!")
}

main().catch(err => {
  console.error("❌ Erro:", err.message)
  process.exit(1)
})
