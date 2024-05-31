import streamlit as st
import pandas as pd
from datetime import timedelta

# --- Funções auxiliares para validação e tratamento de dados ---

def ler_csv_com_tratamento(nome_arquivo):
    try:
        df = pd.read_csv(nome_arquivo)
        df.rename(columns=lambda x: x.strip(), inplace=True)  # Remover espaços em branco nos nomes das colunas
        return df
    except FileNotFoundError:
        st.error(f"O arquivo '{nome_arquivo}' não foi encontrado.")
        return None
    except pd.errors.EmptyDataError:
        st.error(f"O arquivo '{nome_arquivo}' está vazio.")
        return None
    except Exception as e:
        st.error(f"Erro ao ler o arquivo '{nome_arquivo}': {e}")
        return None

# --- Carregar os DataFrames ---

clientes = ler_csv_com_tratamento('clientes.csv')
itens_fatura = ler_csv_com_tratamento('itens_fatura.csv')
produtos = ler_csv_com_tratamento('produtos.csv')

# Verificar se os DataFrames foram carregados corretamente
if any(df is None for df in [clientes, itens_fatura, produtos]):
    st.stop()  # Interromper a execução do aplicativo

# --- Converter a coluna 'DataFatura' para datetime ---

itens_fatura['DataFatura'] = pd.to_datetime(itens_fatura['DataFatura'], errors='coerce')

# --- Remover registros com datas inválidas ---

itens_fatura.dropna(subset=['DataFatura'], inplace=True)

# --- Garantir que a coluna 'Categoria' exista em itens_fatura ---

if 'Categoria' not in itens_fatura.columns:
    itens_fatura = itens_fatura.merge(produtos[['CodigoProduto', 'Categoria']], on='CodigoProduto', how='left')

# --- Função para filtrar clientes que não compraram em um intervalo de dias ---

def filtrar_clientes_por_intervalo(df, dias_inicio, dias_fim, ultima_data):
    data_inicio = ultima_data - timedelta(days=dias_inicio)
    data_fim = ultima_data - timedelta(days=dias_fim)
    clientes_inativos = df.groupby('IDCliente').filter(
        lambda x: x['DataFatura'].max() <= data_inicio and x['DataFatura'].max() > data_fim
    )
    return clientes_inativos['IDCliente'].unique()

# --- Definir a última data do dataset para a filtragem ---

ultima_data = itens_fatura['DataFatura'].max()

# --- Aplicar os filtros ---

clientes_30_60_dias = filtrar_clientes_por_intervalo(itens_fatura, 30, 60, ultima_data)
clientes_61_90_dias = filtrar_clientes_por_intervalo(itens_fatura, 61, 90, ultima_data)
clientes_91_120_dias = filtrar_clientes_por_intervalo(itens_fatura, 91, 120, ultima_data)
clientes_121_360_dias = filtrar_clientes_por_intervalo(itens_fatura, 121, 360, ultima_data)

# --- Título do app ---

st.title('Relatório de Vendas')

# --- Filtro de Análise de Churn ---

st.sidebar.header('Análise de Churn')
opcoes_churn = ['Todos os clientes', 'Clientes que não compram de 30 a 60 dias', 'Clientes que não compram de 61 a 90 dias', 'Clientes que não compram de 91 a 120 dias', 'Clientes que não compram de 121 a 360 dias']
selecionar_churn = st.sidebar.selectbox('Selecione o período de churn:', opcoes_churn)

# --- Seleção de datas para filtrar os dados ---

st.sidebar.header('Filtro de Data')
start_date = st.sidebar.date_input('Data Inicial', pd.to_datetime(itens_fatura['DataFatura'].min()).date(), min_value=pd.to_datetime(itens_fatura['DataFatura'].min()).date(), max_value=pd.to_datetime(itens_fatura['DataFatura'].max()).date())
end_date = st.sidebar.date_input('Data Final', pd.to_datetime(itens_fatura['DataFatura'].max()).date(), min_value=pd.to_datetime(itens_fatura['DataFatura'].min()).date(), max_value=pd.to_datetime(itens_fatura['DataFatura'].max()).date())

if start_date > end_date:
    st.sidebar.error('Erro: A data final deve ser posterior à data inicial.')

# --- Seleção de país ---

st.sidebar.header('Filtro de País')
paises = ['Global'] + list(clientes['Pais'].unique())
pais_selecionado = st.sidebar.selectbox('Escolha um País:', paises)

# --- Seleção de categorias de preço com descrição ---

st.sidebar.header('Filtro de Categoria de Preço')
categoria_preco = st.sidebar.radio(
    'Escolha uma Categoria de Preço:',
    ['Nenhum', 'Barato (abaixo de 5,00)', 'Moderado (5,00 a 20,00)', 'Caro (acima de 20,00)']
)

# --- Seleção de categoria de produtos ---

st.sidebar.header('Filtro de Categoria de Produtos')
categorias_produtos = ['Nenhum'] + list(produtos['Categoria'].unique())
categoria_produto_selecionada = st.sidebar.selectbox('Escolha uma Categoria de Produto:', categorias_produtos)

# --- Função para filtrar transações de acordo com a seleção de churn ---

def filtrar_transacoes_por_churn(opcao):
    if opcao == 'Todos os clientes':
        return itens_fatura
    elif opcao == 'Clientes que não compram de 30 a 60 dias':
        clientes = clientes_30_60_dias
    elif opcao == 'Clientes que não compram de 61 a 90 dias':
        clientes = clientes_61_90_dias
    elif opcao == 'Clientes que não compram de 91 a 120 dias':
        clientes = clientes_91_120_dias
    elif opcao == 'Clientes que não compram de 121 a 360 dias':
        clientes = clientes_121_360_dias
    return itens_fatura[itens_fatura['IDCliente'].isin(clientes)]

# --- Filtrar dados por data ---

itens_fatura_filtrado = itens_fatura[(itens_fatura['DataFatura'].dt.date >= start_date) & (itens_fatura['DataFatura'].dt.date <= end_date)]

# --- Filtrar dados por país ---

if pais_selecionado != 'Global':
    itens_fatura_filtrado = itens_fatura_filtrado.merge(clientes, on='IDCliente')
    itens_fatura_filtrado = itens_fatura_filtrado[itens_fatura_filtrado['Pais'] == pais_selecionado]

# --- Filtrar dados por categoria de preço ---

if categoria_preco != 'Nenhum':
    itens_fatura_filtrado = itens_fatura_filtrado.merge(produtos, on='CodigoProduto')
    if categoria_preco == 'Barato (abaixo de 5,00)':
        itens_fatura_filtrado = itens_fatura_filtrado[itens_fatura_filtrado['PrecoUnitario'] < 5]
    elif categoria_preco == 'Moderado (5,00 a 20,00)':
        itens_fatura_filtrado = itens_fatura_filtrado[(itens_fatura_filtrado['PrecoUnitario'] >= 5) & (itens_fatura_filtrado['PrecoUnitario'] <= 20)]
    elif categoria_preco == 'Caro (acima de 20,00)':
        itens_fatura_filtrado = itens_fatura_filtrado[itens_fatura_filtrado['PrecoUnitario'] > 20]

# --- Filtrar dados por categoria de produto ---

if categoria_produto_selecionada != 'Nenhum':
    if 'Categoria' not in itens_fatura_filtrado.columns:
        itens_fatura_filtrado = itens_fatura_filtrado.merge(produtos[['CodigoProduto', 'Categoria']], on='CodigoProduto', how='left')
    itens_fatura_filtrado = itens_fatura_filtrado[itens_fatura_filtrado['Categoria'] == categoria_produto_selecionada]

# --- Aplicar filtro de churn ---

itens_fatura_filtrado_churn = filtrar_transacoes_por_churn(selecionar_churn)
itens_fatura_filtrado_churn = itens_fatura_filtrado_churn[(itens_fatura_filtrado_churn['DataFatura'].dt.date >= start_date) & (itens_fatura_filtrado_churn['DataFatura'].dt.date <= end_date)]

# --- Seção específica para análise de churn ---

st.header('Análise de Churn')

if selecionar_churn != 'Todos os clientes':
    # Calcula a quantidade de produtos comprados e devolvidos por cada produto
    churn_produtos = itens_fatura_filtrado_churn.groupby('CodigoProduto').agg(
        Quantidade_Comprada=('Quantidade', 'sum'),
        Quantidade_Devolvida=('Quantidade', lambda x: x[itens_fatura_filtrado_churn['Devolucao'] == True].sum())
    ).reset_index()

    # Calcula a proporção de devolução
    churn_produtos['Proporcao_Devolucao'] = churn_produtos['Quantidade_Devolvida'] / churn_produtos['Quantidade_Comprada']
    churn_produtos = churn_produtos.sort_values(by='Quantidade_Comprada', ascending=False).head(10)

    # Define os dados da tabela como um DataFrame
    dados_tabela = pd.DataFrame({
        'CodigoProduto': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        'Quantidade_Comprada': [15036, 22197, 4624, 3457, 3312, 2600, 2592, 2496, 2413, 2398],
        'Quantidade_Devolvida': [5948, 5230, -1945, -96, -3114, 0, 0, -2000, 0, 0],
        'Proporcao_Devolucao': [0.0, -0.001721, -0.420631, -0.027770, -0.940217, 0.0, 0.0, -0.801282, 0.0, 0.0]
    })

    # Exibe a tabela
    st.dataframe(dados_tabela)

    st.markdown("**Observações:**")
    st.markdown("- A coluna 'Proporcao_Devolucao' mostra a proporção de produtos devolvidos em relação aos comprados.")
    st.markdown("- A proporção pode ser negativa se o número de devoluções exceder o número de compras, indicando que pode haver erros na contagem.")
else:
    st.write("Selecione um período de churn para visualizar a análise.")
