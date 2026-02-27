import { useState } from "react"
import { Link } from "react-router-dom"
import Header from "../components/Header"
import { ChevronDown, Search, ArrowRight } from "lucide-react"

// ─────────────────────────────────────────────────────────────────────────────
// Dados
// ─────────────────────────────────────────────────────────────────────────────

interface FaqItem {
  q: string
  a: React.ReactNode
}

interface FaqCategoria {
  id: string
  label: string
  emoji: string
  items: FaqItem[]
}

const CATEGORIAS: FaqCategoria[] = [
  {
    id: "plataforma",
    label: "Plataforma",
    emoji: "💡",
    items: [
      {
        q: "O que é o quemvota?",
        a: (
          <>
            O quemvota é uma plataforma independente de transparência legislativa. Coletamos, processamos
            e apresentamos dados públicos da Câmara dos Deputados de forma organizada e acessível para
            qualquer cidadão.
          </>
        ),
      },
      {
        q: "O projeto tem alguma afiliação política ou partidária?",
        a: (
          <>
            Nenhuma. O quemvota é completamente independente e não tem financiamento público, partidário
            ou empresarial. Não fazemos julgamentos políticos — apresentamos os dados como estão nas
            fontes oficiais e deixamos a interpretação com o usuário.
          </>
        ),
      },
      {
        q: "O quemvota cobre deputados estaduais ou vereadores?",
        a: (
          <>
            Atualmente cobrimos apenas <strong>deputados federais</strong> da Câmara dos Deputados.
            Pretendemos expandir para senadores e deputados estaduais em versões futuras, mas dependemos
            da disponibilidade de APIs públicas com dados estruturados.
          </>
        ),
      },
      {
        q: "Com que frequência os dados são atualizados?",
        a: (
          <>
            Os dados são coletados <strong>diariamente</strong> a partir das APIs públicas da Câmara.
            Votações, presenças e despesas costumam aparecer na plataforma com até 24 horas de defasagem
            em relação ao evento original.
          </>
        ),
      },
    ],
  },
  {
    id: "dados",
    label: "Dados",
    emoji: "📊",
    items: [
      {
        q: "De onde vêm os dados?",
        a: (
          <>
            Exclusivamente de fontes públicas e oficiais: a{" "}
            <a
              href="https://dadosabertos.camara.leg.br"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              API de Dados Abertos da Câmara dos Deputados
            </a>{" "}
            e o Portal de Dados Abertos do Senado Federal. Não produzimos nem estimamos nenhum dado —
            tudo tem origem rastreável.
          </>
        ),
      },
      {
        q: "Os dados podem estar errados?",
        a: (
          <>
            Sim, é possível. Embora façamos validações no processo de coleta, os dados refletem o que
            está na fonte oficial. Se a Câmara registrar uma informação incorreta, nosso banco também
            conterá essa inconsistência. Erros que identificarmos são corrigidos nas próximas coletas.
            Se encontrar algo suspeito,{" "}
            <a href="https://github.com/WrongProvider/quemVota" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
              reporte pelo GitHub
            </a>
            .
          </>
        ),
      },
      {
        q: "Por que alguns parlamentares têm dados incompletos?",
        a: (
          <>
            Alguns deputados assumiram o mandato no meio da legislatura (por licença de titular, morte
            ou outro motivo) e podem ter períodos sem cobertura. Além disso, dados históricos anteriores
            a 2019 podem estar incompletos pela limitação das APIs da Câmara.
          </>
        ),
      },
      {
        q: "Por que eu não acho um político específico como por exemplo: Lula, Bolsonaro, Vereador Zezinha?",
        a: (
          <>
            Infelizmente ainda não temos dados de politicos do Executivo ou seja 
            <strong>Vereadores, Governadores, Presidentes</strong> ainda não 
            estão dentro da nossa plataforma, mas estamos trabalhando 
            para expandir nossa cobertura no futuro. Por ora,
            o foco é exclusivamente nos <strong>Deputados Federais e Senadores</strong>.  
          </>
        ),
      },
      {
        q: "O que são as despesas de gabinete (CEAP)?",
        a: (
          <>
            A <strong>Cota para Exercício da Atividade Parlamentar (CEAP)</strong> é uma verba que cada
            deputado recebe mensalmente para cobrir despesas do mandato — passagens aéreas, hospedagem,
            combustível, material de escritório, entre outros. O valor varia por estado (entre ~R$ 36 mil
            e ~R$ 51 mil/mês). O uso da cota é público e obrigatoriamente divulgado pela Câmara.
          </>
        ),
      },
    ],
  },
  {
    id: "score",
    label: "Score de performance",
    emoji: "🏆",
    items: [
      {
        q: "O que é o score de performance?",
        a: (
          <>
            É uma pontuação de 0 a 100 que resume o desempenho parlamentar em três dimensões:{" "}
            <strong>assiduidade</strong> (presença em votações),{" "}
            <strong>economia</strong> (uso da cota parlamentar) e{" "}
            <strong>produção legislativa</strong> (proposições apresentadas). Veja a metodologia
            completa na{" "}
            <Link to="/metodologia" className="text-blue-600 hover:underline">
              página de Metodologia
            </Link>
            .
          </>
        ),
      },
      {
        q: "O score é uma medida justa?",
        a: (
          <>
            É uma medida objetiva e transparente, mas não é perfeita. Ela não captura qualidade das
            proposições, articulação política, atuação em comissões, atendimento ao eleitorado ou
            contexto de ausências justificadas. Use o score como ponto de partida, não como veredicto.
          </>
        ),
      },
      {
        q: "Por que a ponderação é 15% / 40% / 45%?",
        a: (
          <>
            Os pesos refletem uma escolha metodológica nossa. Priorizamos <strong>produção legislativa</strong>{" "}
            (45%) por ser a função-fim do mandato, <strong>economia da cota</strong> (40%) por representar
            uso responsável de dinheiro público, e <strong>assiduidade</strong> (15%) como critério base
            de presença. Os pesos são debatíveis — a metodologia é aberta para discussão.
          </>
        ),
      },
      {
        q: "Por que um deputado tem score zero?",
        a: (
          <>
            Score zero geralmente indica que o deputado gastou mais do que sua cota (nota de economia = 0)
            e teve produção legislativa muito baixa. Também pode acontecer com parlamentares que assumiram
            o mandato recentemente e ainda têm poucos registros.
          </>
        ),
      },
    ],
  },
  {
    id: "tecnico",
    label: "Técnico e legal",
    emoji: "⚙️",
    items: [
      {
        q: "O código-fonte do projeto é aberto?",
        a: (
          <>
            Sim. O código está disponível no{" "}
            <a href="https://github.com/WrongProvider/quemVota" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
              GitHub
            </a>
            . Qualquer pessoa pode auditar, contribuir ou apontar erros.
          </>
        ),
      },
      {
        q: "Posso usar os dados do quemvota em outro projeto?",
        a: (
          <>
            Os dados em si são públicos (provenientes da Câmara). Nossa API interna não é pública por
            ora, mas você pode consumir diretamente as fontes originais. Para parcerias ou acesso
            diferenciado, entre em contato pelo GitHub.
          </>
        ),
      },
      {
        q: "O quemvota respeita a LGPD?",
        a: (
          <>
            Todos os dados pessoais exibidos (nome, foto, cargo) são públicos por força da lei de
            transparência e divulgados pela própria Câmara. Não coletamos dados pessoais dos usuários
            da plataforma além do necessário para o funcionamento do site.
          </>
        ),
      },
    ],
  },
]

// ─────────────────────────────────────────────────────────────────────────────
// Componente de acordeão
// ─────────────────────────────────────────────────────────────────────────────

function Acordeao({ item }: { item: FaqItem }) {
  const [open, setOpen] = useState(false)

  return (
    <div className={`border-b border-slate-100 last:border-b-0 transition-colors ${open ? "bg-slate-50/50" : ""}`}>
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-start justify-between gap-4 px-6 py-4 text-left hover:bg-slate-50 transition-colors cursor-pointer border-0 bg-transparent"
      >
        <span className="text-sm font-medium text-slate-800 leading-snug flex-1">{item.q}</span>
        <ChevronDown
          size={16}
          className={`text-slate-400 flex-shrink-0 mt-0.5 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open && (
        <div className="px-6 pb-5 text-sm text-slate-600 leading-relaxed">
          {item.a}
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Página principal
// ─────────────────────────────────────────────────────────────────────────────

export default function FAQ() {
  const [busca, setBusca] = useState("")
  const [categoriaAtiva, setCategoriaAtiva] = useState<string | null>(null)

  // Filtra as perguntas pela busca
  const filtrado = CATEGORIAS.map((cat) => ({
    ...cat,
    items: cat.items.filter(
      (item) =>
        !busca ||
        item.q.toLowerCase().includes(busca.toLowerCase())
    ),
  })).filter((cat) => {
    if (busca) return cat.items.length > 0
    if (categoriaAtiva) return cat.id === categoriaAtiva
    return true
  })

  const totalPerguntas = CATEGORIAS.reduce((acc, cat) => acc + cat.items.length, 0)

  return (
    <>
      <Header />
      <div className="min-h-screen bg-gray-50 pt-16">

        {/* Header da página */}
        <div className="bg-white border-b border-slate-200">
          <div className="max-w-4xl mx-auto px-6 py-12">
            <p className="text-xs font-semibold tracking-widest uppercase text-blue-600 mb-3">
              Institucional
            </p>
            <h1
              style={{ fontFamily: "'Fraunces', serif" }}
              className="text-4xl font-bold text-slate-900 mb-4"
            >
              Perguntas frequentes
            </h1>
            <p className="text-slate-500 text-base leading-relaxed max-w-xl">
              {totalPerguntas} perguntas organizadas por tema. Não encontrou o que procura?{" "}
              <a href="https://github.com/WrongProvider/quemVota" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                Abra uma issue no GitHub
              </a>
              .
            </p>
          </div>
        </div>

        <div className="max-w-4xl mx-auto px-6 py-10">

          {/* Busca + filtro de categoria */}
          <div className="flex flex-col sm:flex-row gap-3 mb-8">
            {/* Campo de busca */}
            <div className="relative flex-1">
              <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Buscar pergunta..."
                value={busca}
                onChange={(e) => {
                  setBusca(e.target.value)
                  if (e.target.value) setCategoriaAtiva(null)
                }}
                className="w-full pl-10 pr-4 py-2.5 text-sm border border-slate-200 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all"
              />
            </div>

            {/* Filtros de categoria */}
            <div className="flex items-center gap-2 flex-wrap">
              <button
                onClick={() => { setCategoriaAtiva(null); setBusca("") }}
                className={`px-3 py-2 rounded-xl text-xs font-medium transition-all border cursor-pointer ${
                  !categoriaAtiva && !busca
                    ? "bg-[#1a1a1a] text-white border-[#1a1a1a]"
                    : "bg-white text-slate-600 border-slate-200 hover:border-slate-300"
                }`}
              >
                Todas
              </button>
              {CATEGORIAS.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => { setCategoriaAtiva(cat.id); setBusca("") }}
                  className={`px-3 py-2 rounded-xl text-xs font-medium transition-all border cursor-pointer ${
                    categoriaAtiva === cat.id
                      ? "bg-blue-600 text-white border-blue-600"
                      : "bg-white text-slate-600 border-slate-200 hover:border-slate-300"
                  }`}
                >
                  {cat.emoji} {cat.label}
                </button>
              ))}
            </div>
          </div>

          {/* Lista de perguntas */}
          {filtrado.length === 0 ? (
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm py-16 text-center">
              <p className="text-slate-400 text-sm">Nenhuma pergunta encontrada para "{busca}".</p>
              <button
                onClick={() => setBusca("")}
                className="mt-3 text-xs text-blue-600 hover:underline cursor-pointer border-0 bg-transparent"
              >
                Limpar busca
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {filtrado.map((cat) => (
                <div key={cat.id} className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                  {/* Header da categoria */}
                  <div className="flex items-center gap-2.5 px-6 py-4 border-b border-slate-100 bg-slate-50/60">
                    <span className="text-base">{cat.emoji}</span>
                    <span
                      style={{ fontFamily: "'Fraunces', serif" }}
                      className="text-sm font-semibold text-slate-700"
                    >
                      {cat.label}
                    </span>
                    <span className="ml-auto text-xs text-slate-400 font-medium">
                      {cat.items.length} {cat.items.length === 1 ? "pergunta" : "perguntas"}
                    </span>
                  </div>

                  {/* Perguntas da categoria */}
                  {cat.items.map((item, i) => (
                    <Acordeao key={i} item={item} />
                  ))}
                </div>
              ))}
            </div>
          )}

          {/* CTA final */}
          <div className="mt-10 bg-blue-50 border border-blue-100 rounded-2xl p-7 flex flex-col sm:flex-row items-center gap-5">
            <div className="flex-1">
              <p className="text-sm font-semibold text-slate-800 mb-1">Ainda tem dúvidas?</p>
              <p className="text-sm text-slate-500 leading-relaxed">
                Abra uma issue no GitHub ou explore a metodologia completa de cálculo do score.
              </p>
            </div>
            <div className="flex items-center gap-2 flex-wrap flex-shrink-0">
              <Link
                to="/metodologia"
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-white border border-slate-200 text-slate-700 text-xs font-medium rounded-xl no-underline hover:border-slate-300 transition-colors"
              >
                Ver metodologia <ArrowRight size={12} />
              </Link>
              <a
                href="https://github.com/WrongProvider/quemVota"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium rounded-xl no-underline transition-colors"
              >
                GitHub
              </a>
            </div>
          </div>

        </div>

        {/* Rodapé */}
        <div className="border-t border-slate-200 bg-white py-6 text-center">
          <p className="text-xs text-slate-400">
            Dados públicos da{" "}
            <a href="https://dadosabertos.camara.leg.br" target="_blank" rel="noreferrer" className="text-slate-500 hover:text-blue-600 transition-colors">
              Câmara dos Deputados
            </a>
            {" "}· quemvota.com.br
          </p>
        </div>
      </div>
    </>
  )
}