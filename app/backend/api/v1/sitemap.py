"""
sitemap.py — Endpoints de SEO: sitemap dinâmico e robots.txt.

GET /sitemap.xml  → sitemap com todas as páginas estáticas + perfis de políticos
GET /robots.txt   → instrui crawlers sobre o que podem e não podem indexar
"""

from datetime import date
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.models import Deputado

# ─────────────────────────────────────────────────────────────────────────────
# Configuração — edite ao colocar em produção
# ─────────────────────────────────────────────────────────────────────────────

#BASE_URL = "https://quemvota.com.br"   # prod
BASE_URL = "http://localhost:8000"    # dev
# Páginas estáticas do frontend — atualize se adicionar novas rotas
STATIC_PAGES: list[dict] = [
    {"loc": "/",             "priority": "1.0", "changefreq": "weekly"},
    {"loc": "/politicos",    "priority": "0.9", "changefreq": "weekly"},
    {"loc": "/rankings",     "priority": "0.8", "changefreq": "weekly"},
    {"loc": "/proposicoes",  "priority": "0.7", "changefreq": "daily"},
    {"loc": "/sobre",        "priority": "0.5", "changefreq": "monthly"},
    {"loc": "/metodologia",  "priority": "0.5", "changefreq": "monthly"},
    {"loc": "/faq",          "priority": "0.5", "changefreq": "monthly"},
    {"loc": "/roadmap",      "priority": "0.4", "changefreq": "monthly"},
]

router = APIRouter(tags=["SEO"])


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _url_entry(loc: str, lastmod: str, priority: str, changefreq: str) -> str:
    return (
        f"  <url>\n"
        f"    <loc>{BASE_URL}{loc}</loc>\n"
        f"    <lastmod>{lastmod}</lastmod>\n"
        f"    <changefreq>{changefreq}</changefreq>\n"
        f"    <priority>{priority}</priority>\n"
        f"  </url>"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Sitemap
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/sitemap.xml", include_in_schema=False)
async def sitemap(db: AsyncSession = Depends(get_db)):
    """
    Gera o sitemap XML dinamicamente.
    Inclui páginas estáticas + uma entrada por parlamentar (via slug).
    """
    today = date.today().isoformat()

    # Busca apenas id e slug — query leve, sem carregar o ORM inteiro
    result = await db.execute(
        select(Deputado.id, Deputado.slug)
        .where(Deputado.slug.is_not(None))
        .order_by(Deputado.id)
    )
    politicos = result.all()

    entries: list[str] = []

    # Páginas estáticas
    for page in STATIC_PAGES:
        entries.append(_url_entry(
            loc=page["loc"],
            lastmod=today,
            priority=page["priority"],
            changefreq=page["changefreq"],
        ))

    # Perfis dos parlamentares
    for politico in politicos:
        entries.append(_url_entry(
            loc=f"/politicos/{politico.slug}",
            lastmod=today,
            priority="0.8",
            changefreq="weekly",
        ))

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries)
        + "\n</urlset>"
    )

    return Response(content=xml, media_type="application/xml")


# ─────────────────────────────────────────────────────────────────────────────
# Robots.txt
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/robots.txt", include_in_schema=False)
async def robots():
    """
    Instrui crawlers sobre o que indexar.
    Bloqueia rotas de API, docs e endpoints legados com ID numérico.
    """
    content = f"""User-agent: *
Allow: /
Allow: /politicos/
Allow: /rankings
Allow: /proposicoes
Allow: /sobre
Allow: /metodologia
Allow: /faq
Allow: /roadmap

# Não indexar rotas de API nem documentação
Disallow: /docs
Disallow: /redoc
Disallow: /openapi.json
Disallow: /ranking/
Disallow: /busca/

# Não indexar URLs legadas com ID numérico — o Google deve usar o slug
Disallow: /politicos_detalhe/

Sitemap: {BASE_URL}/sitemap.xml
"""
    return Response(content=content, media_type="text/plain")