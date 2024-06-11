import streamlit as st
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import matplotlib.pyplot as plt
import numpy as np
from datetime import timedelta

# Configuração da Página
st.set_page_config(layout="wide")
st.title('Relatório de Vendas e Segmentação de Clientes')

# URLs dos arquivos no GitHub
base_url = 'https://raw.githubusercontent.com/GiovanoMP/projeto_kore_data/main/'
url_clientes = base_url + 'clientes.csv'
url_itens_fatura = base_url + 'itens_fatura.csv'
url_produtos = base_url + 'produtos.csv'
url_segmentacao = base_url + 'df_treinamento_reduzido.csv'

# Carregar os DataFrames
clientes = pd.read_csv(url_clientes)
itens_fatura = pd.read_csv(url_itens_fatura)
produtos = pd.read_csv(url_produtos)
segmentacao = pd.read_csv(url_segmentacao)

# Preparação de Dados
itens_fatura['DataFatura'] = pd.to_datetime(itens_fatura['DataFatura'], errors='coerce')
itens_fatura = itens_fatura.dropna(subset=['DataFatura'])
clientes.rename(columns=lambda x: x.strip(), inplace=True)
itens_fatura.rename(columns=lambda x: x.strip(), inplace=True)
produtos.rename(columns=lambda x: x.strip(), inplace=True)
segmentacao.rename(columns=lambda x: x.strip(), inplace=True)

if 'Categoria' not in itens_fatura.columns:
    itens_fatura = itens_fatura.merge(produtos[['CodigoProduto', 'Categoria']], on='CodigoProduto', how='left')

# Funções de Análise
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
    ultima_compra = itens_fatura.groupby('IDCliente')['DataFatura'].max().reset_index()
    ultima_compra['DiasDesdeUltimaCompra'] = (data_referencia - ultima_compra['DataFatura']).dt.days
    return ultima_compra[['IDCliente', 'DiasDesdeUltimaCompra']]

# Funções de Análise de Churn
def filtrar_clientes_por_intervalo(df, dias_inicio, dias_fim, ultima_data):
    data_inicio = ultima_data - timedelta(days=dias_inicio)
    data_fim = ultima_data - timedelta(days=dias_fim)
    clientes_inativos = df.groupby('IDCliente').filter(
        lambda x: x['DataFatura'].max() <= data_inicio and x['DataFatura'].max() > data_fim
    )
    return clientes_inativos['IDCliente'].unique()

def analisar_produtos(clientes, descricao):
    transacoes = itens_fatura[itens_fatura['IDCliente'].isin(clientes)]
    produtos_mais_comprados = transacoes.groupby('CodigoProduto')['Quantidade'].sum().sort_values(ascending=False).head(10)
    produtos_devolucoes = transacoes[transacoes['Devolucao']].groupby('CodigoProduto')['Quantidade'].sum()
    produtos_mais_comprados = produtos_mais_comprados.to_frame().join(produtos_devolucoes, rsuffix='_Devolucao').fillna(0)
    produtos_mais_comprados.columns = ['Quantidade_Comprada', 'Quantidade_Devolvida']
    produtos_mais_comprados['Proporcao_Devolucao'] = produtos_mais_comprados['Quantidade_Devolvida'] / produtos_mais_comprados['Quantidade_Comprada']
    produtos_mais_comprados.reset_index(inplace=True)
    st.write(f"Produtos mais comprados por {descricao}:")
    st.dataframe(produtos_mais_comprados)
    st.write("Clientes:")
    for cliente in clientes:
        st.write(f"Cliente {cliente}")

# Funções de Previsão de Vendas
def preprocessar_dados(df):
    df['DataFatura'] = pd.to_datetime(df['DataFatura'])
    df['Ano'] = df['DataFatura'].dt.year
    df['Mes'] = df['DataFatura'].dt.month
    df['DiaSemana'] = df['DataFatura'].dt.dayofweek
    return df

def prever_vendas(df_itens_fatura, meses_a_prever):
    st.write("Pré-processando dados...")
    df_itens_fatura['DataFatura'] = pd.to_datetime(df_itens_fatura['DataFatura'], errors='coerce')

    # Tratamento de valores ausentes
    df_itens_fatura.fillna(0, inplace=True)

    # Criação de features baseadas nas datas
    df_itens_fatura['Mes'] = df_itens_fatura['DataFatura'].dt.month
    df_itens_fatura['Ano'] = df_itens_fatura['DataFatura'].dt.year
    df_itens_fatura['DiaSemana'] = df_itens_fatura['DataFatura'].dt.dayofweek

    # Normalização das variáveis numéricas
    scaler = StandardScaler()
    df_itens_fatura[['Quantidade', 'ValorTotal']] = scaler.fit_transform(df_itens_fatura[['Quantidade', 'ValorTotal']])

    # Separação entre features e target
    X = df_itens_fatura.drop(['NumeroFatura', 'CodigoProduto', 'DataFatura', 'IDCliente', 'Venda', 'Devolucao', 'ValorTotal'], axis=1)
    y = df_itens_fatura['ValorTotal']

    # Divisão em treino e teste
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Modelo de Regressão Linear
    model = LinearRegression()
    model.fit(X_train, y_train)

    # Previsões
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    st.write(f'Mean Squared Error: {mse}')
    st.write(f'Mean Absolute Error: {mae}')
    st.write(f'R² Score: {r2}')

    st.write("Visualizando as previsões de vendas futuras...")
    fig, ax = plt.subplots()
    ax.plot(range(len(y_test)), y_test, label='Valor Real')
    ax.plot(range(len(y_pred)), y_pred, label='Previsão')
    ax.set_xlabel('Índice')
    ax.set_ylabel('Valor Total')
    ax.legend()
    ax.set_title('Previsões de Vendas')
    st.pyplot(fig)

    return model

# Interface do Streamlit
st.sidebar.header('Menu')
opcao = st.sidebar.radio('Selecione uma opção:', ['Relatório de Vendas', 'Análise de Churn', 'Segmentação de Clientes', 'Informações por Código do Cliente', 'Análises e Insights', 'Previsão de Vendas com Machine Learning'])

# Seção de Relatório de Vendas
if opcao == 'Relatório de Vendas':
    st.sidebar.header('Filtro de Data')
    start_date = st.sidebar.date_input('Data Inicial', pd.to_datetime(itens_fatura['DataFatura'].min()).date(), min_value=pd.to_datetime(itens_fatura['DataFatura'].min()).date(), max_value=pd.to_datetime(itens_fatura['DataFatura'].max()).date(), format="DD/MM/YYYY")
    end_date = st.sidebar.date_input('Data Final', pd.to_datetime(itens_fatura['DataFatura'].max()).date(), min_value=pd.to_datetime(itens_fatura['DataFatura'].min()).date(), max_value=pd.to_datetime(itens_fatura['DataFatura'].max()).date(), format="DD/MM/YYYY")

    if start_date > end_date:
        st.sidebar.error('Erro: A data final deve ser posterior à data inicial.')

    st.sidebar.header('Filtro de Categoria de Preço')
    categoria_preco = st.sidebar.radio(
        'Escolha uma Categoria de Preço:',
        ['Nenhum', 'Barato (abaixo de 5,00)', 'Moderado (5,00 a 20,00)', 'Caro (acima de 20,00)']
    )

    st.sidebar.header('Filtro de País')
    paises = ['Global'] + list(clientes['Pais'].unique())
    pais_selecionado = st.sidebar.selectbox('Escolha um País:', paises)

    st.sidebar.header('Filtro de Categoria de Produtos')
    categorias_produtos = ['Nenhum'] + list(produtos['Categoria'].unique())
    categoria_produto_selecionada = st.sidebar.selectbox('Escolha uma Categoria de Produto:', categorias_produtos)

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

    if pais_selecionado != 'Global':
        itens_fatura_filtrado = itens_fatura_filtrado.merge(clientes, on='IDCliente')
        itens_fatura_filtrado = itens_fatura_filtrado[itens_fatura_filtrado['Pais'] == pais_selecionado]
    else:
        itens_fatura_filtrado = itens_fatura_filtrado.merge(clientes, on='IDCliente')

    if categoria_produto_selecionada != 'Nenhum':
        itens_fatura_filtrado = itens_fatura_filtrado[itens_fatura_filtrado['Categoria'] == categoria_produto_selecionada]

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
    st.header('Indicadores de Clientes')
    st.write(f"Clientes Únicos: {calcular_clientes_unicos(itens_fatura_filtrado)}")
    st.subheader('Top Clientes')
    top_clientes = calcular_top_clientes(itens_fatura_filtrado)
    st.dataframe(top_clientes)
    st.subheader('Frequência de Compras por Cliente')
    st.bar_chart(calcular_frequencia_compras(itens_fatura_filtrado))
    st.header('Indicadores de Produtos')
    st.subheader('Produtos Mais Vendidos')
    st.dataframe(calcular_produtos_mais_vendidos(itens_fatura_filtrado, produtos))
    st.subheader('Produtos com Melhor Desempenho por Categoria')
    st.dataframe(calcular_produtos_melhor_desempenho(itens_fatura_filtrado, produtos))
    st.subheader('Produtos Mais Devolvidos')
    st.dataframe(calcular_produtos_mais_devolvidos(itens_fatura_filtrado, produtos))
    st.header('Indicadores de Transações')
    st.write(f"Número de Transações: {calcular_numero_transacoes(itens_fatura_filtrado)}")
    st.write(f"Transações com Devoluções: {calcular_transacoes_com_devolucoes(itens_fatura_filtrado)}")
    st.write(f"Ticket Médio: ${calcular_ticket_medio(itens_fatura_filtrado):,.2f}")
    st.header('Análise Temporal')
    st.subheader('Variação Sazonal nas Vendas')
    st.line_chart(calcular_variacao_sazonal(itens_fatura_filtrado))
    st.subheader('Tendência de Vendas ao Longo do Tempo')
    st.line_chart(calcular_tendencia_vendas(itens_fatura_filtrado))

# Seção de Análise de Churn
elif opcao == 'Análise de Churn':
    st.header('Análise de Churn')
    ultima_data = pd.to_datetime(itens_fatura['DataFatura'].max())

    st.sidebar.header('Filtro de Churn')
    intervalo = st.sidebar.selectbox('Selecione um intervalo de dias:', ['30-60 dias', '61-90 dias', '91-120 dias', '121-360 dias'])
    if intervalo == '30-60 dias':
        dias_inicio, dias_fim = 30, 60
    elif intervalo == '61-90 dias':
        dias_inicio, dias_fim = 61, 90
    elif intervalo == '91-120 dias':
        dias_inicio, dias_fim = 91, 120
    elif intervalo == '121-360 dias':
        dias_inicio, dias_fim = 121, 360

    clientes_filtrados = filtrar_clientes_por_intervalo(itens_fatura, dias_inicio, dias_fim, ultima_data)
    quantidade_total_clientes = itens_fatura['IDCliente'].nunique()
    qtd_clientes_filtrados = len(clientes_filtrados)
    st.write(f"Quantidade total de clientes: {quantidade_total_clientes}")
    st.write(f"Clientes que não compram há {dias_fim} a {dias_inicio} dias: {qtd_clientes_filtrados}")
    porcentagem_churn = (qtd_clientes_filtrados / quantidade_total_clientes) * 100
    st.write(f"Porcentagem de churn: {porcentagem_churn:.2f}%")
    st.write("Clientes:")
    for cliente in clientes_filtrados:
        st.write(f"Cliente {cliente}")
    analisar_produtos(clientes_filtrados, f"clientes que não compram há {dias_fim} a {dias_inicio} dias")

# Seção de Segmentação de Clientes
elif opcao == 'Segmentação de Clientes':
    st.header('Segmentação de Clientes')
    segmentos_ajustados = ['Nenhum'] + [f'Segmento {i}' for i in range(1, 6)]
    segmento_selecionado = st.sidebar.selectbox('Selecione um Segmento:', segmentos_ajustados)
    if segmento_selecionado != 'Nenhum':
        if st.button('Mostrar Clientes'):
            segmento_numero = int(segmento_selecionado.split()[-1])
            clientes_segmento = segmentacao[segmentacao['segmento'] == segmento_numero]
            clientes_ids = clientes_segmento['IDCliente'].unique()
            st.write(f"Clientes no {segmento_selecionado}:")

            # Mostrar produtos recomendados para o segmento
            st.write("Produtos recomendados:")
            produtos_recomendados = clientes_segmento['ProdutosRecomendados'].iloc[0]
            for produto in eval(produtos_recomendados):
                categoria = produtos[produtos['CodigoProduto'] == str(produto)]['Categoria']
                if not categoria.empty:
                    categoria = categoria.values[0]
                    st.write(f"  - Produto: {produto}, Categoria: {categoria}")
                else:
                    st.write(f"  - Produto: {produto}, Categoria: Não encontrada")

            # Mostrar clientes
            st.write("Clientes:")
            for cliente in clientes_ids:
                st.write(f"Cliente {cliente}")

# Seção de Busca de Cliente
elif opcao == 'Informações por Código do Cliente':
    st.header('Informações por Código do Cliente')
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

# Seção de Análises e Insights
elif opcao == 'Análises e Insights':
    st.header('Análises e Insights')
    st.write("""
    Este relatório apresenta uma análise detalhada das transações de uma empresa de varejo online do Reino Unido, especializada na venda de presentes únicos para todas as ocasiões. O conjunto de dados abrange todas as transações ocorridas entre 01/12/2010 e 09/12/2011, com muitos clientes sendo atacadistas. O objetivo desta análise é identificar padrões de vendas, comportamento de compra dos clientes e áreas de melhoria para aumentar a receita e a fidelidade dos clientes.
    """)
    st.header('Análise da Receita')
    st.subheader('Distribuição da Receita por País')
    st.write("""
    O país que gerou a maior receita foi o **Reino Unido**, com uma receita total de $6,747,156.15. Isso indica que a maior parte das vendas ocorre no mercado local, sugerindo uma forte base de clientes domésticos. Países como Alemanha, França e Países Baixos também contribuíram significativamente para a receita, representando mercados importantes para a empresa.
    """)
    st.subheader('Receita Diária')
    st.write("""
    A análise da receita diária revela picos significativos e tendências sazonais, indicando períodos de alta demanda, possivelmente relacionados a promoções ou eventos específicos. Por exemplo, observou-se um pico significativo em dezembro de 2010, provavelmente devido às compras de fim de ano. Este insight pode ser utilizado para planejar campanhas de marketing e otimizar a alocação de estoque.
    """)
    st.subheader('Receita Mensal')
    st.write("""
    A análise da receita mensal mostra um padrão sazonal claro, com picos de receita em determinados meses do ano, como novembro e dezembro, possivelmente devido às compras de final de ano. Observa-se que a receita em dezembro de 2011 foi a mais alta do período analisado, destacando a importância das promoções de fim de ano.
    """)
    st.header('Análise de Produtos')
    st.subheader('Produtos Mais Vendidos')
    st.write("""
    Os 10 produtos mais vendidos foram identificados, sendo o produto 23843 o mais popular com 80,995 unidades vendidas. Outros produtos de destaque incluem:
    - Produto 23166: 77,907 unidades vendidas
    - Produto 84077: 54,319 unidades vendidas
    - Produto 22197: 48,984 unidades vendidas
    - Produto 85099B: 46,040 unidades vendidas
    - Produto 85123A: 36,646 unidades vendidas
    - Produto 84879: 35,132 unidades vendidas
    - Produto 21212: 33,616 unidades vendidas
    - Produto 23084: 27,066 unidades vendidas
    - Produto 22492: 26,076 unidades vendidas
    Conhecer os produtos mais vendidos pode ajudar a empresa a focar suas estratégias de marketing e estoque nesses itens para maximizar as vendas.
    """)
    st.subheader('Produtos Mais Devolvidos')
    st.write("""
    A análise dos produtos mais devolvidos revela possíveis problemas com qualidade, descrição do produto ou expectativas dos clientes. Por exemplo, os produtos 22121, 84843 e 21774 foram os mais devolvidos, sugerindo que podem necessitar de atenção especial. Identificar os produtos com maior taxa de devolução pode ajudar a empresa a tomar medidas corretivas, como melhorar a descrição do produto, aumentar a qualidade ou ajustar as expectativas dos clientes através de uma comunicação mais clara.
    """)
    st.header('Análise do Comportamento dos Clientes')
    st.subheader('Ticket Médio')
    st.write("""
    O valor médio gasto por transação foi analisado para entender o comportamento de compra dos clientes. O ticket médio identificado foi de aproximadamente $22.80. Estratégias como upselling e cross-selling podem ser implementadas para aumentar o ticket médio. Por exemplo, sugerir produtos complementares ou de maior valor durante o processo de compra pode incentivar os clientes a gastar mais.
    """)
    st.subheader('Top Clientes')
    st.write("""
    Os principais clientes foram identificados, com os maiores gastos contribuindo significativamente para a receita total. Os 5 principais clientes foram:
    - Cliente 146460: $280,206.02
    - Cliente 181020: $259,657.30
    - Cliente 174500: $194,390.79
    - Cliente 164460: $168,472.50
    - Cliente 149110: $143,711.17
    Manter esses clientes satisfeitos é crucial, e estratégias como programas de fidelidade, descontos exclusivos e atendimento personalizado podem ser eficazes para garantir a fidelidade desses clientes valiosos.
    """)
    st.header('Estratégias Recomendadas')
    st.write("""
    1. **Upselling e Cross-selling**: Sugerir produtos complementares ou de maior valor durante o processo de compra pode aumentar o ticket médio. Por exemplo, promover itens que frequentemente são comprados juntos.
    2. **Programas de Fidelidade**: Implementar programas de fidelidade que recompensem os clientes por compras recorrentes pode aumentar a retenção de clientes. Oferecer pontos de recompensa, descontos exclusivos e brindes pode incentivar os clientes a comprar com mais frequência.
    3. **Descontos Exclusivos e Ofertas Personalizadas**: Enviar ofertas exclusivas baseadas no histórico de compras dos clientes pode incentivar novas compras. Usar dados de compra para segmentar clientes e enviar promoções específicas pode aumentar a eficácia das campanhas de marketing.
    4. **Melhoria da Experiência do Cliente**: Garantir um processo de compra fácil e intuitivo, além de um serviço de atendimento ao cliente de alta qualidade, pode melhorar a satisfação do cliente. Investir em uma plataforma de e-commerce eficiente e treinamento de equipe de atendimento são passos importantes.
    5. **Engajamento Pós-Compra**: Enviar emails de agradecimento, solicitar feedback e sugerir novos produtos com base nas compras anteriores pode manter os clientes engajados e incentivá-los a realizar novas compras. Este engajamento contínuo ajuda a construir uma relação de longo prazo com os clientes.
    """)
    st.header('Conclusão')
    st.write("""
    A análise dos dados de vendas revelou insights valiosos sobre o comportamento dos clientes e a performance dos produtos. Implementar as estratégias recomendadas pode ajudar a aumentar a receita, melhorar a satisfação do cliente e fortalecer a fidelidade dos clientes. Este relatório fornece uma base sólida para decisões estratégicas que podem impulsionar o crescimento e a rentabilidade da empresa.
    """)

# Seção de Previsão de Vendas
elif opcao == 'Previsão de Vendas com Machine Learning':
    st.header('Previsão de Vendas com Machine Learning')
    meses_a_prever = st.sidebar.slider('Prever para quantos meses?', 1, 3, 1)
    if st.button('Prever Vendas'):
        modelo_treinado = prever_vendas(itens_fatura, meses_a_prever)
        if modelo_treinado:
            st.write("Modelo treinado e previsões feitas com sucesso!")



