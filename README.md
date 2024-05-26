# Dashboard de Vendas Globais

Este projeto realiza a análise, limpeza e transformação de um conjunto de dados de vendas online, culminando na criação de um banco de dados PostgreSQL e dashboards interativos com Power BI e Streamlit.

## Bibliotecas Utilizadas

- `pandas`: Manipulação e análise de dados
- `re`: Operações com expressões regulares
- `sklearn.feature_extraction.text.TfidfVectorizer`: Vetorização de descrições de produtos
- `sklearn.cluster.KMeans`: Algoritmos de clusterização
- `sqlalchemy.create_engine`: Conexão com banco de dados SQL
- `matplotlib.pyplot` e `seaborn`: Visualizações de dados

## Descrição do Conjunto de Dados

- `NumeroFatura`: Número da fatura
- `CodigoProduto`: Código do produto
- `Descricao`: Descrição do produto
- `Quantidade`: Quantidade de produtos vendidos
- `DataFatura`: Data e hora da fatura
- `PrecoUnitario`: Preço unitário do produto
- `IDCliente`: Identificação única do cliente
- `Pais`: País do cliente

## Limpeza e Transformação de Dados

1. **Renomeação das Colunas**: Colunas renomeadas para o português.
2. **Tratamento de Valores Ausentes e Duplicados**: Exclusão de valores ausentes e duplicados.
3. **Clusterização**: Normalização e vetorização de descrições de produtos com TF-IDF, seguido de K-means para agrupar produtos em 8 categorias.
4. **Análise de Quantidades e Preços**: Identificação de erros e criação de colunas `Venda` e `Devolucao`.
5. **Colunas Adicionais**: `ValorTotal` e `CategoriaPreco`.

## Banco de Dados SQL

Os dados foram organizados em três DataFrames principais e salvos em arquivos CSV para importação no PostgreSQL:
1. **Clientes**
2. **Produtos**
3. **Itens de Fatura**

## Ferramentas Utilizadas

- **PostgreSQL**: Banco de dados local.
- **DBeaver**: Popular tabelas e consultas SQL.
- **ODBC e Power BI**: Transferência de dados e criação de dashboard.
- **Streamlit**: Dashboard interativo para visualização de insights.

## Conclusão

Este projeto resultou em uma infraestrutura robusta para análise de vendas globais, proporcionando uma base sólida para futuras análises e tomada de decisões estratégicas.

## Como Executar

1. Clone o repositório
2. Instale as dependências
3. Execute o script em Streamlit: `streamlit run app.py`


