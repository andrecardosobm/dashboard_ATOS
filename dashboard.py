import streamlit as st 
import pandas as pd
import plotly.express as px
from PIL import Image
import calendar
from sqlalchemy import create_engine

st.set_page_config(layout="wide")
st.title("📊 Dashboard de Vendas por Filial")

# Logo no topo da sidebar
logo = Image.open("images.jpg")
st.sidebar.image(logo, use_container_width=True)

# Função para carregar dados
@st.cache_data
def carregar_dados():
    try:
        # String de conexão com NeonDB
        conn_str = "postgresql+psycopg2://neondb_owner:npg_fW2ezy5qgZLl@ep-fragrant-dawn-a58fnaua-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"
        
        engine = create_engine(conn_str)
        df = pd.read_sql("SELECT * FROM nome_da_tabela", engine)
        return df
    except Exception as e:
        st.error(f"Erro ao conectar no banco de dados: {e}")
        return pd.DataFrame()

# Carregando dados
df = carregar_dados()
if df.empty:
    st.stop()

# Pré-processamento
df.rename(columns={"nmFilial": "FILIAL", "vlVenda": "VLVENDA", "dtVenda": "DTVENDA", "nrCNPJ": "CNPJ"}, inplace=True)
df["DTVENDA"] = pd.to_datetime(df["DTVENDA"])
df["ANO"] = df["DTVENDA"].dt.year
df["MES"] = df["DTVENDA"].dt.month

# Sidebar – filtros
filiais = sorted(df["FILIAL"].unique())
filial = st.sidebar.selectbox("🏬 Selecione a filial", filiais)

meses_disponiveis = df[(df["FILIAL"] == filial) & (df["ANO"] == 2025)]["MES"].unique()
mes_ult = st.sidebar.selectbox("🗓️ Selecione o mês de referência (2025)", sorted(meses_disponiveis))
nome_mes = calendar.month_name[mes_ult]

# Dados filtrados
cnpj = df[df["FILIAL"] == filial]["CNPJ"].iloc[0]
data_inicio_mes = pd.Timestamp(f"2025-{mes_ult:02d}-01")
data_fim_mes = df[(df["CNPJ"] == cnpj) & (df["ANO"] == 2025) & (df["MES"] == mes_ult)]["DTVENDA"].max()

df_2024 = df[(df["CNPJ"] == cnpj) & (df["ANO"] == 2024) & (df["MES"] == mes_ult)]
df_2025 = df[(df["CNPJ"] == cnpj) & (df["ANO"] == 2025) & (df["MES"] == mes_ult)]

vendas_2024 = df_2024["VLVENDA"].sum()
vendas_2025 = df_2025["VLVENDA"].sum()
meta_2025 = vendas_2024 * 1.05

acum_2024 = vendas_2024
df_acum_2025 = df[(df["CNPJ"] == cnpj) & (df["DTVENDA"] >= data_inicio_mes) & (df["DTVENDA"] <= data_fim_mes)]
acum_2025 = df_acum_2025[df_acum_2025["ANO"] == 2025]["VLVENDA"].sum()
acum_meta = acum_2024 * 1.05

# Previsão
vendas_periodo = df_2025[(df_2025["DTVENDA"] >= data_inicio_mes) & (df_2025["DTVENDA"] <= data_fim_mes)]
dias_com_venda = vendas_periodo["DTVENDA"].dt.day.nunique()
media_diaria = vendas_periodo["VLVENDA"].sum() / dias_com_venda if dias_com_venda else 0
previsao = media_diaria * 30

# Crescimento
cresc_2025 = ((vendas_2025 / vendas_2024) - 1) * 100 if vendas_2024 else 0
cresc_meta = ((vendas_2025 / acum_meta) - 1) * 100 if acum_meta else 0

# Layout
st.subheader(f"📅 Mês de Referência: {nome_mes} / 2025")
tab1, tab2, tab3 = st.tabs(["📈 Vendas vs Meta", "📊 Acumulados", "📉 Crescimento"])

with tab1:
    st.metric("Vendas 2024", f"R$ {vendas_2024:,.2f}")
    st.metric("Meta 2025", f"R$ {meta_2025:,.2f}")
    st.metric("Vendas 2025", f"R$ {vendas_2025:,.2f}")
    fig1 = px.bar(pd.DataFrame({
        "Indicador": ["Vendas 2024", "Meta 2025", "Vendas 2025"],
        "Valor": [vendas_2024, meta_2025, vendas_2025]
    }), x="Indicador", y="Valor", color="Indicador", text_auto=True, title="Vendas x Meta x Realizado")
    st.plotly_chart(fig1, use_container_width=True)

with tab2:
    st.metric("Previsão 2025", f"R$ {previsao:,.2f}")
    st.metric("Acumulado Vendas 2024", f"R$ {acum_2024:,.2f}")
    st.metric("Acumulado Meta", f"R$ {acum_meta:,.2f}")
    st.metric("Acumulado Vendas 2025", f"R$ {acum_2025:,.2f}")
    df_acum = pd.DataFrame({
        "Indicador": ["Previsão 2025", "Acum. 2024", "Acum. Meta", "Acum. 2025"],
        "Valor": [previsao, acum_2024, acum_meta, acum_2025]
    })
    fig2 = px.bar(df_acum, x="Indicador", y="Valor", color="Indicador", text_auto=True,
                  color_discrete_sequence=["#8dd3c7", "#1f78b4", "#fb8072", "#e31a1c"],
                  title="Acumulados do Mês")
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    st.metric("Crescimento 2025", f"{cresc_2025:.2f}%")
    st.metric("Crescimento sobre Meta", f"{cresc_meta:.2f}%")

    df_2025_cres = pd.DataFrame({
        "Etapa": ["Início", "Atual"],
        "Crescimento": [0, cresc_2025]
    })
    fig_2025 = px.line(df_2025_cres, x="Etapa", y="Crescimento", markers=True,
                       title="Crescimento de Vendas em 2025",
                       color_discrete_sequence=["#1f77b4"])
    st.plotly_chart(fig_2025, use_container_width=True)

    df_meta_cres = pd.DataFrame({
        "Etapa": ["Início", "Atual"],
        "Crescimento": [0, cresc_meta]
    })
    fig_meta = px.line(df_meta_cres, x="Etapa", y="Crescimento", markers=True,
                       title="Crescimento sobre a Meta",
                       color_discrete_sequence=["#ff7f0e"])
    st.plotly_chart(fig_meta, use_container_width=True)

    if mes_ult > 1:
        mes_anterior = mes_ult - 1
        vendas_2024_ant = df[(df["CNPJ"] == cnpj) & (df["ANO"] == 2024) & (df["MES"] == mes_anterior)]["VLVENDA"].sum()
        vendas_2025_ant = df[(df["CNPJ"] == cnpj) & (df["ANO"] == 2025) & (df["MES"] == mes_anterior)]["VLVENDA"].sum()
        meta_ant = vendas_2024_ant * 1.05
        acum_meta_ant = meta_ant
        cresc_meta_ant = ((vendas_2025_ant / acum_meta_ant) - 1) * 100 if acum_meta_ant else 0
        variacao_cresc_meta = cresc_meta - cresc_meta_ant

        st.metric(
            label=f"Variação de Crescimento sobre Meta vs {calendar.month_name[mes_anterior]}",
            value=f"{variacao_cresc_meta:+.2f}%",
            delta=f"{variacao_cresc_meta:+.2f}%"
        )

        df_comp = pd.DataFrame({
            "Mês": [calendar.month_name[mes_anterior], calendar.month_name[mes_ult]],
            "Crescimento sobre Meta": [cresc_meta_ant, cresc_meta]
        })

        fig_comp = px.line(df_comp, x="Mês", y="Crescimento sobre Meta", markers=True,
                           title="Comparativo de Crescimento sobre Meta: Mês Atual vs Mês Anterior",
                           color_discrete_sequence=["#4daf4a"])
        st.plotly_chart(fig_comp, use_container_width=True)
    else:
        st.info("Não há mês anterior disponível para comparação.")
