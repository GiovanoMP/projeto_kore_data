import streamlit as st
import pandas as pd

# Carregar os dataframes
clientes = pd.read_csv('clientes.csv')
itens_fatura = pd.read_csv('itens_fatura.csv')
produtos = pd.read_csv('produtos.csv')
segmentacao = pd.read_csv('df_treinamento_reduzido.csv')

# Pré-processamento de dados
itens_fatura['DataFatura'] = pd.to_datetime(itens_fatura['DataFatura'], errors='coerce')
itens_fatura = itens_fatura.dropna(subset=['DataFatura'])
clientes.rename(columns=lambda x: x.strip(), inplace=True)
itens_fatura.rename(columns=lambda x: x.strip(), inplace=True)
produtos.rename(columns=lambda x: x.strip(), inplace=True)

# Adiciona a coluna 'Categoria' em itens_fatura se não existir
if 'Categoria' not in itens_fatura.columns:
    itens_fatura = itens_fatura.merge(produtos[['CodigoProduto', 'Categoria']], on='CodigoProduto', how='left')

# Funções auxiliares para calcular os indicadores
def calcular_receita_total(itens_fatura):
    return itens_fatura['ValorTotal'].sum()

def calcular_receita_diaria(itens_fatura, start_date, end_date):
    filtro = (itens_fatura['DataFatura'].dt.date >= start_date) & (itens_fatura['DataFatura'].dt.date <= end_date)
    receita_diaria = itens_fatura[filtro].groupby(itens_fatura['DataFatura'].dt.date)['ValorTotal'].sum()
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

def calcular_clientes_unicos(itens_fatura):
    return itens_fatura['IDCliente'].nunique()

def calcular_top_clientes(itens_fatura, n=100):
    top_clientes = itens_fatura.groupby('IDCliente')['ValorTotal'].sum().nlargest(n).reset_index()
    top_clientes['IDCliente'] = top_clientes['IDCliente'].astype(str)  # Ajustar a formatação
    return top_clientes

def calcular_frequencia_compras(itens_fatura):
    frequencia = itens_fatura.groupby('IDCliente').size()
    return frequencia

def calcular_produtos_mais_vendidos(itens_fatura, produtos):
    vendidos = itens_fatura.groupby('CodigoProduto')['Quantidade'].sum().nlargest(10).reset_index()
    return vendidos.merge(produtos, on='CodigoProduto')

def calcular_produtos_melhor_desempenho(itens_fatura, produtos):
    desempenho = itens_fatura.groupby('CodigoProduto')['ValorTotal'].sum().nlargest(10).reset_index()
    return desempenho.merge(produtos, on='CodigoProduto')

def calcular_produtos_mais_devolvidos(itens_fatura, produtos):
    devolvidos = itens_fatura[itens_fatura['Devolucao'] == True].groupby('CodigoProduto')['Quantidade'].sum().nlargest(10).reset_index()
    return devolvidos.merge(produtos, on='CodigoProduto')

def calcular_numero_transacoes(itens_fatura):
    return itens_fatura['NumeroFatura'].nunique()

def calcular_transacoes_com_devolucoes(itens_fatura):
    return itens_fatura[itens_fatura['Devolucao'] == True]['NumeroFatura'].nunique()

def calcular_ticket_medio(itens_fatura):
    return itens_fatura['ValorTotal'].mean()

def calcular_variacao_sazonal(itens_fatura):
    variacao = itens_fatura.groupby(itens_fatura['DataFatura'].dt.month)['ValorTotal'].sum()
    return variacao

def calcular_tendencia_vendas(itens_fatura):
    tendencia = itens_fatura.groupby(itens_fatura['DataFatura'].dt.to_period('M'))['ValorTotal'].sum()
    return tendencia

# Título do app
st.title('Relatório de Vendas e Segmentação de Clientes')

# Menu lateral
st.sidebar.header('Menu')
opcao = st.sidebar.radio('Selecione uma opção:', ['Relatório de Vendas', 'Segmentação de Clientes'])

# Seção de Relatório de Vendas
if opcao == 'Relatório de Vendas':
    # Seleção de datas para filtrar os dados
    st.sidebar.header('Filtro de Data')
    start_date = st.sidebar.date_input('Data Inicial', pd.to_datetime(itens_fatura['DataFatura'].min()).date(), min_value=pd.to_datetime(itens_fatura['DataFatura'].min()).date(), max_value=pd.to_datetime(itens_fatura['DataFatura'].max()).date())
    end_date = st.sidebar.date_input('Data Final', pd.to_datetime(itens_fatura['DataFatura'].max()).date(), min_value=pd.to_datetime(itens_fatura['DataFatura'].min()).date(), max_value=pd.to_datetime(itens_fatura['DataFatura'].max()).date())

    if start_date > end_date:
        st.sidebar.error('Erro: A data final deve ser posterior à data inicial.')

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

    # Seleção de país
    st.sidebar.header('Filtro de País')
    paises = ['Global'] + list(clientes['Pais'].unique())
    pais_selecionado = st.sidebar.selectbox('Escolha um País:', paises)

    # Filtrar dados por categoria de preço
    if categoria_preco != 'Nenhum':
        itens_fatura_filtrado = itens_fatura.merge(produtos, on='CodigoProduto')
        if categoria_preco == 'Barato (abaixo de 5,00)':
            itens_fatura_filtrado = itens_fatura_filtrado[itens_fatura_filtrado['PrecoUnitario'] < 5]
        elif categoria_preco == 'Moderado (5,00 a 20,00)':
            itens_fatura_filtrado = itens_fatura_filtrado[(itens_fatura_filtrado['PrecoUnitario'] >= 5) & (itens_fatura_filtrado['PrecoUnitario'] <= 20)]
        elif categoria_preco == 'Caro (acima de 20,00)':
            itens_fatura_filtrado = itens_fatura_filtrado[itens_fatura_filtrado['PrecoUnitario'] > 20]
    else:
        itens_fatura_filtrado = itens_fatura.copy()

    # Filtrar dados por categoria de produto
    if categoria_produto_selecionada != 'Nenhum':
        if 'Categoria' not in itens_fatura_filtrado.columns:
            itens_fatura_filtrado = itens_fatura_filtrado.merge(produtos[['CodigoProduto', 'Categoria']], on='CodigoProduto', how='left')
        itens_fatura_filtrado = itens_fatura_filtrado[itens_fatura_filtrado['Categoria'] == categoria_produto_selecionada]

    # Filtrar dados por país
    if pais_selecionado != 'Global':
        itens_fatura_filtrado = itens_fatura_filtrado.merge(clientes, on='IDCliente')
        itens_fatura_filtrado = itens_fatura_filtrado[itens_fatura_filtrado['Pais'] == pais_selecionado]
    else:
        itens_fatura_filtrado = itens_fatura_filtrado.merge(clientes, on='IDCliente')

    # Seção de Indicadores de Vendas
    st.header('Indicadores de Vendas')
    st.write(f"Receita Total: ${calcular_receita_total(itens_fatura_filtrado):,.2f}")

    st.subheader('Receita Diária')
    st.line_chart(calcular_receita_diaria(itens_fatura_filtrado, start_date, end_date))

    st.subheader('Receita Mensal')
    st.line_chart(calcular_receita_mensal(itens_fatura_filtrado))

    st.subheader('Receita por País')
    receita_por_pais = calcular_receita_por_pais(itens_fatura_filtrado, clientes)
    if not receita_por_pais.empty:
        st.bar_chart(receita_por_pais)
    else:
        st.write("Nenhum dado disponível para Receita por País.")

    # Seção de Indicadores de Clientes
    st.header('Indicadores de Clientes')
    st.write(f"Clientes Únicos: {calcular_clientes_unicos(itens_fatura_filtrado)}")

    st.subheader('Top Clientes')
    top_clientes = calcular_top_clientes(itens_fatura_filtrado)
    st.dataframe(top_clientes)

    st.subheader('Frequência de Compras por Cliente')
    st.bar_chart(calcular_frequencia_compras(itens_fatura_filtrado))

    # Seção de Indicadores de Produtos
    st.header('Indicadores de Produtos')
    st.subheader('Produtos Mais Vendidos')
    st.dataframe(calcular_produtos_mais_vendidos(itens_fatura_filtrado, produtos))

    st.subheader('Produtos com Melhor Desempenho por Categoria')
    st.dataframe(calcular_produtos_melhor_desempenho(itens_fatura_filtrado, produtos))

    st.subheader('Produtos Mais Devolvidos')
    st.dataframe(calcular_produtos_mais_devolvidos(itens_fatura_filtrado, produtos))

    # Seção de Indicadores de Transações
    st.header('Indicadores de Transações')
    st.write(f"Número de Transações: {calcular_numero_transacoes(itens_fatura_filtrado)}")
    st.write(f"Transações com Devoluções: {calcular_transacoes_com_devolucoes(itens_fatura_filtrado)}")
    st.write(f"Ticket Médio: ${calcular_ticket_medio(itens_fatura_filtrado):,.2f}")

    # Seção de Análise Temporal
    st.header('Análise Temporal')
    st.subheader('Variação Sazonal nas Vendas')
    st.line_chart(calcular_variacao_sazonal(itens_fatura_filtrado))

    st.subheader('Tendência de Vendas ao Longo do Tempo')
    st.line_chart(calcular_tendencia_vendas(itens_fatura_filtrado))

    # Rodapé
    st.write('Relatório gerado por Streamlit')

# Seção de Segmentação de Clientes
else:
    st.header('Segmentação de Clientes')

    # Mostrar informações de segmentação
    st.write("Segmentação de clientes:", segmentacao)

    # Mostrar produtos recomendados para um cliente
    id_cliente = st.text_input('Digite o ID do cliente:')
    if id_cliente:
        # Substituir a vírgula por ponto para converter para float
        id_cliente = id_cliente.replace(',', '.')
        cliente = segmentacao[segmentacao['IDCliente'] == float(id_cliente)]
        if not cliente.empty:
            produtos_recomendados = eval(cliente['ProdutosRecomendados'].values[0])
            st.write(f"Produtos recomendados para o cliente {id_cliente}: {produtos_recomendados}")
        else:
            st.write(f"Cliente {id_cliente} não encontrado.")
