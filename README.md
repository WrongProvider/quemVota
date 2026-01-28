# QuemVota

**QuemVota** é uma plataforma de visualização de dados públicos sobre a atuação legislativa no Brasil, com foco em votações nominais da Câmara dos Deputados.

O projeto tem como objetivo **facilitar o acesso, a compreensão e a auditoria** de informações oficiais, sem emitir julgamentos de valor, opiniões políticas ou classificações ideológicas.

---

## 🎯 Objetivo do Projeto

O QuemVota existe para responder a uma pergunta simples, com base em dados verificáveis:

> **Como os parlamentares votam, na prática?**

A plataforma apresenta:
- registros oficiais de votos
- informações institucionais
- estatísticas descritivas

Sempre com **fontes públicas e metodologia transparente**.

---

## 📌 Escopo do MVP

### Incluído
- Câmara dos Deputados
- Legislatura atual
- Votações nominais
- Presença em votações
- Autoria de projetos
- Filiação partidária
- Classificação técnica de temas

### Fora do escopo (neste estágio)
- Avaliações morais ou políticas
- Rótulos ideológicos (ex: esquerda/direita)
- Rankings de “melhor” ou “pior”
- Análise de discurso ou redes sociais
- Conteúdo opinativo ou editorial

---

## 🧠 Princípios do Projeto

- **Dados acima de narrativas**
- **Transparência metodológica**
- **Neutralidade descritiva**
- **Reprodutibilidade**
- **Rastreabilidade das fontes**

O QuemVota descreve comportamentos observáveis, não intenções, motivações ou valores pessoais.

---

## 📊 Fontes de Dados

Todos os dados utilizados são públicos e oficiais, incluindo:

- API de Dados Abertos da Câmara dos Deputados
- Registros oficiais de votações nominais
- Informações institucionais publicadas pela Câmara

Cada voto exibido na plataforma possui:
- data
- identificação da proposição
- link direto para a fonte oficial

---

## 🧮 Metodologia (resumo)

- Os dados são coletados automaticamente a partir de fontes oficiais.
- Votações são armazenadas com seus identificadores originais.
- Projetos recebem **uma classificação temática técnica**, baseada no assunto principal da proposição.
- Estatísticas apresentadas são **descritivas**, como:
  - percentual de presença
  - distribuição de votos por tema
  - alinhamento com orientação partidária

Uma descrição detalhada da metodologia está disponível na plataforma.

---

## ⚖️ Disclaimer

O QuemVota:

- Não realiza avaliações morais, políticas ou pessoais de parlamentares.
- Não atribui intenções, valores ou motivações a votos registrados.
- Não substitui a consulta às fontes oficiais.
- Reflete informações conforme disponibilizadas pelos órgãos públicos, sujeitas a inconsistências de origem.

As classificações temáticas e estatísticas apresentadas são inferências técnicas baseadas em dados públicos.

---

## 🛠️ Stack Tecnológica (planejada)

- **Backend**: Python, FastAPI
- **Banco de Dados**: PostgreSQL
- **Coleta de Dados**: Jobs assíncronos
- **Frontend**: Next.js / React
- **Infraestrutura**: Deploy simplificado (cloud)

---

## 🚧 Status do Projeto

🔧 Em desenvolvimento (MVP)

O projeto encontra-se em fase inicial, com foco na estruturação do pipeline de dados e na visualização básica das informações.

---

## 📬 Contato e Retificações

Caso identifique inconsistências ou deseje solicitar correções baseadas em fontes oficiais, utilize o canal de contato disponibilizado na plataforma.

---

## 📄 Licença

Este projeto respeita as normas de uso de dados públicos e a legislação brasileira vigente.
