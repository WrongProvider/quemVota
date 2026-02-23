import { AlertCircle, Database, TrendingUp, DollarSign, FileText, Users } from "lucide-react"
import Header from "../components/Header"

export default function Metodologia() {
  return (
    <>
      <Header />
      <div className="max-w-4xl mx-auto px-8 py-12 font-sans">

        {/* HEADER */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold mb-4 text-slate-800">
            📊 Metodologia de Cálculo
          </h1>
          <p className="text-lg text-slate-500 leading-relaxed">
            Entenda como calculamos o score de performance parlamentar com base em três pilares principais:
            assiduidade, economia e produção legislativa.
          </p>
        </div>

        {/* FONTES DE DADOS */}
        <Section icon={<Database size={24} className="text-blue-500" />} title="Fontes de Dados">
          <p className="mb-4">
            Todos os dados utilizados são provenientes de fontes públicas e oficiais:
          </p>
          <ul className="leading-loose text-slate-600 list-disc list-inside space-y-1">
            <li>
              <strong>API Pública da Câmara dos Deputados:</strong>{" "}
              <a
                href="https://dadosabertos.camara.leg.br/swagger/api.html"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-500 hover:underline"
              >
                dadosabertos.camara.leg.br
              </a>
            </li>
            <li>
              <strong>Webservice de Dados Abertos Legislativos:</strong>{" "}
              <a
                href="https://www2.camara.leg.br/transparencia/dados-abertos/dados-abertos-legislativo/webservices/proposicoes-1"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-500 hover:underline"
              >
                Proposições e Autoria
              </a>
            </li>
          </ul>
        </Section>

        {/* SCORE FINAL */}
        <Section icon={<TrendingUp size={24} className="text-emerald-500" />} title="Score Final de Performance">
          <p className="mb-6">
            O score final é calculado através de uma <strong>média ponderada</strong> de três critérios,
            variando de 0 a 100 pontos:
          </p>

          <FormulaBox>
            <code className="text-lg">
              Score Final = (Assiduidade × 0.15) + (Economia × 0.40) + (Produção × 0.45)
            </code>
          </FormulaBox>

          <div className="grid grid-cols-3 gap-4 mt-6">
            <WeightCard label="Assiduidade" weight="15%" colorClass="border-blue-500 text-blue-500" />
            <WeightCard label="Economia" weight="40%" colorClass="border-emerald-500 text-emerald-500" />
            <WeightCard label="Produção" weight="45%" colorClass="border-purple-500 text-purple-500" />
          </div>
        </Section>

        {/* CRITÉRIO 1: ASSIDUIDADE */}
        <Section icon={<Users size={24} className="text-blue-500" />} title="1. Assiduidade (Peso: 15%)">
          <p className="mb-4">
            Mede a presença do parlamentar nas sessões de votação da Câmara.
            Uma alta taxa de presença indica comprometimento com as atividades legislativas.
          </p>

          <FormulaBox>
            <code>Nota Assiduidade = (Presenças ÷ Total de Sessões) × 100</code>
          </FormulaBox>

          <ExampleBox>
            <strong>Exemplo:</strong><br />
            Parlamentar presente em 150 de 177 sessões:<br />
            <code>(150 ÷ 177) × 100 = 84,75 pontos</code>
          </ExampleBox>
        </Section>

        {/* CRITÉRIO 2: ECONOMIA */}
        <Section icon={<DollarSign size={24} className="text-emerald-500" />} title="2. Economia (Peso: 40%)">
          <p className="mb-4">
            Avalia o uso responsável da cota parlamentar (CEAP - Cota para Exercício da Atividade Parlamentar).
            Cada estado possui um limite mensal diferente.
          </p>

          <FormulaBox>
            <div className="mb-2">
              <code>Cota Total do Período = Cota Mensal × Meses de Mandato</code>
            </div>
            <div className="mb-2">
              <code>Economia = (Cota Total - Gasto Total) ÷ Cota Total</code>
            </div>
            <div>
              <code>Nota Economia = Economia × 100</code>
            </div>
          </FormulaBox>

          <ExampleBox>
            <strong>Exemplo (Amapá - R$ 40.000/mês):</strong><br />
            Mandato de 12 meses, gastou R$ 489.064,11<br />
            Cota total: <code>R$ 40.000 × 12 = R$ 480.000</code><br />
            Neste caso: gastou mais que a cota → <code>Nota = 0 pontos</code><br /><br />
            <em className="text-slate-500">
              * Se o gasto for menor que a cota, a nota aumenta proporcionalmente
            </em>
          </ExampleBox>

          <div className="mt-6 p-4 bg-slate-100 rounded-lg">
            <p className="m-0 text-sm text-slate-600">
              💡 <strong>Nota:</strong> As cotas variam por UF devido a diferenças de distância de Brasília
              e custo de vida. Estados mais distantes possuem cotas maiores para cobrir deslocamentos.
            </p>
          </div>
        </Section>

        {/* CRITÉRIO 3: PRODUÇÃO */}
        <Section icon={<FileText size={24} className="text-purple-500" />} title="3. Produção Legislativa (Peso: 45%)">
          <p className="mb-4">
            Avalia a quantidade e relevância das proposições legislativas apresentadas pelo parlamentar.
            Diferentes tipos de proposição recebem pontuações diferentes, e ser <strong>autor principal</strong> vale mais.
          </p>

          <div className="mb-6">
            <h4 className="mb-3 text-slate-800 font-semibold">
              Sistema de Pontuação por Tipo de Proposição:
            </h4>
            <ScoreTable>
              <thead>
                <tr>
                  <th>Tipo</th>
                  <th>Descrição</th>
                  <th>Autor Principal</th>
                  <th>Coautor</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>Alta Relevância</strong></td>
                  <td>PEC, PL, PLC, PLP</td>
                  <td className="text-emerald-500 font-bold">1.0 ponto</td>
                  <td className="text-slate-500">0.2 pontos</td>
                </tr>
                <tr>
                  <td><strong>Média Relevância</strong></td>
                  <td>PDC, PRC, MPV</td>
                  <td className="text-amber-500 font-bold">0.5 pontos</td>
                  <td className="text-slate-500">0.1 pontos</td>
                </tr>
                <tr>
                  <td><strong>Baixa Relevância</strong></td>
                  <td>Outros tipos</td>
                  <td className="text-gray-500 font-bold">0.05 pontos</td>
                  <td className="text-gray-400">0.01 pontos</td>
                </tr>
              </tbody>
            </ScoreTable>
          </div>

          <FormulaBox>
            <div className="mb-2">
              <code>Meta de Produção = Meses de Mandato × 2 proposições/mês</code>
            </div>
            <div>
              <code>Nota Produção = min((Total de Proposições ÷ Meta) × 100, 100)</code>
            </div>
          </FormulaBox>

          <ExampleBox>
            <strong>Exemplo:</strong><br />
            Mandato de 12 meses, apresentou:<br />
            • 3 PLs como autor principal = 3.0 pontos<br />
            • 2 PECs como coautor = 0.4 pontos<br />
            • 5 PDCs como autor = 2.5 pontos<br />
            <strong>Total:</strong> 5.9 pontos (≈ 6 proposições)<br /><br />
            Meta: <code>12 × 2 = 24 proposições</code><br />
            Nota: <code>(6 ÷ 24) × 100 = 25 pontos</code>
          </ExampleBox>

          <div className="mt-6 p-4 bg-slate-100 rounded-lg">
            <p className="m-0 text-sm text-slate-600">
              📌 <strong>Legenda dos tipos:</strong><br />
              <strong>PEC</strong> = Proposta de Emenda Constitucional |{" "}
              <strong>PL</strong> = Projeto de Lei |{" "}
              <strong>PLC</strong> = Projeto de Lei Complementar |{" "}
              <strong>PLP</strong> = Projeto de Lei do Plano Plurianual |{" "}
              <strong>PDC</strong> = Projeto de Decreto Legislativo |{" "}
              <strong>PRC</strong> = Projeto de Resolução |{" "}
              <strong>MPV</strong> = Medida Provisória
            </p>
          </div>
        </Section>

        {/* CLASSIFICAÇÃO */}
        <Section icon={<TrendingUp size={24} className="text-amber-500" />} title="Classificação do Score">
          <p className="mb-6">
            Com base no score final, os parlamentares são classificados em:
          </p>

          <div className="grid gap-4">
            <ClassificationCard label="Excelente" range="80 - 100" colorClass="border-emerald-500 bg-emerald-50 text-emerald-600" />
            <ClassificationCard label="Bom"       range="60 - 79"  colorClass="border-blue-500 bg-blue-50 text-blue-600" />
            <ClassificationCard label="Regular"   range="40 - 59"  colorClass="border-amber-500 bg-amber-50 text-amber-600" />
            <ClassificationCard label="Crítico"   range="0 - 39"   colorClass="border-red-500 bg-red-50 text-red-600" />
          </div>
        </Section>

        {/* LIMITAÇÕES */}
        <Section icon={<AlertCircle size={24} className="text-slate-500" />} title="Limitações e Considerações">
          <ul className="leading-loose text-slate-600 list-disc list-inside space-y-2">
            <li>
              <strong>Dados em desenvolvimento:</strong> O banco de dados ainda está sendo ajustado
              e pode apresentar inconsistências.
            </li>
            <li>
              <strong>Contexto político:</strong> O score não captura nuances como qualidade das proposições,
              impacto social ou contexto político de ausências justificadas.
            </li>
            <li>
              <strong>Atualização:</strong> Os dados são atualizados periodicamente conforme disponibilidade
              da API da Câmara.
            </li>
            <li>
              <strong>Uso educacional:</strong> Esta ferramenta tem fins educacionais e de transparência,
              não substituindo análises políticas profundas.
            </li>
          </ul>
        </Section>

        {/* RODAPÉ */}
        <div className="mt-16 pt-8 border-t-2 border-slate-200 text-center text-slate-500">
          <p className="m-0 text-sm">
            Dúvidas ou sugestões? Entre em contato através do nosso repositório no GitHub.
          </p>
        </div>
      </div>
    </>
  )
}

// ========== COMPONENTES AUXILIARES ==========

function Section({ icon, title, children }: { icon: React.ReactNode; title: string; children: React.ReactNode }) {
  return (
    <section className="mb-12">
      <div className="flex items-center gap-3 mb-6">
        {icon}
        <h2 className="text-3xl font-bold m-0 text-slate-800">{title}</h2>
      </div>
      <div className="text-base leading-relaxed text-slate-600">
        {children}
      </div>
    </section>
  )
}

function FormulaBox({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-slate-50 border-2 border-slate-200 rounded-lg p-5 font-mono text-sm overflow-x-auto mb-4">
      {children}
    </div>
  )
}

function ExampleBox({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-4 mt-4 text-sm leading-relaxed">
      {children}
    </div>
  )
}

function WeightCard({ label, weight, colorClass }: { label: string; weight: string; colorClass: string }) {
  return (
    <div className={`bg-slate-50 border-4 ${colorClass} rounded-lg p-4 text-center`}>
      <div className={`text-3xl font-bold mb-1 ${colorClass.split(" ").find(c => c.startsWith("text-"))}`}>
        {weight}
      </div>
      <div className="text-sm text-slate-500 font-medium">{label}</div>
    </div>
  )
}

function ScoreTable({ children }: { children: React.ReactNode }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm [&_th]:bg-slate-100 [&_th]:p-3 [&_th]:text-left [&_th]:font-semibold [&_th]:text-slate-800 [&_th]:border-b-2 [&_th]:border-slate-200 [&_td]:p-3 [&_td]:border-b [&_td]:border-slate-200 [&_tr:last-child_td]:border-b-0">
        {children}
      </table>
    </div>
  )
}

function ClassificationCard({ label, range, colorClass }: {
  label: string
  range: string
  colorClass: string
}) {
  return (
    <div className={`flex items-center justify-between border-2 rounded-lg px-6 py-4 ${colorClass}`}>
      <span className="text-lg font-semibold">{label}</span>
      <span className="text-base font-medium">{range} pontos</span>
    </div>
  )
}