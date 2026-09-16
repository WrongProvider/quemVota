import re

with open('.worktrees/spec-009-novas-metricas/frontend/src/pages/ComparadorDeputados.tsx', 'r') as f:
    content = f.read()

# Replace Mobile cards
mobile_orig = """                <div className="bg-slate-50 p-2 rounded col-span-2">
                  <span className="block text-slate-500 text-xs uppercase tracking-wider">Presenças Registradas</span>
                  <span className="font-medium">{m.totalPresencas}</span>
                </div>"""

mobile_new = """                <div className="bg-slate-50 p-2 rounded">
                  <span className="block text-slate-500 text-xs uppercase tracking-wider">Presenças</span>
                  <span className="font-medium">{m.totalPresencas}</span>
                </div>
                <div className="bg-slate-50 p-2 rounded">
                  <span className="block text-slate-500 text-xs uppercase tracking-wider">Votos Nominais</span>
                  <span className="font-medium">{m.totalVotosNominais}</span>
                </div>
                <div className="bg-slate-50 p-2 rounded">
                  <span className="block text-slate-500 text-xs uppercase tracking-wider">Fidelidade</span>
                  <span className="font-medium">{m.fidelidadePartidaria != null ? `${m.fidelidadePartidaria.toFixed(1)}%` : "N/A"}</span>
                </div>
                <div className="bg-slate-50 p-2 rounded">
                  <span className="block text-slate-500 text-xs uppercase tracking-wider">Relatorias</span>
                  <span className="font-medium">{m.totalRelatorias}</span>
                </div>
                <div className="bg-slate-50 p-2 rounded">
                  <span className="block text-slate-500 text-xs uppercase tracking-wider">Discursos</span>
                  <span className="font-medium">{m.totalDiscursos}</span>
                </div>"""

content = content.replace(mobile_orig, mobile_new)

# Replace Desktop headers
desktop_headers_orig = """                  <th 
                    className="px-6 py-3 text-center text-xs font-medium text-slate-500 uppercase tracking-wider cursor-pointer hover:bg-slate-100"
                    onClick={() => sortData("totalPresencas")}
                  >
                    Presenças {ordenacao === "totalPresencas" && (direcao === "asc" ? "↑" : "↓")}
                  </th>"""

desktop_headers_new = """                  <th 
                    className="px-6 py-3 text-center text-xs font-medium text-slate-500 uppercase tracking-wider cursor-pointer hover:bg-slate-100"
                    onClick={() => sortData("totalPresencas")}
                  >
                    Presenças {ordenacao === "totalPresencas" && (direcao === "asc" ? "↑" : "↓")}
                  </th>
                  <th 
                    className="px-6 py-3 text-center text-xs font-medium text-slate-500 uppercase tracking-wider cursor-pointer hover:bg-slate-100"
                    onClick={() => sortData("totalVotosNominais")}
                  >
                    Votos Nominais {ordenacao === "totalVotosNominais" && (direcao === "asc" ? "↑" : "↓")}
                  </th>
                  <th 
                    className="px-6 py-3 text-center text-xs font-medium text-slate-500 uppercase tracking-wider cursor-pointer hover:bg-slate-100"
                    onClick={() => sortData("fidelidadePartidaria")}
                  >
                    Fidelidade {ordenacao === "fidelidadePartidaria" && (direcao === "asc" ? "↑" : "↓")}
                  </th>
                  <th 
                    className="px-6 py-3 text-center text-xs font-medium text-slate-500 uppercase tracking-wider cursor-pointer hover:bg-slate-100"
                    onClick={() => sortData("totalRelatorias")}
                  >
                    Relatorias {ordenacao === "totalRelatorias" && (direcao === "asc" ? "↑" : "↓")}
                  </th>
                  <th 
                    className="px-6 py-3 text-center text-xs font-medium text-slate-500 uppercase tracking-wider cursor-pointer hover:bg-slate-100"
                    onClick={() => sortData("totalDiscursos")}
                  >
                    Discursos {ordenacao === "totalDiscursos" && (direcao === "asc" ? "↑" : "↓")}
                  </th>"""

content = content.replace(desktop_headers_orig, desktop_headers_new)

# Replace Desktop rows
desktop_rows_orig = """                    <td className="px-6 py-4 whitespace-nowrap text-center text-slate-700">
                      {m.totalPresencas}
                    </td>"""

desktop_rows_new = """                    <td className="px-6 py-4 whitespace-nowrap text-center text-slate-700">
                      {m.totalPresencas}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center text-slate-700">
                      {m.totalVotosNominais}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center text-slate-700">
                      {m.fidelidadePartidaria != null ? `${m.fidelidadePartidaria.toFixed(1)}%` : "N/A"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center text-slate-700">
                      {m.totalRelatorias}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center text-slate-700">
                      {m.totalDiscursos}
                    </td>"""

content = content.replace(desktop_rows_orig, desktop_rows_new)

with open('.worktrees/spec-009-novas-metricas/frontend/src/pages/ComparadorDeputados.tsx', 'w') as f:
    f.write(content)

