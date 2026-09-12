import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { formatarMoedaBRL } from "../utils/formatters";
import { useSeo } from "../hooks/useSeo";

export default function EmpresasRanking() {
  useSeo({
    title: "Empresas e Fornecedores | QuemVota",
    description: "Ranking das empresas que mais receberam verba pública via cota parlamentar.",
    canonicalUrl: "https://quemvota.com.br/empresas",
  });

  const [empresas, setEmpresas] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/empresas/ranking?limit=100").then(res => {
      setEmpresas(res.data);
      setLoading(false);
    });
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <main className="flex-grow container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Fornecedores da Câmara</h1>
        <p className="text-slate-600 mb-6">Explore de forma neutra as empresas e serviços que mais recebem verbas através da Cota para Exercício da Atividade Parlamentar (CEAP).</p>

        {loading ? (
          <p>Carregando...</p>
        ) : (
          <div className="bg-white shadow-sm rounded-lg overflow-hidden border border-slate-200">
            <div className="overflow-x-auto table-scrollbar">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Fornecedor</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">CNPJ/CPF</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">Total Recebido</th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-slate-500 uppercase tracking-wider">Notas Emitidas</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-slate-200">
                  {empresas.map(emp => (
                    <tr key={emp.cnpjCpf} className="hover:bg-slate-50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap font-medium text-slate-900">
                        <Link to={`/empresas/${emp.cnpjCpf}`} className="text-blue-600 hover:underline">{emp.nome}</Link>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-slate-500">{emp.cnpjCpf}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-right font-medium text-slate-700">{formatarMoedaBRL(emp.totalRecebido)}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-center text-slate-500">{emp.quantidadeNotas}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
