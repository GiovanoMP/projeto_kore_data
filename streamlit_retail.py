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
st.title('Relatório de Vendas')

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

# Filtrar dados por data
itens_fatura_filtrado = itens_fatura[(itens_fatura['DataFatura'].dt.date >= start_date) & (itens_fatura['DataFatura'].dt.date <= end_date)]

# Filtrar dados por país
if pais_selecionado != 'Global':
    itens_fatura_filtrado = itens_fatura_filtrado.merge(clientes, on='IDCliente')
    itens_fatura_filtrado = itens_fatura_filtrado[itens_fatura_filtrado['Pais'] == pais_selecionado]
else:
    itens_fatura_filtrado = itens_fatura_filtrado.merge(clientes, on='IDCliente')

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

# Seção de Indicadores de Vendas
st.header('Indicadores de Vendas')
st.write(f"Receita Total: ${calcular_receita_total(itens_fatura_filtrado):,.2f}")

st.subheader('Receita Diária')
st.line_chart(calcular_receita_diaria(itens_fatura_filtrado, start_date, end_date))

st.subheader('Receita Mensal')
st.line_chart(calcular_receita_mensal(itens_fatura_filtrado))

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

# Título do app
st.title('Relatório Final | Insights da Análise de Dados de Vendas')

# Análise da Receita
st.header('2. Análise da Receita')

st.subheader('2.1. Distribuição da Receita por País')
st.write("""
O país que gerou a maior receita foi o **Reino Unido**. Isso indica que a maior parte das vendas ocorre no mercado local, sugerindo uma forte base de clientes domésticos. Países como Alemanha, França e Países Baixos também contribuíram significativamente para a receita, representando mercados importantes para a empresa.
""")

st.subheader('2.2. Receita Diária')
st.write("""
A análise da receita diária revela picos significativos e tendências sazonais, indicando períodos de alta demanda, possivelmente relacionados a promoções ou eventos específicos. Esses picos podem ser utilizados para planejar campanhas de marketing e otimizar a alocação de estoque. Por exemplo, observou-se um pico significativo em dezembro de 2010, provavelmente devido às compras de fim de ano.
""")

st.subheader('2.3. Receita Mensal')
st.write("""
A análise da receita mensal mostra um padrão sazonal claro, com picos de receita em determinados meses do ano, como novembro e dezembro, possivelmente devido às compras de final de ano. Este insight pode ser utilizado para planejar melhor as promoções sazonais e gerenciar o estoque de forma eficiente. Observa-se que a receita em dezembro de 2011 foi a mais alta do período analisado.
""")

# Análise de Produtos
st.header('3. Análise de Produtos')

st.subheader('3.1. Produtos Mais Vendidos')
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

st.subheader('3.2. Produtos Mais Devolvidos')
st.write("""
A análise dos produtos mais devolvidos revela possíveis problemas com qualidade, descrição do produto ou expectativas dos clientes. Por exemplo, os produtos 22121, 84843 e 21774 foram os mais devolvidos, sugerindo que podem necessitar de atenção especial. Identificar os produtos com maior taxa de devolução pode ajudar a empresa a tomar medidas corretivas, como melhorar a descrição do produto, aumentar a qualidade ou ajustar as expectativas dos clientes através de uma comunicação mais clara.
""")

# Análise do Comportamento dos Clientes
st.header('4. Análise do Comportamento dos Clientes')

st.subheader('4.1. Ticket Médio')
st.write("""
O valor médio gasto por transação foi analisado para entender o comportamento de compra dos clientes. O ticket médio identificado foi de aproximadamente £22.80. Estratégias como upselling e cross-selling podem ser implementadas para aumentar o ticket médio. Por exemplo, sugerir produtos complementares ou de maior valor durante o processo de compra pode incentivar os clientes a gastar mais.
""")

st.subheader('4.2. Top Clientes')
st.write("""
Os principais clientes foram identificados, com os maiores gastos contribuindo significativamente para a receita total. Os 5 principais clientes foram:
- Cliente 146460: £280,206.02
- Cliente 181020: £259,657.30
- Cliente 174500: £194,390.79
- Cliente 164460: £168,472.50
- Cliente 149110: £143,711.17

Manter esses clientes satisfeitos é crucial, e estratégias como programas de fidelidade, descontos exclusivos e atendimento personalizado podem ser eficazes para garantir a fidelidade desses clientes valiosos.
""")

# Estratégias Recomendadas
st.header('5. Estratégias Recomendadas')
st.write("""
1. **Upselling e Cross-selling**: Sugerir produtos complementares ou de maior valor durante o processo de compra pode aumentar o ticket médio.
2. **Programas de Fidelidade**: Implementar programas de fidelidade que recompensem os clientes por compras recorrentes pode aumentar a retenção de clientes.
3. **Descontos Exclusivos e Ofertas Personalizadas**: Enviar ofertas exclusivas baseadas no histórico de compras dos clientes pode incentivar novas compras.
4. **Melhoria da Experiência do Cliente**: Garantir um processo de compra fácil e intuitivo, além de um serviço de atendimento ao cliente de alta qualidade, pode melhorar a satisfação do cliente.
5. **Engajamento Pós-Compra**: Enviar emails de agradecimento, solicitar feedback e sugerir novos produtos com base nas compras anteriores pode manter os clientes engajados e incentivá-los a realizar novas compras.
""")

# Conclusão
st.header('6. Conclusão')
st.write("""
A análise dos dados de vendas revelou insights valiosos sobre o comportamento dos clientes e a performance dos produtos. Implementar as estratégias recomendadas pode ajudar a aumentar a receita, melhorar a satisfação do cliente e fortalecer a fidelidade dos clientes. Este relatório fornece uma base sólida para decisões estratégicas que podem impulsionar o crescimento e a rentabilidade da empresa.
""")

# Rodapé
st.write('Relatório gerado por Streamlit')
