import streamlit as st
import pandas as pd

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
    top_clientes['IDCliente'] = top_clientes['IDCliente'].astype(str) 
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

# Função para calcular o tempo desde a última compra
def calcular_tempo_desde_ultima_compra(itens_fatura, data_referencia):
    ultima_compra = itens_fatura.groupby('IDCliente')['DataFatura'].max()
    dias_desde_ultima_compra = (data_referencia - ultima_compra).dt.days
    return dias_desde_ultima_compra

# Título do app
st.title('Relatório de Vendas e Segmentação de Clientes')

# Menu lateral
st.sidebar.header('Menu')
opcao = st.sidebar.radio('Selecione uma opção:', ['Relatório de Vendas', 'Segmentação de Clientes', 'Busca de Cliente', 'Histórico de Vendas e Churn'])

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

    # Ajustar os segmentos de clientes de 1 a 5 e incluir a opção "Nenhum"
    segmentos_ajustados = ['Nenhum'] + [f'Segmento {i}' for i in range(1, 6)]
    
    # Seleção de segmento
    segmento_selecionado = st.sidebar.selectbox('Selecione um Segmento:', segmentos_ajustados)

    if segmento_selecionado != 'Nenhum':
        if st.button('Mostrar Clientes'):
            # Extrair o número do segmento
            segmento_numero = int(segmento_selecionado.split()[-1])
            
            # Filtrar clientes por segmento
            clientes_segmento = segmentacao[segmentacao['segmento'] == segmento_numero]
            clientes_ids = clientes_segmento['IDCliente'].unique()
            
            st.write(f"Clientes no {segmento_selecionado}:")
            for cliente in clientes_ids:
                st.write(f"Cliente {cliente}:")
                produtos_recomendados = clientes_segmento[clientes_segmento['IDCliente'] == cliente]['ProdutosRecomendados'].values[0]
                st.write("Produtos recomendados:")
                for produto in eval(produtos_recomendados):
                    categoria = produtos[produtos['CodigoProduto'] == str(produto)]['Categoria']
                    if not categoria.empty:
                        categoria = categoria.values[0]
                        st.write(f"  - Produto: {produto}, Categoria: {categoria}")
                    else:
                        st.write(f"  - Produto: {produto}, Categoria: Não encontrada")

# Seção de Busca de Cliente
elif opcao == 'Busca de Cliente':
    st.header('Busca de Cliente')

    # Input para buscar cliente
    id_cliente = st.sidebar.text_input('Digite o ID do cliente:')
    if id_cliente:
        try:
            id_cliente_float = float(id_cliente.replace(',', '.'))
            cliente = segmentacao[segmentacao['IDCliente'] == id_cliente_float]
            if not cliente.empty:
                cliente_info = clientes[clientes['IDCliente'] == id_cliente_float]
                valor_total = itens_fatura[itens_fatura['IDCliente'] == id_cliente_float]['ValorTotal'].sum()
                ultimos_produtos = itens_fatura[itens_fatura['IDCliente'] == id_cliente_float].sort_values(by='DataFatura', ascending=False).head(5)
                
                st.write(f"Informações do cliente {id_cliente}:")
                if not cliente_info.empty:
                    st.write(f"País: {cliente_info['Pais'].values[0]}")
                st.write(f"Valor total de compras: ${valor_total:,.2f}")
                st.write("Últimos produtos comprados:")
                for _, row in ultimos_produtos.iterrows():
                    st.write(f"  - Produto: {row['CodigoProduto']}, Data: {row['DataFatura'].date()}, Valor: ${row['ValorTotal']:,.2f}")
                
                st.write("Produtos recomendados:")
                produtos_recomendados = eval(cliente['ProdutosRecomendados'].values[0])
                for produto in produtos_recomendados:
                    categoria = produtos[produtos['CodigoProduto'] == str(produto)]['Categoria']
                    if not categoria.empty:
                        categoria = categoria.values[0]
                        st.write(f"  - Produto: {produto}, Categoria: {categoria}")
                    else:
                        st.write(f"  - Produto: {produto}, Categoria: Não encontrada")
            else:
                st.write(f"Cliente {id_cliente} não encontrado.")
        except ValueError:
            st.write("Por favor, insira um ID de cliente válido.")

# Seção de Histórico de Vendas e Churn
elif opcao == 'Histórico de Vendas e Churn':
    st.header('Histórico de Vendas e Churn')

    # Calcular o tempo desde a última compra
    data_referencia = pd.to_datetime(itens_fatura['DataFatura'].max())
    tempo_desde_ultima_compra = calcular_tempo_desde_ultima_compra(itens_fatura, data_referencia)

    # Categorizar clientes por tempo desde a última compra
    churn_30_59 = tempo_desde_ultima_compra[(tempo_desde_ultima_compra >= 30) & (tempo_desde_ultima_compra <= 59)]
    churn_60_89 = tempo_desde_ultima_compra[(tempo_desde_ultima_compra >= 60) & (tempo_desde_ultima_compra <= 89)]
    churn_90_119 = tempo_desde_ultima_compra[(tempo_desde_ultima_compra >= 90) & (tempo_desde_ultima_compra <= 119)]
    churn_120_180 = tempo_desde_ultima_compra[(tempo_desde_ultima_compra >= 120) & (tempo_desde_ultima_compra <= 180)]
    churn_181_plus = tempo_desde_ultima_compra[tempo_desde_ultima_compra > 180]

    # Exibir os clientes em cada categoria de churn
    st.subheader('Clientes que não compram há 30 a 59 dias:')
    st.write(churn_30_59)

    st.subheader('Clientes que não compram há 60 a 89 dias:')
    st.write(churn_60_89)

    st.subheader('Clientes que não compram há 90 a 119 dias:')
    st.write(churn_90_119)

    st.subheader('Clientes que não compram há 120 a 180 dias (Churn):')
    st.write(churn_120_180)

    st.subheader('Clientes que não compram há mais de 181 dias (Churn):')
    st.write(churn_181_plus)


