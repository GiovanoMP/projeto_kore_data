import streamlit as st

# Título do app
st.title('Relatório de Análise de Dados de Vendas')

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
