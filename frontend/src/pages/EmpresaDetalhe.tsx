import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client";
import { formatarMoedaBRL } from "../utils/formatters";
import { useSeo } from "../hooks/useSeo";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#a28dda', '#8884d8', '#82ca9d', '#ffc658'];

export default function EmpresaDetalhe() {
  const { cnpj } = useParams<{ cnpj: string }>();
  const [empresa, setEmpresa] = useState<any>(null);
  const [notas, setNotas] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Reconstrói o CNPJ original substituindo "_" de volta por "/"
  const cnpjOriginal = cnpj ? decodeURIComponent(cnpj).replace(/_/g, '/') : '';

  useSeo({
    title: empresa ? `Fornecedor: ${empresa.nome} | QuemVota` : "Fornecedor | QuemVota",
    description: empresa ? `Análise descritiva dos pagamentos recebidos por ${empresa.nome} da Cota Parlamentar.` : "Análise de fornecedor.",
    canonicalUrl: `https://quemvota.com.br/empresas/${cnpj}`,
  });

  useEffect(() => {
    if (!cnpjOriginal) return;
    
    Promise.all([
      api.get(`/empresas/${encodeURIComponent(cnpjOriginal)}/resumo`),
      api.get(`/empresas/${encodeURIComponent(cnpjOriginal)}/notas`)
    ]).then(([resResumo, resNotas]) => {
      setEmpresa(resResumo.data);
      setNotas(resNotas.data);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, [cnpjOriginal]);

  if (loading) return <div className="p-8">Carregando...</div>;
  if (!empresa) return <div className="p-8">Empresa não encontrada.</div>;

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <main className="flex-grow container mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-slate-900">{empresa.nome}</h1>
          <p className="text-slate-500">CNPJ/CPF: {empresa.cnpjCpf}</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <h2 className="text-lg font-semibold text-slate-700 mb-2">Total Recebido (CEAP)</h2>
            <p className="text-4xl font-bold text-blue-600">{formatarMoedaBRL(empresa.totalRecebido)}</p>
            <p className="text-slate-500 mt-1">Através de {empresa.quantidadeNotas} notas emitidas</p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <h2 className="text-lg font-semibold text-slate-700 mb-4">Divisão por Partidos</h2>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={empresa.distribuicaoPartidos.slice(0, 8)}
                    dataKey="total"
                    nameKey="partido"
                    cx="50%"
                    cy="50%"
                    outerRadius={60}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {empresa.distribuicaoPartidos.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(val: number) => formatarMoedaBRL(val)} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200 mb-8">
          <h2 className="text-lg font-semibold text-slate-700 mb-4">Top 10 Deputados</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={empresa.topDeputados} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" tickFormatter={(val) => `R$${(val/1000).toFixed(0)}k`} />
                <YAxis dataKey="nomeDeputado" type="category" width={150} tick={{ fontSize: 12 }} />
                <Tooltip formatter={(val: number) => formatarMoedaBRL(val)} />
                <Bar dataKey="total" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-4 border-b border-slate-200">
            <h2 className="text-lg font-semibold text-slate-700">Últimas Notas Fiscais</h2>
          </div>
          <div className="overflow-x-auto table-scrollbar">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Data</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Deputado</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Tipo de Despesa</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">Valor Líquido</th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-slate-500 uppercase tracking-wider">Documento</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-slate-200">
                {notas.map((n, i) => (
                  <tr key={i} className="hover:bg-slate-50">
                    <td className="px-6 py-4 whitespace-nowrap text-slate-500">
                      {n.dataDocumento ? new Date(n.dataDocumento).toLocaleDateString('pt-BR') : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Link to={`/politicos/${n.idDeputado}`} className="text-blue-600 hover:underline">
                        {n.nomeDeputado}
                      </Link>
                    </td>
                    <td className="px-6 py-4 text-slate-700">{n.tipoDespesa}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right font-medium text-slate-900">
                      {formatarMoedaBRL(n.valorLiquido)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      {n.urlDocumento ? (
                        <a href={n.urlDocumento} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">Ver Nota</a>
                      ) : (
                        <span className="text-slate-400">N/A</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
