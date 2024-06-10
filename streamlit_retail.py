import streamlit as st
import pandas as pd
from datetime import timedelta
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from xgboost import XGBRegressor
from scipy.stats import uniform, randint
import matplotlib.pyplot as plt

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
    ultima_compra = itens_fatura.groupby('IDCliente')['DataFatura'].max().reset_index()
    ultima_compra['DiasDesdeUltimaCompra'] = (data_referencia - ultima_compra['DataFatura']).dt.days
    return ultima_compra[['IDCliente', 'DiasDesdeUltimaCompra']]

# Função para prever vendas
def previsao_vendas(meses):
    # Pré-processamento de Dados
    itens_fatura['DataFatura'] = itens_fatura['DataFatura'].dt.to_period('D').astype('int64').astype(int)

    # Selecionar as Colunas Relevantes
    colunas_importantes = [
        'DataFatura', 'Quantidade', 'CategoriaPreco', 'Devolucao', 'Venda', 
        'PrecoUnitario', 'IDCliente', 'ValorTotal', 'segmento'
    ]
    df_treinamento_simplificado = itens_fatura[colunas_importantes]

    # Tratar a Coluna 'CategoriaPreco' (One-Hot Encoding)
    encoder = OneHotEncoder(handle_unknown='ignore')
    categoria_preco_encoded = encoder.fit_transform(df_treinamento_simplificado[['CategoriaPreco']]).toarray()
    categoria_preco_encoded_df = pd.DataFrame(categoria_preco_encoded, columns=encoder.get_feature_names_out(['CategoriaPreco']))
    df_treinamento_simplificado = pd.concat([df_treinamento_simplificado, categoria_preco_encoded_df], axis=1)
    df_treinamento_simplificado.drop('CategoriaPreco', axis=1, inplace=True)

    # Tratar valores ausentes
    df_treinamento_simplificado.dropna(inplace=True)

    # Adicionar features derivadas
    df_treinamento_simplificado['PrecoMedio'] = df_treinamento_simplificado['PrecoUnitario'] / df_treinamento_simplificado['Quantidade']
    df_treinamento_simplificado['NumComprasCliente'] = df_treinamento_simplificado.groupby('IDCliente')['Quantidade'].transform('sum')
    df_treinamento_simplificado['DiasDesdeUltimaCompra'] = df_treinamento_simplificado.groupby('IDCliente')['DataFatura'].transform(lambda x: x.max() - x)

    # Remover outliers
    q1 = df_treinamento_simplificado['Quantidade'].quantile(0.25)
    q3 = df_treinamento_simplificado['Quantidade'].quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    df_treinamento_simplificado = df_treinamento_simplificado[(df_treinamento_simplificado['Quantidade'] >= lower_bound) & (df_treinamento_simplificado['Quantidade'] <= upper_bound)]

    # Separar os Dados
    X = df_treinamento_simplificado.drop('Quantidade', axis=1)
    y = df_treinamento_simplificado['Quantidade']

    # Garantir que os nomes das colunas sejam strings
    X.columns = X.columns.astype(str)

    # Normalizar os Dados
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Função para previsão
    def previsao_vendas(meses):
        # Dividir em Treino e Teste
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

        # Definir o Modelo
        model = XGBRegressor(objective='reg:squarederror', random_state=42)

        # Definir o Grid de Hiperparâmetros
        param_dist = {
            'n_estimators': randint(100, 300),
            'learning_rate': uniform(0.01, 0.2),
            'max_depth': randint(3, 7),
            'min_child_weight': randint(1, 6),
            'subsample': uniform(0.6, 0.4),
            'colsample_bytree': uniform(0.6, 0.4)
        }

        # Randomized Search com Validação Cruzada
        random_search = RandomizedSearchCV(estimator=model, param_distributions=param_dist, n_iter=50, cv=3, n_jobs=-1, scoring='neg_mean_squared_error', random_state=42)
        random_search.fit(X_train, y_train)

        # Melhor Modelo
        best_model = random_search.best_estimator_

        # Avaliar o Melhor Modelo
        y_pred = best_model.predict(X_test)

        r2 = r2_score(y_test, y_pred)
        rmse = mean_squared_error(y_test, y_pred, squared=False)
        mae = mean_absolute_error(y_test, y_pred)
        
        return r2, rmse, mae, y_test, y_pred

# Título do app
st.title('Relatório de Vendas e Segmentação de Clientes')

# Menu lateral
st.sidebar.header('Menu')
opcao = st.sidebar.radio('Selecione uma opção:', ['Relatório de Vendas', 'Segmentação de Clientes', 'Informações por Código do Cliente', 'Análise de Churn', 'Análises e Insights', 'Previsão de Vendas'])

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

    # Seleção de categorias de produtos
    st.sidebar.header('Filtro de Categoria de Produtos')
    categorias_produtos = ['Nenhum'] + list(produtos['Categoria'].unique())
    categoria_produto_selecionada = st.sidebar.selectbox('Escolha uma Categoria de Produto:', categorias_produtos)

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

    # Filtrar dados por categoria de produto
    if categoria_produto_selecionada != 'Nenhum':
        itens_fatura_filtrado = itens_fatura_filtrado[itens_fatura_filtrado['Categoria'] == categoria_produto_selecionada]

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

# Seção de Análise de Churn
elif opcao == 'Análise de Churn':
    st.header('Análise de Churn')

    # Calcular o tempo desde a última compra
    data_referencia = pd.to_datetime(itens_fatura['DataFatura'].max())
    tempo_desde_ultima_compra = calcular_tempo_desde_ultima_compra(itens_fatura, data_referencia)

    # Fazer o join com o dataframe de clientes para obter os nomes dos clientes
    churn_data = tempo_desde_ultima_compra.merge(clientes, on='IDCliente')

    # Categorizar clientes por tempo desde a última compra
    churn_30_59 = churn_data[(churn_data['DiasDesdeUltimaCompra'] >= 30) & (churn_data['DiasDesdeUltimaCompra'] <= 59)]
    churn_60_89 = churn_data[(churn_data['DiasDesdeUltimaCompra'] >= 60) & (churn_data['DiasDesdeUltimaCompra'] <= 89)]
    churn_90_119 = churn_data[(churn_data['DiasDesdeUltimaCompra'] >= 90) & (churn_data['DiasDesdeUltimaCompra'] <= 119)]
    churn_120_180 = churn_data[(churn_data['DiasDesdeUltimaCompra'] >= 120) & (churn_data['DiasDesdeUltimaCompra'] <= 180)]
    churn_181_plus = churn_data[churn_data['DiasDesdeUltimaCompra'] > 180]

    # Seleção de categoria de churn
    st.sidebar.header('Filtro de Churn')
    opcao_churn = st.sidebar.radio('Selecione uma opção:', [
        '30 a 59 dias', '60 a 89 dias', '90 a 119 dias', '120 a 180 dias (Churn)', 'Mais de 181 dias (Churn)'
    ])

    if opcao_churn == '30 a 59 dias':
        st.subheader('Clientes que não compram há 30 a 59 dias:')
        st.dataframe(churn_30_59)
    elif opcao_churn == '60 a 89 dias':
        st.subheader('Clientes que não compram há 60 a 89 dias:')
        st.dataframe(churn_60_89)
    elif opcao_churn == '90 a 119 dias':
        st.subheader('Clientes que não compram há 90 a 119 dias:')
        st.dataframe(churn_90_119)
    elif opcao_churn == '120 a 180 dias (Churn)':
        st.subheader('Clientes que não compram há 120 a 180 dias (Churn):')
        st.dataframe(churn_120_180)
    elif opcao_churn == 'Mais de 181 dias (Churn)':
        st.subheader('Clientes que não compram há mais de 181 dias (Churn):')
        st.dataframe(churn_181_plus)

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
elif opcao == 'Informações por Código do Cliente':
    st.header('Informações por Código do Cliente')

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

# Seção de Análises e Insights
elif opcao == 'Análises e Insights':
    st.header('Análises e Insights')

    st.write("""
    Este relatório apresenta uma análise detalhada das transações de uma empresa de varejo online do Reino Unido, especializada na venda de presentes únicos para todas as ocasiões. O conjunto de dados abrange todas as transações ocorridas entre 01/12/2010 e 09/12/2011, com muitos clientes sendo atacadistas. O objetivo desta análise é identificar padrões de vendas, comportamento de compra dos clientes e áreas de melhoria para aumentar a receita e a fidelidade dos clientes.
    """)

    # Análise da Receita
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

    # Análise de Produtos
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

    # Análise do Comportamento dos Clientes
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

    # Estratégias Recomendadas
    st.header('Estratégias Recomendadas')
    st.write("""
    1. **Upselling e Cross-selling**: Sugerir produtos complementares ou de maior valor durante o processo de compra pode aumentar o ticket médio. Por exemplo, promover itens que frequentemente são comprados juntos.
       
    2. **Programas de Fidelidade**: Implementar programas de fidelidade que recompensem os clientes por compras recorrentes pode aumentar a retenção de clientes. Oferecer pontos de recompensa, descontos exclusivos e brindes pode incentivar os clientes a comprar com mais frequência.

    3. **Descontos Exclusivos e Ofertas Personalizadas**: Enviar ofertas exclusivas baseadas no histórico de compras dos clientes pode incentivar novas compras. Usar dados de compra para segmentar clientes e enviar promoções específicas pode aumentar a eficácia das campanhas de marketing.

    4. **Melhoria da Experiência do Cliente**: Garantir um processo de compra fácil e intuitivo, além de um serviço de atendimento ao cliente de alta qualidade, pode melhorar a satisfação do cliente. Investir em uma plataforma de e-commerce eficiente e treinamento de equipe de atendimento são passos importantes.

    5. **Engajamento Pós-Compra**: Enviar emails de agradecimento, solicitar feedback e sugerir novos produtos com base nas compras anteriores pode manter os clientes engajados e incentivá-los a realizar novas compras. Este engajamento contínuo ajuda a construir uma relação de longo prazo com os clientes.
    """)

    # Conclusão
    st.header('Conclusão')
    st.write("""
    A análise dos dados de vendas revelou insights valiosos sobre o comportamento dos clientes e a performance dos produtos. Implementar as estratégias recomendadas pode ajudar a aumentar a receita, melhorar a satisfação do cliente e fortalecer a fidelidade dos clientes. Este relatório fornece uma base sólida para decisões estratégicas que podem impulsionar o crescimento e a rentabilidade da empresa.
    """)

# Seção de Previsão de Vendas
elif opcao == 'Previsão de Vendas':
    st.header('Previsão de Vendas com Machine Learning')

    # Seleção de período para previsão
    st.sidebar.header('Período de Previsão')
    meses = st.sidebar.selectbox('Selecione o número de meses para previsão:', [1, 2, 3, 4, 5, 6])

    # Executar previsão
    r2, rmse, mae, y_test, y_pred = previsao_vendas(meses)

    # Exibir métricas de avaliação
    st.write(f"Período de Previsão: {meses} meses")
    st.write(f"R²: {r2:.2f}")
    st.write(f"RMSE: {rmse:.2f}")
    st.write(f"MAE: {mae:.2f}")

    # Visualizar os Resultados
    plt.figure(figsize=(10, 5))
    plt.scatter(y_test, y_pred, alpha=0.3)
    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--')
    plt.xlabel('Valor Real')
    plt.ylabel('Previsão')
    plt.title('Comparação entre Valor Real e Previsão')
    st.pyplot(plt)

    plt.figure(figsize=(10, 5))
    plt.scatter(y_test, y_test - y_pred, alpha=0.3)
    plt.axhline(y=0, color='r', linestyle='--')
    plt.xlabel('Valor Real')
    plt.ylabel('Resíduo')
    plt.title('Gráfico de Resíduos')
    st.pyplot(plt)

# Instruções para uso:
st.sidebar.write("### Instruções para uso:")
st.sidebar.write("1. **Relatório de Vendas**: Utilize filtros para selecionar a data, categoria de preço, país e categoria de produto. Visualize indicadores de vendas, clientes e produtos, além de análises temporais.")
st.sidebar.write("2. **Análise de Churn**: Use o filtro de churn para selecionar clientes que não compram há um certo período e visualizá-los.")
st.sidebar.write("3. **Segmentação de Clientes**: Selecione um segmento para visualizar clientes e seus produtos recomendados.")
st.sidebar.write("4. **Informações por Código do Cliente**: Digite o ID do cliente para visualizar informações detalhadas, incluindo país, valor total de compras e últimos produtos comprados.")
st.sidebar.write("5. **Análises e Insights**: Veja uma análise detalhada das transações, comportamento de compra e estratégias recomendadas.")
st.sidebar.write("6. **Previsão de Vendas**: Selecione o número de meses para a previsão de vendas e visualize os resultados.")


