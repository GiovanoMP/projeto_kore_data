import streamlit as st
import pandas as pd

# Carregar os dataframes
clientes = pd.read_csv('clientes.csv')
itens_fatura = pd.read_csv('itens_fatura.csv')
produtos = pd.read_csv('produtos.csv')

# Converter a coluna 'DataFatura' para datetime
itens_fatura['DataFatura'] = pd.to_datetime(itens_fatura['DataFatura'], errors='coerce')

# Filtrar registros com datas válidas
itens_fatura = itens_fatura.dropna(subset=['DataFatura'])

# Garantir que os nomes das colunas estejam corretos
clientes.rename(columns=lambda x: x.strip(), inplace=True)
itens_fatura.rename(columns=lambda x: x.strip(), inplace=True)
produtos.rename(columns=lambda x: x.strip(), inplace=True)

# Verificar se a coluna 'Categoria' existe em itens_fatura e adicionar se necessário
if 'Categoria' not in itens_fatura.columns:
    itens_fatura = itens_fatura.merge(produtos[['CodigoProduto', 'Categoria']], on='CodigoProduto', how='left')

# Funções auxiliares para calcular os indicadores
# ... (Suas funções de cálculo de indicadores)

# Título do app
st.title('Relatório de Vendas')

# --- Filtros ---
st.sidebar.header("Filtros")

# Seleção de datas para filtrar os dados
start_date = st.sidebar.date_input("Data Inicial", itens_fatura['DataFatura'].min().date())
end_date = st.sidebar.date_input("Data Final", itens_fatura['DataFatura'].max().date())

# Seleção de categorias de preço com descrição
categoria_preco = st.sidebar.radio(
    'Escolha uma Categoria de Preço:',
    ['Nenhum', 'Barato (abaixo de 5,00)', 'Moderado (5,00 a 20,00)', 'Caro (acima de 20,00)']
)

# Seleção de categoria de produtos
categoria_produto_selecionada = st.sidebar.selectbox("Categoria de Produto", ['Nenhum'] + list(produtos['Categoria'].unique()))

# Seleção de país
pais_selecionado = st.sidebar.selectbox("País", ['Global'] + list(clientes['Pais'].unique()))

# --- Filtragem de Dados ---

# Filtrar dados por data
itens_fatura_filtrado = itens_fatura[(itens_fatura['DataFatura'].dt.date >= start_date) & (itens_fatura['DataFatura'].dt.date <= end_date)]

# Filtrar dados por categoria de preço
if categoria_preco != 'Nenhum':
    itens_fatura_filtrado = itens_fatura_filtrado.merge(produtos, on='CodigoProduto')
    if categoria_preco == 'Barato (abaixo de 5,00)':
        itens_fatura_filtrado = itens_fatura_filtrado[itens_fatura_filtrado['PrecoUnitario'] < 5]
    elif categoria_preco == 'Moderado (5,00 a 20,00)':
        itens_fatura_filtrado = itens_fatura_filtrado[(itens_fatura_filtrado['PrecoUnitario'] >= 5) & (itens_fatura_filtrado['PrecoUnitario'] <= 20)]
    elif categoria_preco == 'Caro (acima de 20,00)':
        itens_fatura_filtrado = itens_fatura_filtrado[itens_fatura_filtrado['PrecoUnitario'] > 20]

# Filtrar dados por categoria de produto
if categoria_produto_selecionada != 'Nenhum':
    if 'Categoria' not in itens_fatura_filtrado.columns:
        itens_fatura_filtrado = itens_fatura_filtrado.merge(produtos[['CodigoProduto', 'Categoria']], on='CodigoProduto', how='left')
    itens_fatura_filtrado = itens_fatura_filtrado[itens_fatura_filtrado['Categoria'] == categoria_produto_selecionada]

# Filtrar dados por país
if pais_selecionado != 'Global':
    itens_fatura_filtrado = itens_fatura_filtrado.merge(clientes, on='IDCliente')
    itens_fatura_filtrado = itens_fatura_filtrado[itens_fatura_filtrado['Pais'] == pais_selecionado]

# --- Seção de Indicadores ---
st.header('Indicadores de Vendas')
# ... (Seu código para exibir os indicadores)

# --- Seção de Análise Temporal ---
st.header('Análise Temporal')
# ... (Seu código para exibir a análise temporal)
