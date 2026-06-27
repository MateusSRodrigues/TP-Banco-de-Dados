# 🚦 Análise de Acidentes de Trânsito em Belo Horizonte

Este repositório contém o projeto final da disciplina de Banco de Dados. O objetivo principal foi realizar o ciclo completo de dados: desde a modelagem conceitual e relacional, passando pela ingestão e limpeza (ETL) em um banco de dados analítico, até a Análise Exploratória de Dados (EDA) dos acidentes de trânsito com vítimas na cidade de Belo Horizonte.

Os dados utilizados são públicos e foram disponibilizados pela BHTRANS (Prefeitura de Belo Horizonte).

---

## 🛠️ Tecnologias Utilizadas

* **Banco de Dados:** [DuckDB](https://duckdb.org/) (escolhido por sua alta performance analítica com arquivos locais).
* **Linguagens:** SQL (DDL e DML) e Python.
* **Bibliotecas Python:**
  * `duckdb` (conexão e queries)
  * `pandas` (manipulação de dataframes para os gráficos)
  * `matplotlib` e `seaborn` (visualização de dados)

---

## 📂 Estrutura do Projeto

Para que os scripts funcionem corretamente, o repositório foi organizado da seguinte forma:

```text
├── data/
│   ├── raw/                  # Coloque os arquivos CSV originais da BHTRANS aqui (si-bol, si-log, etc.)
│   └── processed/            # Onde o arquivo 'acidentes_transito.duckdb' será gerado automaticamente
├── docs/                     # Diagramas ER, Dicionário de Dados e o Relatório Técnico
├── scripts/
│   ├── bd.py                 # Script para criar as tabelas (DDL) e ingerir os CSVs (Carga/Limpeza)
│   └── consultas.py          # Script com as queries SQL avançadas e geração dos gráficos (EDA)
└── README.md
