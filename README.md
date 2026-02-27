<div align="center">

<img src="https://img.shields.io/badge/Status-Em%20Desenvolvimento-yellow?style=for-the-badge" />
<img src="https://img.shields.io/badge/Licença-GPL--3.0-blue?style=for-the-badge" />
<img src="https://img.shields.io/badge/PRs-Bem--vindos-brightgreen?style=for-the-badge" />

# 🗳️ QuemVota

**Transparência parlamentar ao alcance de todos.**

O QuemVota é uma plataforma web que agrega dados públicos da API da Câmara dos Deputados e os apresenta de forma clara, acessível e sem viés político. Saiba como seus representantes votam, o que gastam e quantos dias trabalham — tudo em um só lugar.

[Ver Demo](quemvota.com.br) · [Reportar Bug](https://github.com/WrongProvider/quemVota/issues) · [Sugerir Funcionalidade](https://github.com/WrongProvider/quemVota/issues)

</div>

---

## 📋 Sumário

- [Sobre o Projeto](#-sobre-o-projeto)
- [Funcionalidades](#-funcionalidades)
- [Stack Tecnológica](#-stack-tecnológica)
- [Arquitetura](#-arquitetura)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação e Execução](#-instalação-e-execução)
- [Variáveis de Ambiente](#-variáveis-de-ambiente)
- [Fontes de Dados](#-fontes-de-dados)
- [Princípios e Metodologia](#-princípios-e-metodologia)
- [Contribuindo](#-contribuindo)
- [Licença](#-licença)

---

## 📖 Sobre o Projeto

O QuemVota nasce de uma pergunta simples:

> **Como os parlamentares votam, na prática?**

A plataforma consome dados oficiais e públicos da API da Câmara dos Deputados e os transforma em visualizações intuitivas, permitindo que qualquer cidadão acompanhe a atuação de seus representantes sem precisar navegar por portais governamentais complexos.

O projeto não emite julgamentos políticos, não atribui rótulos ideológicos e não produz rankings subjetivos. Apenas **dados descritivos, com fontes rastreáveis**.

---

## ✨ Funcionalidades

- 🗳️ **Histórico de votações nominais** — veja como cada deputado votou em cada proposição
- 💸 **Gastos parlamentares** — visualize o uso da cota parlamentar por deputado
- 📅 **Presença e assiduidade** — acompanhe quantos dias o parlamentar compareceu às sessões
- 📝 **Autoria de projetos** — descubra quais proposições foram apresentadas por cada deputado
- 🏛️ **Filiação partidária** — histórico de partidos de cada parlamentar
- 🔍 **Classificação temática de proposições** — categorização técnica baseada no assunto principal
- 📊 **Estatísticas descritivas** — percentuais de presença, alinhamento partidário e distribuição de votos

---

## 🛠️ Stack Tecnológica

| Camada | Tecnologia |
|--------|-----------|
| **Frontend** | React 18 + TypeScript + Vite |
| **Backend** | Python + FastAPI |
| **Banco de Dados** | PostgreSQL |
| **Coleta de Dados** | Jobs assíncronos (Python) |
| **Fonte de Dados** | API de Dados Abertos da Câmara dos Deputados |

---

## 🏗️ Arquitetura

```
quemVota/
├── app/
│   ├── frontend/          # Aplicação React + Vite
│   │   ├── src/
│   │   │   ├── components/
│   │   │   ├── pages/
│   │   │   └── services/
│   │   └── package.json
│   └── backend/           # API FastAPI
│       ├── routers/       # Endpoints da API
│       ├── models/        # Modelos do banco de dados
│       ├── schemas/       # Schemas Pydantic
│       ├── services/      # Lógica de negócio e coleta de dados
│       └── main.py
├── LICENSE
└── README.md
```

---

## 📦 Pré-requisitos

Certifique-se de ter instalado:

- [Node.js](https://nodejs.org/) >= 18.x
- [Python](https://www.python.org/) >= 3.10
- [PostgreSQL](https://www.postgresql.org/) >= 14
- [pip](https://pip.pypa.io/) ou [uv](https://github.com/astral-sh/uv)

---

## 🚀 Instalação e Execução

### 1. Clone o repositório

```bash
git clone https://github.com/WrongProvider/quemVota.git
cd quemVota
```

### 2. Configure o banco de dados

Crie um banco de dados PostgreSQL, utilize os schemas em pydantic para estruturar o banco, (futuramente disponibilizarei um dump exemplo)

```bash
createdb quemvota
psql quemvota < dump-quemvota-*.sql
```

### 3. Backend (FastAPI)

```bash
cd app/backend

# Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt

# Configure as variáveis de ambiente (veja a seção abaixo)
cp .env.example .env

# Execute o servidor
uvicorn main:app --reload
```

A API estará disponível em: `http://localhost:8000`  
Documentação automática (Swagger): `http://localhost:8000/docs`

### 4. Frontend (React + Vite)

```bash
cd app/frontend

# Instale as dependências
npm install

# Configure as variáveis de ambiente
cp .env.example .env

# Execute em modo de desenvolvimento
npm run dev
```

O frontend estará disponível em: `http://localhost:5173`

---

## 🔐 Variáveis de Ambiente

### Backend (`.env`)

```env
# Banco de Dados
DATABASE_URL=postgresql://usuario:senha@localhost:5432/quemvota

# API
SECRET_KEY=sua_chave_secreta
DEBUG=True
```

### Frontend (`.env`)

```env
VITE_API_URL=http://localhost:8000
```

> ⚠️ Nunca commite arquivos `.env` com credenciais reais. Adicione-os ao `.gitignore`.

---

## 📊 Fontes de Dados

Todos os dados utilizados são **públicos e oficiais**:

| Fonte | Descrição |
|-------|-----------|
| [API da Câmara dos Deputados](https://dadosabertos.camara.leg.br/swagger/api.html) | Votações nominais, deputados, proposições, gastos e presença |

Cada registro exibido na plataforma inclui data, identificação da proposição e link direto para a fonte oficial.

---

## 🧠 Princípios e Metodologia

O QuemVota segue um conjunto claro de princípios:

- **Dados acima de narrativas** — apenas fatos verificáveis são apresentados
- **Transparência metodológica** — a forma como os dados são processados é pública
- **Neutralidade descritiva** — sem rótulos ideológicos ou rankings subjetivos
- **Reprodutibilidade** — qualquer pessoa pode verificar os dados nas fontes originais
- **Rastreabilidade** — todo dado tem origem identificada e linkável

As classificações temáticas são **inferências técnicas** baseadas no assunto da proposição, sem julgamento de valor.

> O QuemVota descreve comportamentos observáveis. Não atribui intenções, motivações ou valores pessoais a nenhum parlamentar.

---

## 🤝 Contribuindo

Contribuições são muito bem-vindas! Para contribuir:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/minha-feature`)
3. Faça commit das suas alterações (`git commit -m 'feat: adiciona minha feature'`)
4. Faça push para a branch (`git push origin feature/minha-feature`)
5. Abra um Pull Request

Caso encontre inconsistências nos dados, abra uma [issue](https://github.com/WrongProvider/quemVota/issues) com a fonte oficial de referência.

---

## 📄 Licença

Distribuído sob a licença **GPL-3.0**. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

<div align="center">
  Feito com ❤️ para promover transparência pública no Brasil.
</div>