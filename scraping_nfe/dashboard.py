import os
import django
import pandas as pd
import streamlit as st
import plotly.express as px
import re

# Configuração do ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scraping_nfe.settings')
django.setup()

from nfce.models import NotaFiscal, Item

# Função para carregar os dados do banco
def carregar_dados():
    # Carregar os dados dos itens, com informações relacionadas à nota fiscal
    itens = Item.objects.select_related('nota_fiscal').values(
        'descricao', 'quantidade', 'valor_total', 'nota_fiscal__data_emissao', 'nota_fiscal__categoria', 'nota_fiscal__razao_social'
    )
    
    # Criar um DataFrame para os itens
    df_itens = pd.DataFrame(list(itens))
    
    # Função para extrair a data da string "Data de Autorização: 18/09/2024 10:42:33"
    def extrair_data(data_str):
        if pd.isnull(data_str):
            return None
        match = re.search(r'(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})', data_str)
        if match:
            return match.group(1)
        return None

    # Aplicar a função para extrair a data correta da coluna 'nota_fiscal__data_emissao'
    df_itens['nota_fiscal__data_emissao'] = df_itens['nota_fiscal__data_emissao'].apply(extrair_data)
    
    # Converte a coluna 'nota_fiscal__data_emissao' para o formato datetime
    df_itens['nota_fiscal__data_emissao'] = pd.to_datetime(df_itens['nota_fiscal__data_emissao'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
    
    # Renomear as colunas para facilitar a manipulação
    df_itens.rename(columns={'nota_fiscal__data_emissao': 'data_emissao', 'nota_fiscal__categoria': 'categoria', 'nota_fiscal__razao_social': 'razao_social'}, inplace=True)

    # Carregar as notas fiscais diretamente, com as informações de data de emissão e categoria
    notas_fiscais = NotaFiscal.objects.values(
        'id', 'data_emissao', 'categoria', 'valor_total_produtos'
    )
    
    # Criar um DataFrame para as notas fiscais
    df_notas = pd.DataFrame(list(notas_fiscais))
    
    # Aplicar a função para extrair a data correta da coluna 'data_emissao' das notas fiscais
    df_notas['data_emissao'] = df_notas['data_emissao'].apply(extrair_data)
    
    # Converte a coluna 'data_emissao' para o formato datetime
    df_notas['data_emissao'] = pd.to_datetime(df_notas['data_emissao'], format='%d/%m/%Y %H:%M:%S', errors='coerce')

    # Verificar os dados carregados
    #st.write("Dados carregados dos itens:", df_itens.head())  # Exibir as primeiras linhas dos itens
    #st.write("Dados carregados das notas fiscais:", df_notas.head())  # Exibir as primeiras linhas das notas fiscais
    
    # Combinar os dados dos itens e das notas fiscais (se necessário, pode-se realizar merges ou joins)
    df_combinado = pd.concat([df_itens, df_notas], axis=0, ignore_index=True)
    
    return df_combinado

# Função para calcular os indicadores de gasto mensal
def calcular_gastos_mensais(df):
    # Agrupa os dados por mês/ano para calcular o gasto mensal
    gasto_mensal = df.groupby(df['data_emissao'].dt.to_period('M'))['valor_total'].sum().reset_index()
    gasto_mensal.rename(columns={'valor_total': 'Gasto Total'}, inplace=True)
    return gasto_mensal

# Função para calcular o gasto total e a média de gastos
def calcular_indicadores(df):
    if df.empty:
        return 0, 0

    gasto_total = df['valor_total'].sum()
    media_gastos = df['valor_total'].mean()
    return gasto_total, media_gastos

# Função para calcular a data da última compra
def calcular_ultima_compra(df):
    if df.empty:
        return None
    ultima_compra = df['data_emissao'].max()
    return ultima_compra

# Função para calcular o número total de compras
def calcular_total_compras(df):
    return df['data_emissao'].nunique()

# Função para exibir a razão social com mais compras
def razao_social_com_mais_compras(df_filtrado):
    razao_social_freq = df_filtrado.groupby('razao_social')['valor_total'].sum().reset_index()
    razao_social_freq = razao_social_freq.sort_values(by='valor_total', ascending=False)
    return razao_social_freq

# Função para comparar preços de itens entre diferentes razões sociais
def comparar_precos(df_filtrado):
    precos_comparacao = df_filtrado.groupby(['descricao', 'razao_social'])['valor_total'].mean().unstack().fillna(0)
    return precos_comparacao

# Função para aplicar o tema globalmente
def aplicar_tema_completo(tema_noite):
    if tema_noite:
        st.markdown("""
            <style>
                body, .stApp {
                    background-color: #1E1E1E; /* Fundo preto */
                    color: #E0E0E0;
                }
                .css-1d391kg, .stSidebar, .stContainer {
                    background-color: #2C2C2C; /* Cinza escuro */
                    color: #E0E0E0;
                }
                .stButton>button {
                    background-color: #444444;
                    color: #E0E0E0;
                    border-radius: 30px;
                    padding: 10px 30px;
                }
                .stButton>button:hover {
                    background-color: #555555;
                }
                .stMetric-value, .stMetric-label, h1, h2, h3, p, span {
                    color: #E0E0E0 !important; /* Dourado */
                }
                .stAlert {
                    background-color: #333333;
                    color: #E0E0E0 !important;
                }
                .stDataFrame, .stTable, .stPlotlyChart {
                    background-color: #2E2E2E; /* DataFrames e tabelas com fundo preto */
                    color: #E0E0E0 !important;
                    border: 1px solid #444444;
                }
                .stTextInput, .stNumberInput, .stSelectbox {
                    background-color: #444444; /* Campos de input escuros */
                    color: #444444;
                    border: 1px solid #555555;
                }
                .stSidebar .stButton>button, .stSidebar .stNumberInput input, .stSidebar .stTextInput input, .stSidebar select {
                    background-color: #444444; /* Botões e selects escuros */
                    color: #E0E0E0;
                }
                .stCheckbox>div>label, .stRadio>div>label, .stSelectbox>div>label, .stSidebar {
                    color: #E0E0E0 !important;
                }
                .stSidebar h2, .stSidebar h3 {
                    color: #E0E0E0 !important;
                }
                .stMetric-value {
                    color: #E0E0E0 !important;
                    font-size: 2em;
                }
                .stMetric-label {
                    color: #E0E0E0 !important;
                }
                header.stAppHeader {
                    background-color: #444444;
                    color: #E0E0E0;
                    border-bottom: 1px solid #E0E0E0;
                }
                header.stAppHeader button {
                    background-color: #555555;
                    color: #E0E0E0 !important;
                }
                .st-emotion-cache-1wivap2, .st-cx {
    
    color: #E0E0E0; /* Texto claro */
    
}

            </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
                body, .stApp {
                    background-color: #FFFFFF;
                    color: #000000;
                }
                .css-1d391kg, .stSidebar, .stContainer {
                    background-color: #F0F0F0;
                    color: #000000;
                }
                .stButton>button {
                    background-color: #E0E0E0;
                    color: #000000;
                    border-radius: 30px;
                    padding: 10px 30px;
                }
                .stButton>button:hover {
                    background-color: #CCCCCC;
                }
                .stMetric-value, .stMetric-label, h1, h2, h3, p, span {
                    color: #000000 !important;
                }
                .stAlert {
                    background-color: #F0F0F0;
                    color: #000000 !important;
                }
                .stDataFrame, .stTable, .stPlotlyChart {
                    background-color: #FFFFFF;
                    color: #000000 !important;
                }
                .stTextInput, .stNumberInput, .stSelectbox {
                    background-color: #FFFFFF;
                    color: #000000;
                    border: 1px solid #CCCCCC;
                }
                .stSidebar .stButton>button, .stSidebar .stNumberInput input, .stSidebar .stTextInput input, .stSidebar select {
                    background-color: #FFFFFF;
                    color: #000000;
                }
                .stCheckbox>div>label, .stRadio>div>label, .stSelectbox>div>label, .stSidebar {
                    color: #000000 !important;
                }
                .stSidebar h2, .stSidebar h3 {
                    color: #000000 !important;
                }
                .stMetric-value {
                    color: #007BFF !important;
                    font-size: 1.8em !important;
                }
                header.stAppHeader {
                    background-color: #FFFFFF;
                    color: #000000;
                    border-bottom: 1px solid #000000;
                }
                header.stAppHeader button {
                    background-color: #E0E0E0;
                    color: #000000 !important;
                }
            </style>
        """, unsafe_allow_html=True)





# Função para exibir o alerta com a cor correta e formatação adequada
def exibir_alerta_meta(gasto_total, meta_gasto):
    if gasto_total >= meta_gasto:
        st.error(f"🚨 Você ultrapassou a meta de R$ {meta_gasto:,.2f}.")
    elif gasto_total >= meta_gasto * 0.9:
        st.warning(f"⚠️ Você está próximo de atingir a meta de gasto. Gasto atual: R$ {gasto_total:,.2f}.")
    else:
        st.success(f"✅ Você está dentro da meta de gasto. Gasto atual: R$ {gasto_total:,.2f}.")
# Função para gerar sugestões de economia
def gerar_sugestoes_economia(df_filtrado):
    # Agrupar os dados por descrição do item e razão social, calculando a média de preços
    precos_por_item = df_filtrado.groupby(['descricao', 'razao_social'])['valor_total'].mean().unstack()

    # Encontrar o menor preço para cada item
    itens_mais_baratos = precos_por_item.idxmin(axis=1)  # Razão social com menor preço para cada item
    precos_mais_baratos = precos_por_item.min(axis=1)  # Menor preço para cada item

    # Gerar recomendações
    recomendacoes = []
    for item, supermercado in itens_mais_baratos.items():
        preco = precos_mais_baratos[item]
        recomendacoes.append({
            'item': item,
            'supermercado': supermercado,
            'preco': preco
        })

    return recomendacoes

# Função para exibir sugestões de economia com estilo
def exibir_sugestoes(df_filtrado):
    st.subheader("💡 Sugestões de Economia")

    sugestoes = gerar_sugestoes_economia(df_filtrado)
    
    if sugestoes:
        # Custom CSS para melhorar o estilo visual
        st.markdown("""
            <style>
                .sugestao-box {
                    background-color: #f0f0f0;
                    padding: 10px;
                    border-radius: 8px;
                    margin-bottom: 10px;
                    border-left: 5px solid #36a2eb;
                }
                .sugestao-box h4 {
                    margin: 0;
                    color: #1e88e5;
                }
                .sugestao-box p {
                    margin: 0;
                    color: #333;
                }
            </style>
        """, unsafe_allow_html=True)

        # Exibindo cada sugestão dentro de uma caixa personalizada
        for sugestao in sugestoes:
            st.markdown(f"""
                <div class="sugestao-box">
                    <h4>Item: {sugestao['item']}</h4>
                    <p>Supermercado mais barato: <strong>{sugestao['supermercado']}</strong></p>
                    <p>Preço: <strong>R$ {sugestao['preco']:.2f}</strong></p>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.write("Nenhuma sugestão disponível.")


# Função para visualizar gráficos interativos
def graficos_interativos(df_filtrado):
    fig_linha = px.line(df_filtrado, x='data_emissao', y='valor_total', title='Gastos ao Longo do Tempo', markers=True)
    fig_area = px.area(df_filtrado, x='data_emissao', y='valor_total', title='Área Acumulada de Gastos')
    
    fig_linha.update_layout(xaxis_rangeslider_visible=True)
    fig_area.update_layout(xaxis_rangeslider_visible=True)
    
    return fig_linha, fig_area

# Função para exibir o dashboard com personalização completa
def exibir_dashboard():
    st.sidebar.image("logo_dash.png", width=200)  # Insira o caminho correto da logo aqui
    st.title('Dashboard Financeiro')

    # Carregar dados
    df = carregar_dados()

    if not df.empty:
        # Adicionar seletor de tema
        tema_noite = st.sidebar.checkbox("Modo Noite", value=False)

        # Aplicar o tema ao dashboard
        aplicar_tema_completo(tema_noite)

        # Adicionar filtros para seleção de mês, ano e categoria
        st.sidebar.header("Filtros")
        meses_disponiveis = df['data_emissao'].dt.month.unique()
        anos_disponiveis = df['data_emissao'].dt.year.unique()
        categorias_disponiveis = df['categoria'].unique()

        mes_selecionado = st.sidebar.selectbox("Selecione o mês", options=meses_disponiveis, format_func=lambda x: f"Mês {x}" if pd.notnull(x) else "Todos")
        ano_selecionado = st.sidebar.selectbox("Selecione o ano", options=anos_disponiveis, format_func=lambda x: f"{x}" if pd.notnull(x) else "Todos")
        categoria_selecionada = st.sidebar.selectbox("Selecione a categoria", options=categorias_disponiveis, format_func=lambda x: x if pd.notnull(x) else "Todas")

        # Filtrar os dados com base no mês, ano e categoria selecionados
        df_filtrado = df.copy()
        if pd.notnull(mes_selecionado):
            df_filtrado = df_filtrado[df_filtrado['data_emissao'].dt.month == mes_selecionado]
        if pd.notnull(ano_selecionado):
            df_filtrado = df_filtrado[df_filtrado['data_emissao'].dt.year == ano_selecionado]
        if pd.notnull(categoria_selecionada):
            df_filtrado = df_filtrado[df_filtrado['categoria'] == categoria_selecionada]

        # Exibir a razão social com mais compras
        if categoria_selecionada == 'alimentacao':
            st.subheader("Razão Social com mais Compras (Alimentação)")
            razao_social_mais_compras = razao_social_com_mais_compras(df_filtrado)
            st.write(razao_social_mais_compras)
            
            # Exibir comparação de preços por razão social
            st.subheader("Comparação de Preços de Itens entre Razões Sociais")
            precos_comparacao = comparar_precos(df_filtrado)
            st.dataframe(precos_comparacao)

        # Data da última compra
        ultima_compra = calcular_ultima_compra(df_filtrado)
        if ultima_compra:
            st.subheader(f"Data da Última Compra: {ultima_compra.strftime('%d/%m/%Y')}")
        else:
            st.subheader("Nenhuma compra registrada.")

        # Total de compras realizadas
        total_compras = calcular_total_compras(df_filtrado)
        st.subheader(f"Total de Compras Realizadas: {total_compras}")

        # Meta de gasto por categoria
        st.sidebar.header(f"Meta de Gasto Mensal para {categoria_selecionada}")
        meta_gasto = st.sidebar.number_input(f"Defina a meta de gasto mensal para {categoria_selecionada} (R$)", min_value=0.0, value=1000.0, step=100.0)

        # Calcular indicadores
        gasto_total, media_gastos = calcular_indicadores(df_filtrado)
        gasto_mensal = calcular_gastos_mensais(df_filtrado)

        # Exibir alerta de acordo com a proximidade da meta
        exibir_alerta_meta(gasto_total, meta_gasto)

        # Indicadores resumidos
        st.subheader("Indicadores de Resumo")
        col1, col2 = st.columns(2)
        col1.metric("Gasto Total Acumulado", f"R$ {gasto_total:,.2f}")
        col2.metric("Média de Gastos", f"R$ {media_gastos:,.2f}")

        # Gráfico de Gastos Mensais
        st.subheader("Gastos Mensais")
        if not gasto_mensal.empty:
            fig_gastos_mensais = px.bar(
                gasto_mensal, x=gasto_mensal['data_emissao'].astype(str), y='Gasto Total',
                labels={'x': 'Mês', 'Gasto Total': 'Gasto Total'},
                title="Gasto Mensal Acumulado"
            )
            st.plotly_chart(fig_gastos_mensais)
        else:
            st.write("Nenhum dado disponível para o gráfico de gastos mensais.")

        # Gráfico de Categorias de Gastos
        st.subheader("Categorias de Gastos")
        categorias_gastos = df_filtrado.groupby('categoria')['valor_total'].sum()
        if not categorias_gastos.empty:
            fig_categorias = px.pie(
                categorias_gastos, values='valor_total', names=categorias_gastos.index,
                title="Distribuição de Gastos por Categoria"
            )
            st.plotly_chart(fig_categorias)
        st.subheader("Sugestões de Economia")
        economias_sugeridas = gerar_sugestoes_economia(df_filtrado)
        st.write(economias_sugeridas)

        fig_linha, fig_area = graficos_interativos(df_filtrado)
        st.subheader("Visualização de Gráficos Interativos")
        st.plotly_chart(fig_linha)
        st.plotly_chart(fig_area)
    else:
            st.write("Nenhum dado disponível para exibir no dashboard.")

# Chamar a função para exibir o dashboard
if __name__ == "__main__":
    exibir_dashboard()
