import streamlit as st
import pandas as pd
import numpy as np

# URLs dos arquivos no GitHub
base_url = 'https://raw.githubusercontent.com/GiovanoMP/projeto_kore_data/main/'
url_clientes = base_url + 'clientes.csv'
url_itens_fatura = base_url + 'itens_fatura.csv'
url_produtos = base_url + 'produtos.csv'
url_segmentacao = base_url + 'df_treinamento_reduzido.csv'

# Carregar os dataframes
clientes = pd.read_csv(url_clientes)
itens_fatura = pd.read_csv(url_itens_fatura)
produtos = pd.read_csv(url_produtos)
segmentacao = pd.read_csv(url_segmentacao)

# Converter a coluna 'DataFatura' para datetime
itens_fatura['DataFatura'] = pd.to_datetime(itens_fatura['DataFatura'], errors='coerce')

# Filtrar registros com datas válidas
itens_fatura = itens_fatura.dropna(subset=['DataFatura'])

# Garantir que os nomes das colunas estejam corretos
clientes.rename(columns=lambda x: x.strip(), inplace=True)
itens_fatura.rename(columns=lambda x: x.strip(), inplace=True)
produtos.rename(columns=lambda x: x.strip(), inplace=True)
segmentacao.rename(columns=lambda x: x.strip(), inplace=True)

# Verificar se a coluna 'Categoria' existe em itens_fatura e adicionar se necessário
if 'Categoria' not in itens_fatura.columns:
    itens_fatura = itens_fatura.merge(produtos[['CodigoProduto', 'Categoria']], on='CodigoProduto', how='left')

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
elif opcao == 'Segmentação de Clientes':
    st.header('Segmentação de Clientes')

    # Seleção de segmento
    segmento_selecionado = st.sidebar.selectbox('Selecione um Segmento:', segmentacao['segmento'].unique())
    
    # Seleção de tipo de produto
    tipo_produto_selecionado = st.sidebar.selectbox('Selecione um Tipo de Produto:', produtos['Categoria'].unique())

    if st.button('Mostrar Clientes'):
        # Filtrar clientes por segmento e tipo de produto
        clientes_segmento = segmentacao[segmentacao['segmento'] == segmento_selecionado]
        clientes_ids = clientes_segmento['IDCliente'].unique()
        
        itens_fatura_filtrado = itens_fatura[(itens_fatura['IDCliente'].isin(clientes_ids)) & 
                                             (itens_fatura['Categoria'] == tipo_produto_selecionado)]
        
        clientes_filtrados = itens_fatura_filtrado['IDCliente'].unique()
        
        st.write(f"Clientes no segmento {segmento_selecionado} e tipo de produto {tipo_produto_selecionado}:")
        st.write(clientes_filtrados)
