import streamlit as st
import pandas as pd
from datetime import timedelta

# Funções auxiliares para validação e tratamento de dados
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

# Carregar os DataFrames
clientes = ler_csv_com_tratamento('clientes.csv')
itens_fatura = ler_csv_com_tratamento('itens_fatura.csv')
produtos = ler_csv_com_tratamento('produtos.csv')

# Verificar se os DataFrames foram carregados corretamente
if any(df is None for df in [clientes, itens_fatura, produtos]):
    st.stop()  # Interromper a execução do aplicativo

# Converter a coluna 'DataFatura' para datetime
itens_fatura['DataFatura'] = pd.to_datetime(itens_fatura['DataFatura'], errors='coerce')

# Remover registros com datas inválidas
itens_fatura.dropna(subset=['DataFatura'], inplace=True)

# Garantir que a coluna 'Categoria' exista em itens_fatura
if 'Categoria' not in itens_fatura.columns:
    itens_fatura = itens_fatura.merge(produtos[['CodigoProduto', 'Categoria']], on='CodigoProduto', how='left')

# Funções para calcular indicadores de vendas
def calcular_receita_total(itens_fatura):
    return itens_fatura['ValorTotal'].sum()

def calcular_receita_diaria(itens_fatura, start_date, end_date):
    filtered_data = itens_fatura[
        (itens_fatura['DataFatura'].dt.date >= start_date) & (itens_fatura['DataFatura'].dt.date <= end_date)
    ]
    receita_diaria = filtered_data.resample('D', on='DataFatura')['ValorTotal'].sum()
    return receita_diaria

def calcular_receita_mensal(itens_fatura):
    receita_mensal = itens_fatura.groupby(itens_fatura['DataFatura'].dt.to_period('M'))['ValorTotal'].sum()
    return receita_mensal

def calcular_receita_por_pais(itens_fatura, clientes):
    merged_data = itens_fatura.merge(clientes, on='IDCliente')
    if 'Pais' in merged_data.columns:
        receita_pais = merged_data.groupby('Pais')['ValorTotal'].sum()
        return receita_pais
    else:
        return pd.Series()

# Funções para calcular indicadores de clientes
def calcular_clientes_unicos(itens_fatura):
    return itens_fatura['IDCliente'].nunique()

def calcular_top_clientes(itens_fatura, n=100):
    top_clientes = itens_fatura.groupby('IDCliente')['ValorTotal'].sum().nlargest(n).reset_index()
    top_clientes['IDCliente'] = top_clientes['IDCliente'].astype(str)  # Ajustar a formatação
    return top_clientes

def calcular_frequencia_compras(itens_fatura):
    frequencia = itens_fatura.groupby('IDCliente').size()
    return frequencia

# Funções para calcular indicadores de produtos
def calcular_produtos_mais_vendidos(itens_fatura, produtos):
    vendidos = itens_fatura.groupby('CodigoProduto')['Quantidade'].sum().nlargest(10).reset_index()
    return vendidos.merge(produtos, on='CodigoProduto')

def calcular_produtos_melhor_desempenho(itens_fatura, produtos):
    desempenho = itens_fatura.groupby('CodigoProduto')['ValorTotal'].sum().nlargest(10).reset_index()
    return desempenho.merge(produtos, on='CodigoProduto')

def calcular_produtos_mais_devolvidos(itens_fatura, produtos):
    devolvidos = itens_fatura[itens_fatura['Devolucao'] == True].groupby('CodigoProduto')['Quantidade'].sum().nlargest(10).reset_index()
    return devolvidos.merge(produtos, on='CodigoProduto')

# Funções para calcular indicadores de transações
def calcular_numero_transacoes(itens_fatura):
    return itens_fatura['NumeroFatura'].nunique()

def calcular_transacoes_com_devolucoes(itens_fatura):
    return itens_fatura[itens_fatura['Devolucao'] == True]['NumeroFatura'].nunique()

def calcular_ticket_medio(itens_fatura):
    return itens_fatura['ValorTotal'].mean()

# Funções para análise temporal
def calcular_variacao_sazonal(itens_fatura):
    variacao = itens_fatura.groupby(itens_fatura['DataFatura'].dt.month)['ValorTotal'].sum()
    return variacao

def calcular_tendencia_vendas(itens_fatura):
    tendencia = itens_fatura.groupby(itens_fatura['DataFatura'].dt.to_period('M'))['ValorTotal'].sum()
    return tendencia

# Função para filtrar clientes que não compraram em um intervalo de dias
def filtrar_clientes_por_intervalo(df, dias_inicio, dias_fim, ultima_data):
    data_inicio = ultima_data - timedelta(days=dias_inicio)
    data_fim = ultima_data - timedelta(days=dias_fim)
    clientes_inativos = df.groupby('IDCliente').filter(
        lambda x: x['DataFatura'].max() <= data_inicio and x['DataFatura'].max() > data_fim
    )
    return clientes_inativos['IDCliente'].unique()

# Definir a última data do dataset para a filtragem
ultima_data = itens_fatura['DataFatura'].max()

# Aplicar os filtros
clientes_30_60_dias = filtrar_clientes_por_intervalo(itens_fatura, 30, 60, ultima_data)
clientes_61_90_dias = filtrar_clientes_por_intervalo(itens_fatura, 61, 90, ultima_data)
clientes_91_120_dias = filtrar_clientes_por_intervalo(itens_fatura, 91, 120, ultima_data)
clientes_121_360_dias = filtrar_clientes_por_intervalo(itens_fatura, 121, 360, ultima_data)

# Título do app
st.title('Relatório de Vendas')

# Filtro de Análise de Churn
st.sidebar.header('Análise de Churn')
opcoes_churn = ['Todos os clientes', 'Clientes que não compram de 30 a 60 dias', 'Clientes que não compram de 61 a 90 dias', 'Clientes que não compram de 91 a 120 dias', 'Clientes que não compram de 121 a 360 dias']
selecionar_churn = st.sidebar.selectbox('Selecione o período de churn:', opcoes_churn)

# Seleção de datas para filtrar os dados
st.sidebar.header('Filtro de Data')
start_date = st.sidebar.date_input('Data Inicial', pd.to_datetime(itens_fatura['DataFatura'].min()).date(), min_value=pd.to_datetime(itens_fatura['DataFatura'].min()).date(), max_value=pd.to_datetime(itens_fatura['DataFatura'].max()).date())
end_date = st.sidebar.date_input('Data Final', pd.to_datetime(itens_fatura['DataFatura'].max()).date(), min_value=pd.to_datetime(itens_fatura['DataFatura'].min()).date(), max_value=pd.to_datetime(itens_fatura['DataFatura'].max()).date())

if start_date > end_date:
    st.sidebar.error('Erro: A data final deve ser posterior à data inicial.')

# Seleção de país
st.sidebar.header('Filtro de País')
paises = ['Global'] + list(clientes['Pais'].unique())
pais_selecionado = st.sidebar.selectbox('Escolha um País:', paises)

# Seleção de categorias de preço com descrição
st.sidebar.header('Filtro de Categoria de Preço')
categoria_preco = st.sidebar.radio(
    'Escolha uma Categoria de Preço:',
    ['Nenhum', 'Barato (abaixo de 5,00)', 'Moderado (5,00 a 20,00)', 'Caro (acima de 20,00)']
)

# Seleção de categoria de produtos
st.sidebar.header('Filtro de Categoria de Produtos')
categorias_produtos = ['Nenhum'] + list(produtos['Categoria'].unique())
categoria_produto_selecionada = st.sidebar.selectbox('Escolha uma Categoria de Produto:', categorias_produtos)

# Função para filtrar transações de acordo com a seleção de churn
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

# Filtrar dados por data
itens_fatura_filtrado = itens_fatura[(itens_fatura['DataFatura'].dt.date >= start_date) & (itens_fatura['DataFatura'].dt.date <= end_date)]

# Filtrar dados por país
if pais_selecionado != 'Global':
    itens_fatura_filtrado = itens_fatura_filtrado.merge(clientes, on='IDCliente')
    itens_fatura_filtrado = itens_fatura_filtrado[itens_fatura_filtrado['Pais'] == pais_selecionado]

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

# Aplicar filtro de churn
itens_fatura_filtrado_churn = filtrar_transacoes_por_churn(selecionar_churn)
itens_fatura_filtrado_churn = itens_fatura_filtrado_churn[(itens_fatura_filtrado_churn['DataFatura'].dt.date >= start_date) & (itens_fatura_filtrado_churn['DataFatura'].dt.date <= end_date)]

# Seção de Indicadores de Vendas
st.header('Indicadores de Vendas')
st.write(f"Receita Total: ${calcular_receita_total(itens_fatura_filtrado_churn):,.2f}")

st.subheader('Receita Diária')
st.line_chart(calcular_receita_diaria(itens_fatura_filtrado_churn, start_date, end_date))

st.subheader('Receita Mensal')
st.line_chart(calcular_receita_mensal(itens_fatura_filtrado_churn))

# Seção de Indicadores de Clientes
st.header('Indicadores de Clientes')
st.write(f"Clientes Únicos: {calcular_clientes_unicos(itens_fatura_filtrado_churn)}")

st.subheader('Top Clientes')
top_clientes = calcular_top_clientes(itens_fatura_filtrado_churn)
st.dataframe(top_clientes)

st.subheader('Frequência de Compras por Cliente')
st.bar_chart(calcular_frequencia_compras(itens_fatura_filtrado_churn))

# Seção de Indicadores de Produtos
st.header('Indicadores de Produtos')
st.subheader('Produtos Mais Vendidos')
st.dataframe(calcular_produtos_mais_vendidos(itens_fatura_filtrado_churn, produtos))

st.subheader('Produtos com Melhor Desempenho por Categoria')
st.dataframe(calcular_produtos_melhor_desempenho(itens_fatura_filtrado_churn, produtos))

st.subheader('Produtos Mais Devolvidos')
st.dataframe(calcular_produtos_mais_devolvidos(itens_fatura_filtrado_churn, produtos))

# Seção de Indicadores de Transações
st.header('Indicadores de Transações')
st.write(f"Número de Transações: {calcular_numero_transacoes(itens_fatura_filtrado_churn)}")
st.write(f"Transações com Devoluções: {calcular_transacoes_com_devolucoes(itens_fatura_filtrado_churn)}")
st.write(f"Ticket Médio: ${calcular_ticket_medio(itens_fatura_filtrado_churn):,.2f}")

# Seção de Análise Temporal
st.header('Análise Temporal')
st.subheader('Variação Sazonal nas Vendas')
st.line_chart(calcular_variacao_sazonal(itens_fatura_filtrado_churn))

st.subheader('Tendência de Vendas ao Longo do Tempo')
st.line_chart(calcular_tendencia_vendas(itens_fatura_filtrado_churn))
