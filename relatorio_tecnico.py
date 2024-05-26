import streamlit as st

# Título e introdução
st.title('Relatório Técnico: Análise e Transformação de Dados para Criação de Dashboard de Vendas Globais')

# Introdução
st.markdown("""
Este relatório descreve o processo de análise, limpeza e transformação de um conjunto de dados de vendas online, culminando na criação de um banco de dados PostgreSQL, utilização de ferramentas como DBeaver e ODBC, e a construção de dashboards utilizando Power BI e Streamlit.
""")

# Bibliotecas Utilizadas
st.header('Bibliotecas Utilizadas')
st.markdown("""
Foram utilizadas as seguintes bibliotecas no projeto:
- `pandas`: Para manipulação e análise de dados.
- `re`: Para operações com expressões regulares.
- `sklearn.feature_extraction.text.TfidfVectorizer`: Para vetorizar descrições de produtos.
- `sklearn.cluster.KMeans`: Para aplicar algoritmos de clusterização.
- `sqlalchemy.create_engine`: Para conexão com o banco de dados SQL.
- `matplotlib.pyplot` e `seaborn`: Para visualizações de dados.
""")

# Descrição do Conjunto de Dados
st.header('Descrição do Conjunto de Dados')
st.markdown("""
O conjunto de dados inicial possui as seguintes colunas:
- `NumeroFatura`: Número da fatura que identifica a transação.
- `CodigoProduto`: Código do produto vendido.
- `Descricao`: Descrição do produto vendido.
- `Quantidade`: Quantidade de produtos vendidos na transação.
- `DataFatura`: Data e hora em que a fatura foi gerada.
- `PrecoUnitario`: Preço unitário do produto vendido.
- `IDCliente`: Identificação única do cliente.
- `Pais`: País onde o cliente está localizado.
""")

# Limpeza e Transformação de Dados
st.header('Limpeza e Transformação de Dados')
st.markdown("""
1. **Renomeação das Colunas**:
   As colunas foram renomeadas para o português para melhor entendimento.

2. **Tratamento de Valores Ausentes e Duplicados**:
   - Excluímos valores ausentes nas colunas `Descricao` e `IDCliente` para garantir a integridade das análises.
   - Valores duplicados foram removidos para evitar distorções.

3. **Limpeza de Textos e Clusterização**:
   - As descrições dos produtos foram normalizadas e vetorizadas usando TF-IDF.
   - Aplicamos o método de K-means para agrupar produtos em 8 categorias distintas com base nas suas descrições.
   - As categorias foram nomeadas conforme características comuns dos produtos, facilitando a visualização e análise subsequente.

4. **Análise de Quantidades e Preços**:
   - Quantidades e preços unitários foram analisados para identificar possíveis erros (ex.: preços zerados).
   - Transações com quantidade negativa foram identificadas como devoluções, e novas colunas (`Venda` e `Devolucao`) foram criadas.

5. **Criação de Colunas Adicionais**:
   - Colunas como `ValorTotal` (quantidade * preço unitário) e `CategoriaPreco` (classificação de preços: Barato, Moderado, Caro) foram adicionadas para enriquecer as análises.
""")

# Preparação dos Dados para Banco de Dados SQL
st.header('Preparação dos Dados para Banco de Dados SQL')
st.markdown("""
Os dados foram organizados em três DataFrames principais:
1. **Clientes**: Informações dos clientes.
2. **Produtos**: Informações dos produtos.
3. **Itens de Fatura**: Detalhes das transações, incluindo vendas e devoluções.

Esses DataFrames foram salvos em arquivos CSV para posterior importação no banco de dados PostgreSQL.
""")

# Construção do Banco de Dados e Ferramentas Utilizadas
st.header('Construção do Banco de Dados e Ferramentas Utilizadas')
st.markdown("""
- **PostgreSQL**: O banco de dados foi construído localmente, utilizando DBeaver para popular as tabelas e realizar consultas SQL.
- **ODBC e Power BI**: Utilizamos ODBC para transferir dados do PostgreSQL para o Power BI, onde foi construído um dashboard de vendas globais.
- **Streamlit**: Com base nas consultas SQL, um dashboard interativo foi criado em Streamlit para visualização de insights.
""")

# Conclusão
st.header('Conclusão')
st.markdown("""
O processo descrito permitiu uma análise detalhada e transformação dos dados, facilitando a criação de visualizações úteis para o negócio. A integração com PostgreSQL, Power BI e Streamlit demonstrou a viabilidade e eficácia das ferramentas utilizadas para gerar insights acionáveis.

A implementação desses passos resultou em uma infraestrutura robusta para análise de vendas globais, proporcionando uma base sólida para futuras análises e tomada de decisões estratégicas.
""")
