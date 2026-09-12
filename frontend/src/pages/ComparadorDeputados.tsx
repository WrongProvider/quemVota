import React, { useEffect, useState } from "react"
import { useSeo } from "../hooks/useSeo"
import { fetchResumoMetricas, type ResumoMetricasDeputado } from "../api/metricas.api"
import Header from "../components/Header"
import { formatarMoedaBRL } from "../utils/formatters"
import { useNavigate } from "react-router-dom"

export default function ComparadorDeputados() {
  useSeo({
    title: "Comparador de Parlamentares | Estatísticas e Transparência - QuemVota",
    description: "Compare dados factuais, presenças, gastos da cota e produção legislativa dos parlamentares brasileiros sem juízo de valor.",
  })

  const navigate = useNavigate()
  const [metricas, setMetricas] = useState<ResumoMetricasDeputado[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [ordenacao, setOrdenacao] = useState<keyof ResumoMetricasDeputado>("nome")
  const [direcao, setDirecao] = useState<"asc" | "desc">("asc")
  const [filtroUF, setFiltroUF] = useState<string>("")
  const [filtroPartido, setFiltroPartido] = useState<string>("")

  useEffect(() => {
    fetchResumoMetricas()
      .then((data) => {
        setMetricas(data)
        setLoading(false)
      })
      .catch((err) => {
        console.error(err)
        setError(true)
        setLoading(false)
      })
  }, [])

  const sortData = (col: keyof ResumoMetricasDeputado) => {
    if (ordenacao === col) {
      setDirecao(direcao === "asc" ? "desc" : "asc")
    } else {
      setOrdenacao(col)
      setDirecao("desc")
    }
  }

  const ufs = Array.from(new Set(metricas.map((m) => m.uf))).filter(Boolean).sort()
  const partidos = Array.from(new Set(metricas.map((m) => m.partido))).filter(Boolean).sort()

  const dadosFiltrados = metricas
    .filter((m) => (filtroUF ? m.uf === filtroUF : true))
    .filter((m) => (filtroPartido ? m.partido === filtroPartido : true))
    .sort((a, b) => {
      const valA = a[ordenacao]
      const valB = b[ordenacao]
      if (valA === null || valA === undefined) return 1
      if (valB === null || valB === undefined) return -1
      
      if (typeof valA === "string" && typeof valB === "string") {
        return direcao === "asc" ? valA.localeCompare(valB) : valB.localeCompare(valA)
      }
      if (valA < valB) return direcao === "asc" ? -1 : 1
      if (valA > valB) return direcao === "asc" ? 1 : -1
      return 0
    })

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col">
        <Header />
        <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 flex items-center justify-center">
          <div className="animate-pulse flex flex-col items-center">
            <div className="h-8 w-64 bg-slate-200 rounded mb-4"></div>
            <div className="h-64 w-full bg-slate-200 rounded"></div>
          </div>
        </main>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col">
        <Header />
        <main className="flex-1 max-w-7xl w-full mx-auto p-4 flex items-center justify-center">
          <p className="text-red-500 font-semibold">Ocorreu um erro ao carregar as métricas.</p>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans text-slate-900">
      <Header />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900">Comparador de Parlamentares</h1>
          <p className="text-slate-600 mt-2 text-lg">
            Explore dados factuais de gastos, presença e produção legislativa de forma neutra.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <select 
            className="border-slate-300 rounded-md shadow-sm p-2 bg-white"
            value={filtroUF}
            onChange={(e) => setFiltroUF(e.target.value)}
          >
            <option value="">Todos os Estados</option>
            {ufs.map((uf) => (
              <option key={uf} value={uf}>{uf}</option>
            ))}
          </select>

          <select 
            className="border-slate-300 rounded-md shadow-sm p-2 bg-white"
            value={filtroPartido}
            onChange={(e) => setFiltroPartido(e.target.value)}
          >
            <option value="">Todos os Partidos</option>
            {partidos.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>

        {/* Tabela Mobile-First: No mobile mostra cards, no desktop tabela */}
        <div className="block lg:hidden space-y-4">
          {dadosFiltrados.map((m) => (
            <div 
              key={m.idDeputado} 
              className="bg-white rounded-lg shadow p-4 cursor-pointer active:bg-slate-50"
              onClick={() => navigate(`/politicos/${m.idDeputado}`)}
            >
              <div className="flex items-center gap-4 mb-3">
                <img src={m.urlFoto || ""} alt={m.nome} className="w-12 h-12 rounded-full object-cover bg-slate-200" />
                <div>
                  <h3 className="font-bold text-slate-800">{m.nome}</h3>
                  <p className="text-sm text-slate-500">{m.partido} - {m.uf}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="bg-slate-50 p-2 rounded">
                  <span className="block text-slate-500 text-xs uppercase tracking-wider">Gastos CEAP</span>
                  <span className="font-medium">{formatarMoedaBRL(m.totalGastoCota)}</span>
                </div>
                <div className="bg-slate-50 p-2 rounded">
                  <span className="block text-slate-500 text-xs uppercase tracking-wider">Projetos</span>
                  <span className="font-medium">{m.totalProposicoesAutor}</span>
                </div>
                <div className="bg-slate-50 p-2 rounded col-span-2">
                  <span className="block text-slate-500 text-xs uppercase tracking-wider">Presenças Registradas</span>
                  <span className="font-medium">{m.totalPresencas}</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="hidden lg:block bg-white shadow-sm rounded-lg overflow-hidden border border-slate-200">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Perfil</th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider cursor-pointer hover:bg-slate-100"
                    onClick={() => sortData("partido")}
                  >
                    Partido/UF {ordenacao === "partido" && (direcao === "asc" ? "↑" : "↓")}
                  </th>
                  <th 
                    className="px-6 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider cursor-pointer hover:bg-slate-100"
                    onClick={() => sortData("totalGastoCota")}
                  >
                    Gastos (CEAP) {ordenacao === "totalGastoCota" && (direcao === "asc" ? "↑" : "↓")}
                  </th>
                  <th 
                    className="px-6 py-3 text-center text-xs font-medium text-slate-500 uppercase tracking-wider cursor-pointer hover:bg-slate-100"
                    onClick={() => sortData("totalProposicoesAutor")}
                  >
                    Projetos (Autor) {ordenacao === "totalProposicoesAutor" && (direcao === "asc" ? "↑" : "↓")}
                  </th>
                  <th 
                    className="px-6 py-3 text-center text-xs font-medium text-slate-500 uppercase tracking-wider cursor-pointer hover:bg-slate-100"
                    onClick={() => sortData("totalPresencas")}
                  >
                    Presenças {ordenacao === "totalPresencas" && (direcao === "asc" ? "↑" : "↓")}
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-slate-200">
                {dadosFiltrados.map((m) => (
                  <tr 
                    key={m.idDeputado} 
                    className="hover:bg-slate-50 cursor-pointer transition-colors"
                    onClick={() => navigate(`/politicos/${m.idDeputado}`)}
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-10 w-10">
                          <img className="h-10 w-10 rounded-full object-cover bg-slate-200" src={m.urlFoto || ""} alt="" />
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-slate-900">{m.nome}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-slate-500">
                      {m.partido} - {m.uf}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right font-medium text-slate-700">
                      {formatarMoedaBRL(m.totalGastoCota)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center text-slate-700">
                      {m.totalProposicoesAutor}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center text-slate-700">
                      {m.totalPresencas}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  )
}
