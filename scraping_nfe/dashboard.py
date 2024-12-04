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

    # Combinar os dados dos itens e das notas fiscais (se necessário, pode-se realizar merges ou joins)
    df_combinado = pd.concat([df_itens, df_notas], axis=0, ignore_index=True)
    
    return df_combinado

# Função para calcular os indicadores de gasto mensal
def calcular_gastos_mensais(df):
    if df.empty:
        return pd.DataFrame()
        
    try:
        # Converter a coluna de data para datetime se necessário
        df['data_emissao'] = pd.to_datetime(df['data_emissao'])
        
        # Criar uma coluna com o primeiro dia de cada mês
        df['mes'] = df['data_emissao'].dt.to_period('M').astype(str)
        
        # Agrupa os dados por mês para calcular o gasto mensal
        gasto_mensal = df.groupby('mes')['valor_total'].sum().reset_index()
        
        # Converter a coluna 'mes' de volta para datetime
        gasto_mensal['mes'] = pd.to_datetime(gasto_mensal['mes'])
        
        # Renomear as colunas
        gasto_mensal.columns = ['data_emissao', 'valor_total']
        
        # Ordenar por data
        gasto_mensal = gasto_mensal.sort_values('data_emissao')
        
        return gasto_mensal
    except Exception as e:
        st.error(f"Erro ao calcular gastos mensais: {str(e)}")
        return pd.DataFrame()

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

# Função para gerar sugestões de economia
def gerar_sugestoes_economia(df_filtrado):
    try:
        # Criar uma cópia do DataFrame para evitar alterações no original
        df = df_filtrado.copy()

        # Converter colunas para numérico e calcular valor unitário
        df['valor_total'] = pd.to_numeric(df['valor_total'], errors='coerce')
        df['quantidade'] = pd.to_numeric(df['quantidade'], errors='coerce')
        df['valor_unitario'] = df['valor_total'] / df['quantidade']

        # Remover valores inválidos
        df = df[df['valor_unitario'] > 0]

        # Agrupar por produto e estabelecimento
        precos_medios = df.groupby(['descricao', 'razao_social'])['valor_unitario'].mean().reset_index()
        
        # Encontrar produtos similares
        grupos_similares = encontrar_produtos_similares(precos_medios)
        
        # Organizar sugestões por estabelecimento
        sugestoes = {}
        comparacoes = []
        
        # Para cada grupo de produtos similares, verificar diferenças de preço
        for desc_base, produtos in grupos_similares.items():
            if len(produtos) > 1:  # Se o mesmo produto aparece em lugares diferentes
                precos = [(p['razao_social'], p['valor_unitario'], p['descricao']) for p in produtos]
                precos.sort(key=lambda x: x[1])  # Ordenar por preço
                
                # Se há diferença de pelo menos 5%
                if precos[-1][1] > precos[0][1] * 1.05:
                    economia = precos[-1][1] - precos[0][1]
                    economia_percentual = (economia / precos[-1][1]) * 100
                    comparacoes.append({
                        'produto_base': desc_base,
                        'melhor_preco': {
                            'estabelecimento': precos[0][0],
                            'preco': precos[0][1],
                            'descricao': precos[0][2]
                        },
                        'pior_preco': {
                            'estabelecimento': precos[-1][0],
                            'preco': precos[-1][1],
                            'descricao': precos[-1][2]
                        },
                        'economia_percentual': economia_percentual
                    })
        
        # Para cada estabelecimento, pegar seus produtos mais baratos
        for estabelecimento in precos_medios['razao_social'].unique():
            produtos_estabelecimento = precos_medios[precos_medios['razao_social'] == estabelecimento]
            produtos_ordenados = produtos_estabelecimento.sort_values('valor_unitario')
            melhores_produtos = produtos_ordenados.head(5)
            
            sugestoes[estabelecimento] = [
                {
                    'produto': row['descricao'],
                    'preco': row['valor_unitario']
                }
                for _, row in melhores_produtos.iterrows()
            ]
        
        return sugestoes, comparacoes

    except Exception as e:
        st.error(f"Erro ao gerar sugestões: {str(e)}")
        return {}, []

def limpar_descricao(descricao):
    """Remove variações comuns na descrição do produto."""
    # Converter para minúsculo
    desc = descricao.lower()
    
    # Remover variações de embalagem
    desc = desc.replace(' - 1x', ' ').replace('1x', '')
    desc = desc.replace('refri ', 'refrig ')  # Padronizar refrigerante
    
    # Remover caracteres especiais e espaços extras
    import re
    desc = re.sub(r'[^\w\s]', ' ', desc)
    desc = ' '.join(desc.split())
    
    return desc

def encontrar_produtos_similares(produtos_df):
    """Agrupa produtos similares baseado na descrição."""
    grupos_similares = {}
    
    for _, row in produtos_df.iterrows():
        desc_original = row['descricao']
        desc_limpa = limpar_descricao(desc_original)
        
        # Procurar por um grupo existente que contenha uma descrição similar
        grupo_encontrado = False
        for grupo_key in grupos_similares:
            # Melhorar a lógica de comparação
            palavras_grupo = set(grupo_key.split())
            palavras_desc = set(desc_limpa.split())
            palavras_comuns = palavras_grupo & palavras_desc
            
            # Se tiver pelo menos 70% de palavras em comum
            if len(palavras_comuns) >= min(len(palavras_grupo), len(palavras_desc)) * 0.7:
                grupos_similares[grupo_key].append({
                    'descricao': desc_original,
                    'razao_social': row['razao_social'],
                    'valor_unitario': row['valor_unitario']
                })
                grupo_encontrado = True
                break
        
        # Se não encontrou grupo similar, criar um novo
        if not grupo_encontrado:
            grupos_similares[desc_limpa] = [{
                'descricao': desc_original,
                'razao_social': row['razao_social'],
                'valor_unitario': row['valor_unitario']
            }]
    
    return grupos_similares

# Função para exibir as sugestões de economia
def exibir_sugestoes(df_filtrado):
    try:
        if df_filtrado.empty:
            st.info("Não há dados disponíveis para gerar sugestões de economia.")
            return

        sugestoes, comparacoes = gerar_sugestoes_economia(df_filtrado)

        # Exibir comparações de preços entre estabelecimentos
        if comparacoes:
            st.markdown("### 💡 Oportunidades de Economia")
            for comp in comparacoes:
                economia = comp['pior_preco']['preco'] - comp['melhor_preco']['preco']
                st.markdown(f"""
                **{comp['produto_base'].title()}**
                - ✅ Melhor preço: R$ {comp['melhor_preco']['preco']:.2f} em {comp['melhor_preco']['estabelecimento']}
                - ❌ Preço mais alto: R$ {comp['pior_preco']['preco']:.2f} em {comp['pior_preco']['estabelecimento']}
                - 💰 Economia possível: R$ {economia:.2f} ({comp['economia_percentual']:.1f}%)
                """)
            st.markdown("---")

        # Exibir produtos mais baratos por estabelecimento
        if not sugestoes:
            st.info("Não foram encontradas sugestões de preços para os estabelecimentos.")
            return

        st.markdown("### 🏪 Melhores Preços por Estabelecimento")
        
        # Criar colunas para mostrar estabelecimentos lado a lado
        num_estabelecimentos = len(sugestoes)
        if num_estabelecimentos > 0:
            colunas = st.columns(min(num_estabelecimentos, 3))  # Máximo de 3 colunas
            
            for idx, (estabelecimento, produtos) in enumerate(sugestoes.items()):
                col_idx = idx % 3  # Garante que voltamos à primeira coluna após 3 estabelecimentos
                with colunas[col_idx]:
                    st.markdown(f"#### {estabelecimento}")
                    st.markdown("🏷️ **Top 5 Melhores Preços:**")
                    
                    for i, produto in enumerate(produtos, 1):
                        preco = produto['preco']
                        nome_produto = produto['produto']
                        
                        # Criar uma caixa estilizada para cada produto
                        st.markdown(f"""
                        <div style='
                            padding: 10px;
                            border-radius: 5px;
                            margin: 5px 0;
                            background-color: rgba(0, 100, 0, 0.1);
                            border-left: 4px solid #006400;
                        '>
                            <span style='font-size: 1.1em;'>
                                <strong>{i}.</strong> {nome_produto}<br>
                                💰 <strong>R$ {preco:.2f}</strong>
                            </span>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("---")

    except Exception as e:
        st.error(f"Erro ao exibir sugestões: {e}")

# Função para aplicar o tema globalmente
def aplicar_tema_completo(tema_noite):
    if tema_noite:
        st.markdown("""
            <style>
                /* Configurações gerais */
                .main {
                    padding: 2rem;
                }
                
                /* Tema escuro */
                .stApp {
                    background-color: #1a1a1a;
                    color: #ffffff;
                }
                
                /* Cards e containers */
                div[data-testid="stMetricValue"], 
                div[data-testid="stMetricDelta"] {
                    background-color: #2d2d2d;
                    padding: 1rem;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                }
                
                /* Textos e títulos */
                h1, h2, h3, p, span, .stMarkdown {
                    color: #ffffff !important;
                }
                
                /* Inputs e seletores */
                .stSelectbox > div > div,
                .stMultiSelect > div > div {
                    background-color: #2d2d2d !important;
                    color: #ffffff !important;
                    border: 1px solid #404040 !important;
                    border-radius: 8px !important;
                }
                
                /* Gráficos e tabelas */
                .stPlotlyChart {
                    background-color: #2d2d2d !important;
                    border-radius: 10px;
                    padding: 1rem;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
                }
                
                /* Sidebar */
                section[data-testid="stSidebar"] {
                    background-color: #2d2d2d;
                    padding: 2rem 1rem;
                }
                
                /* Botões */
                .stButton > button {
                    background-color: #4a90e2 !important;
                    color: white !important;
                    border-radius: 8px !important;
                    border: none !important;
                    padding: 0.5rem 1rem !important;
                    transition: all 0.3s ease !important;
                }
                
                .stButton > button:hover {
                    background-color: #357abd !important;
                    transform: translateY(-2px);
                }
                
                /* Métricas */
                div[data-testid="stMetricValue"] {
                    font-size: 2.5rem !important;
                    font-weight: bold !important;
                    color: #4a90e2 !important;
                }
                
                /* Responsividade */
                @media (max-width: 768px) {
                    .main {
                        padding: 1rem;
                    }
                    
                    div[data-testid="stMetricValue"] {
                        font-size: 1.8rem !important;
                    }
                }
            </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
                /* Configurações gerais */
                .main {
                    padding: 2rem;
                }
                
                /* Tema claro */
                .stApp {
                    background-color: #ffffff;
                    color: #1a1a1a;
                }
                
                /* Cards e containers */
                div[data-testid="stMetricValue"], 
                div[data-testid="stMetricDelta"] {
                    background-color: #f8f9fa;
                    padding: 1rem;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }
                
                /* Textos e títulos */
                h1, h2, h3, p, span, .stMarkdown {
                    color: #1a1a1a !important;
                }
                
                /* Inputs e seletores */
                .stSelectbox > div > div,
                .stMultiSelect > div > div {
                    background-color: #ffffff !important;
                    color: #1a1a1a !important;
                    border: 1px solid #e0e0e0 !important;
                    border-radius: 8px !important;
                }
                
                /* Gráficos e tabelas */
                .stPlotlyChart {
                    background-color: #ffffff !important;
                    border-radius: 10px;
                    padding: 1rem;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }
                
                /* Sidebar */
                section[data-testid="stSidebar"] {
                    background-color: #f8f9fa;
                    padding: 2rem 1rem;
                }
                
                /* Botões */
                .stButton > button {
                    background-color: #4a90e2 !important;
                    color: white !important;
                    border-radius: 8px !important;
                    border: none !important;
                    padding: 0.5rem 1rem !important;
                    transition: all 0.3s ease !important;
                }
                
                .stButton > button:hover {
                    background-color: #357abd !important;
                    transform: translateY(-2px);
                }
                
                /* Métricas */
                div[data-testid="stMetricValue"] {
                    font-size: 2.5rem !important;
                    font-weight: bold !important;
                    color: #4a90e2 !important;
                }
                
                /* Responsividade */
                @media (max-width: 768px) {
                    .main {
                        padding: 1rem;
                    }
                    
                    div[data-testid="stMetricValue"] {
                        font-size: 1.8rem !important;
                    }
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

# Função para exibir o dashboard com personalização completa
def exibir_dashboard():
    # Configurar tema inicial
    tema_noite = st.session_state.get('tema_noite', True)
    
    st.set_page_config(
        page_title="Dashboard de Gastos",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Sidebar com controles
    with st.sidebar:
        st.title("⚙️ Configurações")
        
        # Toggle para tema claro/escuro
        tema_noite = st.toggle("🌙 Modo Escuro", value=tema_noite)
        st.session_state['tema_noite'] = tema_noite
        
        st.markdown("---")
        
        # Filtros
        st.subheader("📅 Filtros de Data")
        data_inicio = st.date_input("Data Inicial")
        data_fim = st.date_input("Data Final")
        
        st.markdown("---")
        
        # Meta de gastos
        st.subheader("🎯 Meta de Gastos")
        meta_gasto = st.number_input("Meta mensal (R$)", min_value=0.0, step=100.0)

    # Aplicar tema
    aplicar_tema_completo(tema_noite)

    # Carregar e filtrar dados
    df = carregar_dados()
    
    if not df.empty:
        # Filtrar dados por data
        if data_inicio and data_fim:
            df_filtrado = df[
                (df['data_emissao'].dt.date >= data_inicio) &
                (df['data_emissao'].dt.date <= data_fim)
            ].copy()  # Criar uma cópia para evitar SettingWithCopyWarning
        else:
            df_filtrado = df.copy()

        # Debug: Mostrar informações sobre os dados
        st.sidebar.markdown("---")
        st.sidebar.subheader("📊 Informações dos Dados")
        st.sidebar.write(f"Total de registros: {len(df_filtrado)}")
        
        # Safely handle date display with NaT check
        min_date = df_filtrado['data_emissao'].min()
        max_date = df_filtrado['data_emissao'].max()
        
        if pd.isna(min_date) or pd.isna(max_date):
            st.sidebar.write("Período: Dados não disponíveis")
        else:
            st.sidebar.write(f"Período: {min_date.strftime('%d/%m/%Y')} até {max_date.strftime('%d/%m/%Y')}")

        # Cabeçalho principal
        st.title("📊 Dashboard de Gastos")
        
        # Métricas principais em colunas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            gasto_total, media_gastos = calcular_indicadores(df_filtrado)
            st.metric("💰 Gasto Total", f"R$ {gasto_total:,.2f}")
        
        with col2:
            st.metric("📈 Média de Gastos", f"R$ {media_gastos:,.2f}")
        
        with col3:
            ultima_compra = calcular_ultima_compra(df_filtrado)
            if ultima_compra:
                st.metric("🗓️ Última Compra", ultima_compra.strftime("%d/%m/%Y"))
        
        with col4:
            total_compras = calcular_total_compras(df_filtrado)
            st.metric("🛍️ Total de Compras", total_compras)

        st.markdown("---")

        # Gráficos em duas colunas
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            st.subheader("📈 Gastos por Mês")
            graficos_interativos(df_filtrado)
        
        with col_graf2:
            st.subheader("🏪 Top Estabelecimentos")
            if not df_filtrado.empty:
                razoes_sociais = razao_social_com_mais_compras(df_filtrado)
                if not razoes_sociais.empty:
                    fig_razoes = px.bar(
                        razoes_sociais.head(5),
                        x='razao_social',
                        y='valor_total',
                        title="Estabelecimentos mais Frequentes",
                        template="plotly_dark" if tema_noite else "plotly_white"
                    )
                    fig_razoes.update_layout(
                        height=400,
                        margin=dict(l=20, r=20, t=40, b=20),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        xaxis_title="Estabelecimento",
                        yaxis_title="Valor Total (R$)"
                    )
                    fig_razoes.update_yaxes(
                        tickprefix="R$ ",
                        tickformat=",.2f"
                    )
                    st.plotly_chart(fig_razoes, use_container_width=True)
                else:
                    st.info("Não há dados suficientes para gerar o gráfico de estabelecimentos.")

        # Alertas e sugestões
        st.markdown("---")
        
        # Seção de alertas
        st.subheader("⚠️ Alertas de Gastos")
        exibir_alerta_meta(gasto_total, meta_gasto)
        
        st.markdown("---")
        
        # Seção de sugestões de economia
        st.subheader("💡 Oportunidades de Economia")
        exibir_sugestoes(df_filtrado)

    else:
        st.error("Não foram encontrados dados para exibir.")

# Função para gerar gráficos interativos
def graficos_interativos(df_filtrado):
    try:
        # Calcular gastos mensais
        df_mensal = calcular_gastos_mensais(df_filtrado)
        
        if not df_mensal.empty:
            # Configuração do tema
            tema = "plotly_dark" if st.session_state.get('tema_noite', False) else "plotly_white"
            
            # Gráfico de linha mensal
            fig_linha = px.line(
                df_mensal,
                x='data_emissao',
                y='valor_total',
                title='Gastos Mensais',
                template=tema,
                markers=True
            )
            
            # Personalizar layout
            fig_linha.update_layout(
                height=400,
                margin=dict(l=20, r=20, t=40, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis_title="Data",
                yaxis_title="Valor (R$)",
                showlegend=False,
                hovermode='x unified'
            )
            
            fig_linha.update_xaxes(
                tickformat="%b/%Y",
                tickangle=45,
                gridcolor='rgba(128,128,128,0.2)',
                showgrid=True
            )
            
            fig_linha.update_yaxes(
                tickprefix="R$ ",
                tickformat=",.2f",
                gridcolor='rgba(128,128,128,0.2)',
                showgrid=True
            )
            
            fig_linha.update_traces(
                hovertemplate="Data: %{x|%b/%Y}<br>Valor: R$ %{y:.2f}<extra></extra>"
            )
            
            # Exibir gráfico
            st.plotly_chart(fig_linha, use_container_width=True)
        else:
            st.warning("Não há dados suficientes para gerar os gráficos.")
            
    except Exception as e:
        st.error(f"Erro ao gerar gráficos: {str(e)}")

# Chamar a função para exibir o dashboard
if __name__ == "__main__":
    exibir_dashboard()
