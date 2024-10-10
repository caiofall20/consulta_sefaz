import os
import django
import pandas as pd
import streamlit as st
import plotly.express as px

# Configuração do ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scraping_nfe.settings')
django.setup()

from nfce.models import Item

# Função para carregar os dados do banco
def carregar_dados():
    itens = Item.objects.select_related('nota_fiscal').values(
        'descricao', 'quantidade', 'valor_total', 'nota_fiscal__data_emissao', 'nota_fiscal__categoria'
    )
    df = pd.DataFrame(list(itens))
    df.rename(columns={'nota_fiscal__data_emissao': 'data_emissao', 'nota_fiscal__categoria': 'categoria'}, inplace=True)
    df['data_emissao'] = pd.to_datetime(df['data_emissao'], errors='coerce')
    return df

# Função para calcular os indicadores
def calcular_indicadores(df):
    if df.empty:
        return 0, 0, pd.Series(dtype='float64')

    gasto_total = df['valor_total'].sum()
    media_gastos = df['valor_total'].mean()
    gasto_mensal = df.groupby(df['data_emissao'].dt.to_period('M'))['valor_total'].sum()
    return gasto_total, media_gastos, gasto_mensal

# Função para exibir o alerta com a cor correspondente
def exibir_alerta_meta(gasto_total, meta_gasto):
    if gasto_total >= meta_gasto:
        st.error(f"🚨 Atenção! O gasto total de R$ {gasto_total:,.2f} ultrapassou a meta de R$ {meta_gasto:,.2f}.")
    elif gasto_total >= meta_gasto * 0.9:
        st.warning(f"⚠️ Você está próximo de atingir a meta de gasto. Gasto atual: R$ {gasto_total:,.2f}")
    else:
        st.success(f"✅ Você está dentro da meta de gasto. Gasto atual: R$ {gasto_total:,.2f}")

# Função para exibir o dashboard com tematização automotiva
def exibir_dashboard():
    st.title('Dashboard Financeiro - Tema Automotivo 🚗')

    # Carregar dados
    df = carregar_dados()

    if not df.empty:
        # Adicionar filtros para seleção de mês, ano e categoria
        st.sidebar.header("Filtros")
        meses_disponiveis = df['data_emissao'].dt.month.unique()
        anos_disponiveis = df['data_emissao'].dt.year.unique()
        categorias_disponiveis = df['categoria'].unique()

        mes_selecionado = st.sidebar.selectbox("Selecione o mês", options=meses_disponiveis, format_func=lambda x: f"Mês {x}" if pd.notnull(x) else "Todos")
        ano_selecionado = st.sidebar.selectbox("Selecione o ano", options=anos_disponiveis, format_func=lambda x: f"{x}" if pd.notnull(x) else "Todos")
        categoria_selecionada = st.sidebar.selectbox("Selecione a categoria", options=categorias_disponiveis, format_func=lambda x: x if pd.notnull(x) else "Todas")

        # Filtrar os dados com base no mês, ano e categoria selecionados
        if pd.notnull(mes_selecionado) and pd.notnull(ano_selecionado):
            df_filtrado = df[(df['data_emissao'].dt.month == mes_selecionado) & (df['data_emissao'].dt.year == ano_selecionado)]
        else:
            df_filtrado = df

        if pd.notnull(categoria_selecionada):
            df_filtrado = df_filtrado[df_filtrado['categoria'] == categoria_selecionada]

        # Meta de gasto mensal
        st.sidebar.header("Meta de Gasto Mensal")
        meta_gasto = st.sidebar.number_input("Defina a meta de gasto mensal (R$)", min_value=0.0, value=1000.0, step=100.0)

        # Calcular indicadores
        gasto_total, media_gastos, gasto_mensal = calcular_indicadores(df_filtrado)

        # Exibir alerta de acordo com a proximidade da meta
        exibir_alerta_meta(gasto_total, meta_gasto)

        # Indicadores resumidos
        st.subheader("Indicadores de Resumo")
        col1, col2 = st.columns(2)
        col1.metric("Gasto Total Acumulado", f"R$ {gasto_total:,.2f}")
        col2.metric("Média de Gastos", f"R$ {media_gastos:,.2f}")

        # Gráfico de Gastos Mensais com cores automotivas
        st.subheader("Gastos Mensais")
        if not gasto_mensal.empty:
            fig_gastos_mensais = px.bar(
                gasto_mensal, x=gasto_mensal.index.astype(str), y='valor_total', 
                labels={'x': 'Mês', 'valor_total': 'Gasto Total'},
                title="Gasto Mensal Acumulado",
                color_discrete_sequence=["#2E8B57"]  # Verde para representar o tema automotivo
            )
            st.plotly_chart(fig_gastos_mensais)
        else:
            st.write("Nenhum dado disponível para o gráfico de gastos mensais.")

        # Gráfico de Categorias de Gastos com tema automotivo
        st.subheader("Categorias de Gastos")
        categorias_gastos = df_filtrado.groupby('categoria')['valor_total'].sum()
        if not categorias_gastos.empty:
            fig_categorias = px.pie(
                categorias_gastos, values='valor_total', names=categorias_gastos.index, 
                title="Distribuição de Gastos por Categoria",
                color_discrete_sequence=px.colors.sequential.RdBu  # Cores para o tema automotivo
            )
            st.plotly_chart(fig_categorias)
        else:
            st.write("Nenhum dado disponível para o gráfico de categorias de gastos.")

    else:
        st.write("Nenhum dado disponível para exibir no dashboard.")

# Chamar a função para exibir o dashboard
if __name__ == "__main__":
    exibir_dashboard()
