import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { formatarMoedaBRL } from "../utils/formatters";
import { useSeo } from "../hooks/useSeo";
import { Search, ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";

export default function EmpresasRanking() {
  useSeo({
    title: "Empresas e Fornecedores | QuemVota",
    description: "Ranking das empresas que mais receberam verba pública via cota parlamentar.",
    canonicalUrl: "https://quemvota.com.br/empresas",
  });

  const [empresas, setEmpresas] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [busca, setBusca] = useState("");
  const [sortField, setSortField] = useState<string>("totalRecebido");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  useEffect(() => {
    api.get("/empresas/ranking?limit=100").then(res => {
      setEmpresas(res.data);
      setLoading(false);
    });
  }, []);

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      // Padrão: decrescente para números, crescente para textos
      setSortOrder(field === "nome" || field === "cnpjCpf" ? "asc" : "desc");
    }
  };

  const renderSortIcon = (field: string) => {
    if (sortField !== field) return <ArrowUpDown className="inline ml-1 h-3 w-3 text-slate-400" />;
    return sortOrder === "asc" ? <ArrowUp className="inline ml-1 h-3 w-3 text-blue-600" /> : <ArrowDown className="inline ml-1 h-3 w-3 text-blue-600" />;
  };

  const empresasFiltradas = empresas.filter(emp => 
    (emp.nome && emp.nome.toLowerCase().includes(busca.toLowerCase())) || 
    (emp.cnpjCpf && emp.cnpjCpf.includes(busca))
  );

  const empresasOrdenadas = [...empresasFiltradas].sort((a, b) => {
    let valA = a[sortField];
    let valB = b[sortField];
    
    if (typeof valA === "string") valA = valA.toLowerCase();
    if (typeof valB === "string") valB = valB.toLowerCase();

    if (valA < valB) return sortOrder === "asc" ? -1 : 1;
    if (valA > valB) return sortOrder === "asc" ? 1 : -1;
    return 0;
  });

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <main className="flex-grow container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Fornecedores da Câmara</h1>
        <p className="text-slate-600 mb-6">Explore de forma neutra as 100 empresas e serviços que mais recebem verbas através da Cota para Exercício da Atividade Parlamentar (CEAP).</p>

        {loading ? (
          <p>Carregando...</p>
        ) : (
          <div className="bg-white shadow-sm rounded-lg overflow-hidden border border-slate-200">
            <div className="p-4 border-b border-slate-200 bg-white">
              <div className="relative w-full md:w-96">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="Buscar fornecedor por nome ou CNPJ/CPF..."
                  value={busca}
                  onChange={(e) => setBusca(e.target.value)}
                  className="pl-9 pr-4 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent w-full"
                />
              </div>
            </div>
            <div className="overflow-x-auto table-scrollbar">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50">
                  <tr>
                    <th 
                      className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider cursor-pointer hover:bg-slate-100"
                      onClick={() => handleSort("nome")}
                    >
                      Fornecedor {renderSortIcon("nome")}
                    </th>
                    <th 
                      className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider cursor-pointer hover:bg-slate-100"
                      onClick={() => handleSort("cnpjCpf")}
                    >
                      CNPJ/CPF {renderSortIcon("cnpjCpf")}
                    </th>
                    <th 
                      className="px-6 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider cursor-pointer hover:bg-slate-100"
                      onClick={() => handleSort("totalRecebido")}
                    >
                      Total Recebido {renderSortIcon("totalRecebido")}
                    </th>
                    <th 
                      className="px-6 py-3 text-center text-xs font-medium text-slate-500 uppercase tracking-wider cursor-pointer hover:bg-slate-100"
                      onClick={() => handleSort("quantidadeNotas")}
                    >
                      Notas Emitidas {renderSortIcon("quantidadeNotas")}
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-slate-200">
                  {empresasOrdenadas.length > 0 ? (
                    empresasOrdenadas.map(emp => (
                      <tr key={emp.cnpjCpf} className="hover:bg-slate-50 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap font-medium text-slate-900">
                          <Link to={`/empresas/${encodeURIComponent(emp.cnpjCpf.replace(/\//g, '_'))}`} className="text-blue-600 hover:underline">{emp.nome}</Link>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-slate-500">{emp.cnpjCpf}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-right font-medium text-slate-700">{formatarMoedaBRL(emp.totalRecebido)}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-center text-slate-500">{emp.quantidadeNotas}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={4} className="px-6 py-8 text-center text-slate-500">
                        Nenhum fornecedor encontrado.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
