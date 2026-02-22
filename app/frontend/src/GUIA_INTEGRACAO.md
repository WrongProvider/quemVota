# 📘 Guia de Integração - Rankings Frontend

## 📁 Estrutura de Arquivos Criados

```
src/
├── api/
│   └── rankings.api.ts          # Funções de chamada à API + Interfaces TypeScript
├── hooks/
│   └── useRankings.ts           # React Query hooks para rankings
├── services/
│   └── ranking.service.ts       # Lógica de negócio e transformação de dados
└── pages/
    └── Rankings.tsx             # Componente principal da página
```

---

## 🎯 O que foi implementado

### 1️⃣ **rankings.api.ts** - Camada de API
✅ **5 Interfaces TypeScript** mapeando os schemas do backend:
- `RankingDespesaPolitico` - Dados de gastos
- `RankingEmpresaLucro` - Empresas que receberam recursos
- `RankingDiscursoPolitico` - Discursos com temas
- `RankingPerformancePolitico` - Performance geral (score)
- `StatsGeral` - Estatísticas do dashboard

✅ **5 Funções de API**:
- `getRankingDespesas()` - GET /ranking/despesa_politico
- `getRankingLucroEmpresas()` - GET /ranking/lucro_empresas
- `getRankingDiscursos()` - GET /ranking/discursos
- `getRankingPerformance()` - GET /ranking/performance_politicos
- `getStatsGeral()` - GET /ranking/stats/geral

### 2️⃣ **useRankings.ts** - React Query Hooks
✅ **5 Hooks customizados**:
- `useRankingDespesas(params)` - Com filtros (q, uf, limit, offset)
- `useRankingLucroEmpresas(params)`
- `useRankingDiscursos(params)`
- `useRankingPerformance()` - Ranking completo de performance
- `useStatsGeral()` - Para dashboard/home

✅ **Cache otimizado**:
- 30 minutos de staleTime
- 2 horas de garbage collection
- Aproveitando o cache de 24h do backend

### 3️⃣ **ranking.service.ts** - Camada de Serviço
✅ **6 Classes de serviço**:

**PerformanceRankingService**
- `getPerformanceRanking()` - Retorna top3 e resto separados
- `getStats()` - Estatísticas gerais
- `getPoliticoPosition(id)` - Posição no ranking
- `filterByScore(min, max)` - Filtra por faixa de score

**DespesaRankingService**
- `getDespesasRanking(filters)` - Com filtros aplicados
- `getTopGastadores(limit)` - Top N gastadores
- `calcularEstatisticas(data)` - Média, total, maior, menor
- `formatarValor(valor)` - Formatação monetária

**EconomiaRankingService**
- `getMaisEconomicos(filters)` - Inverte ordem (menores gastos)
- `calcularPercentualEconomia()` - % baseado na cota

**DiscursoRankingService**
- `getDiscursosRanking()`
- `getTemasMaisFrequentes(topN)` - Agrega temas de todos
- `filtrarPorTema(tema)` - Busca por tema específico

**EmpresaRankingService**
- `getEmpresasRanking()`
- `getTopEmpresas(limit)`
- `calcularEstatisticas(data)`
- `formatarCNPJ(cnpj)` - Formatação com máscara

**FilterService**
- Lista de UFs brasileiras
- Validação de UF
- Normalização de busca (remove acentos)
- Build de query strings

**FormatService**
- `formatarMoeda()` - R$ 1.234,56
- `formatarNumero()` - 1.234
- `formatarPercentual()` - 12.34%
- `truncarTexto()` - Adiciona reticências

### 4️⃣ **Rankings.tsx** - Componente Principal
✅ **Refatorado para usar os novos hooks**
✅ **5 Tabs de ranking**:
- Performance (com pódio top 3)
- Maiores Gastos
- Mais Econômicos
- Mais Discursos (com temas)
- Empresas Beneficiadas

✅ **Filtros dinâmicos**:
- Busca por nome
- Filtro por UF
- Limpar filtros

✅ **Cards visuais**:
- `PodiumCard` - Top 3 com medalhas 🥇🥈🥉
- `RankingCard` - Lista de ranking
- `DiscursoCard` - Com temas em tags
- `EmpresaCard` - Com CNPJ e valor

✅ **Estados de UI**:
- `LoadingState` - Spinner animado
- `ErrorState` - Mensagem de erro
- `EmptyState` - Sem resultados
- `StatCard` - Cards de estatísticas

---

## 🚀 Como Usar

### Exemplo 1: Página de Rankings (já implementado)
```tsx
import { Rankings } from './pages/Rankings'

function App() {
  return <Rankings />
}
```

### Exemplo 2: Dashboard com Stats
```tsx
import { useStatsGeral } from './hooks/useRankings'

function Dashboard() {
  const { data, isLoading } = useStatsGeral()
  
  if (isLoading) return <div>Carregando...</div>
  
  return (
    <div>
      <h1>Média Global: {data?.media_global}</h1>
      <p>Total Parlamentares: {data?.total_parlamentares}</p>
      
      {/* Top 3 */}
      {data?.top_3.map(politico => (
        <div key={politico.id}>
          {politico.nome} - Score: {politico.score}
        </div>
      ))}
    </div>
  )
}
```

### Exemplo 3: Busca com Filtros
```tsx
import { useRankingDespesas } from './hooks/useRankings'

function BuscaPoliticos() {
  const [uf, setUf] = useState("SP")
  const [busca, setBusca] = useState("")
  
  const { data, isLoading } = useRankingDespesas({
    uf,
    q: busca,
    limit: 50
  })
  
  // Query keys diferentes = cache separado por filtro
  // Trocar filtros faz nova requisição automaticamente
}
```

### Exemplo 4: Usando Serviços
```tsx
import { DespesaRankingService } from './services/ranking.service'

function ExibirEstatisticas({ data }) {
  const stats = DespesaRankingService.calcularEstatisticas(data)
  
  return (
    <div>
      <p>Total: {DespesaRankingService.formatarValor(stats.total)}</p>
      <p>Média: {DespesaRankingService.formatarValor(stats.media)}</p>
      <p>Maior: {DespesaRankingService.formatarValor(stats.maior)}</p>
    </div>
  )
}
```

---

## 🔧 Configuração Necessária

### 1. Instalar Dependências
```bash
npm install @tanstack/react-query axios
```

### 2. Configurar React Query Provider
```tsx
// main.tsx ou App.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      {/* Suas rotas */}
    </QueryClientProvider>
  )
}
```

### 3. Configurar Variável de Ambiente
```env
# .env
VITE_API_URL=http://localhost:8000/api
```

---

## 📊 Endpoints do Backend (Referência)

| Endpoint | Método | Descrição | Cache |
|----------|--------|-----------|-------|
| `/ranking/despesa_politico` | GET | Ranking de gastos | 24h |
| `/ranking/lucro_empresas` | GET | Empresas beneficiadas | 24h |
| `/ranking/discursos` | GET | Ranking de discursos + temas | 24h |
| `/ranking/performance_politicos` | GET | Ranking geral (score) | 24h |
| `/ranking/stats/geral` | GET | Estatísticas + top 50 | 24h |

### Parâmetros Disponíveis

**despesa_politico:**
- `q` (string) - Busca por nome
- `uf` (string) - Filtro por estado (AC, SP, etc)
- `limit` (number) - Quantidade de resultados (max 100)
- `offset` (number) - Paginação

**lucro_empresas:**
- `limit` (number) - Quantidade de resultados (max 100)
- `offset` (number) - Paginação

**discursos:**
- `limit` (number) - Quantidade de resultados (max 500)
- `offset` (number) - Paginação

---

## 🎨 Personalização

### Alterar cores do tema
No `Rankings.tsx`, procure por cores hexadecimais:
- `#1E88E5` - Azul principal
- `#F59E0B` - Amarelo/Dourado (top 3)
- `#10B981` - Verde (economia)
- `#EF4444` - Vermelho (gastos)

### Alterar limites de cache
No `useRankings.ts`:
```typescript
const CACHE_CONFIG = {
  staleTime: 1000 * 60 * 30,      // 30 minutos
  gcTime: 1000 * 60 * 60 * 2,     // 2 horas
}
```

### Adicionar novo ranking
1. Criar interface em `rankings.api.ts`
2. Criar função GET em `rankings.api.ts`
3. Criar hook em `useRankings.ts`
4. Criar classe de serviço em `ranking.service.ts`
5. Adicionar tab e componente em `Rankings.tsx`

---

## ✅ Vantagens da Arquitetura

✨ **Separação de Responsabilidades**
- API: apenas chamadas HTTP
- Hooks: gerenciamento de estado/cache
- Services: lógica de negócio
- Components: apenas UI

✨ **Reusabilidade**
- Hooks podem ser usados em múltiplos componentes
- Serviços são independentes da UI
- Interfaces TypeScript garantem consistência

✨ **Performance**
- Cache automático do React Query
- Invalidação inteligente por query key
- Aproveitamento do cache do backend (24h)

✨ **Manutenibilidade**
- Código organizado e documentado
- Fácil adicionar novos rankings
- Testes isolados por camada

---

## 🐛 Troubleshooting

### Erro: "Cannot find module '@tanstack/react-query'"
```bash
npm install @tanstack/react-query
```

### Erro: "VITE_API_URL is not defined"
Crie arquivo `.env` na raiz do projeto com:
```
VITE_API_URL=http://localhost:8000/api
```

### Rankings não aparecem
1. Verifique se o backend está rodando
2. Abra DevTools > Network e veja as requisições
3. Verifique os logs do console

### Cache não está funcionando
1. Verifique se `QueryClientProvider` está no App
2. Confirme que as query keys estão corretas
3. Use React Query DevTools para debug:
```tsx
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

<QueryClientProvider client={queryClient}>
  <App />
  <ReactQueryDevtools />
</QueryClientProvider>
```

---

## 📚 Próximos Passos Sugeridos

1. ✅ Implementar paginação completa nos rankings
2. ✅ Adicionar gráficos com recharts ou chartjs
3. ✅ Criar página de comparação entre políticos
4. ✅ Adicionar export para CSV/Excel
5. ✅ Implementar busca avançada com múltiplos filtros
6. ✅ Adicionar modo escuro (dark mode)
7. ✅ Criar versão mobile otimizada

---

## 📝 Checklist de Integração

- [ ] Instalar dependências (`@tanstack/react-query`, `axios`)
- [ ] Configurar `QueryClientProvider`
- [ ] Configurar `.env` com `VITE_API_URL`
- [ ] Copiar `rankings.api.ts` para `src/api/`
- [ ] Copiar `useRankings.ts` para `src/hooks/`
- [ ] Copiar `ranking.service.ts` para `src/services/`
- [ ] Copiar `Rankings.tsx` para `src/pages/`
- [ ] Adicionar rota no React Router
- [ ] Testar cada tab de ranking
- [ ] Testar filtros de busca e UF
- [ ] Verificar responsividade mobile
- [ ] Testar cache (reload da página)

---

## 🎉 Pronto!

Sua integração está completa! Agora você tem:
- ✅ Tipagem forte com TypeScript
- ✅ Cache otimizado com React Query
- ✅ Código organizado em camadas
- ✅ UI responsiva e moderna
- ✅ 5 tipos de rankings funcionais
- ✅ Filtros dinâmicos
- ✅ Performance otimizada

Qualquer dúvida, consulte os exemplos de uso ou a documentação inline nos arquivos! 🚀
