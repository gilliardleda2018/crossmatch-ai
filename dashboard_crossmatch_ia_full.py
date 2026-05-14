
import pandas as pd
import streamlit as st
from pathlib import Path
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components

BASE_DIR = Path(__file__).parent

# 🔥 NOVOS ARQUIVOS V2
PARES_CSV = BASE_DIR / "pares_doador_receptor_v2.csv"
MATCHES_CSV = BASE_DIR / "matches_cruzados_v2.csv"
CICLOS_2_CSV = BASE_DIR / "ciclos_2_pares_v2.csv"
CICLOS_3_CSV = BASE_DIR / "ciclos_3_pares_v2.csv"

st.set_page_config(page_title="CrossMatch IA V2", layout="wide")

@st.cache_data
def load():
    return (
        pd.read_csv(PARES_CSV),
        pd.read_csv(MATCHES_CSV),
        pd.read_csv(CICLOS_2_CSV),
        pd.read_csv(CICLOS_3_CSV)
    )

pares, matches, ciclos2, ciclos3 = load()

# ======================
# 📊 MÉTRICAS
# ======================
st.title("🧬 CrossMatch IA - V2 (Dados Realistas)")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Pares", len(pares))
col2.metric("Matches viáveis", int(matches["match_viavel"].sum()))
col3.metric("Distância média", f"{matches['distancia_km'].mean():.0f} km")
col4.metric("Risco médio desistência", f"{pares['prob_desistencia_doador'].mean():.2f}")

# ======================
# 📘 ABA
# ======================
menu = st.sidebar.radio("Menu", [
    "Visão geral",
    "Grafo",
    "Simulador",
    "Ranking",
    "Insights clínicos",
    "Como interpretar"
])

# ======================
# 📊 VISÃO GERAL
# ======================
if menu == "Visão geral":
    st.subheader("Distribuição ABO")
    col1, col2 = st.columns(2)

    col1.bar_chart(pares["abo_receptor"].value_counts())
    col2.bar_chart(pares["abo_doador"].value_counts())

    st.subheader("Distribuição PRA")
    st.bar_chart(pares["faixa_pra"].value_counts())

# ======================
# 🕸️ GRAFO
# ======================
elif menu == "Grafo":
    st.subheader("Rede de doação cruzada")

    df = matches[matches["match_viavel"] == 1].head(200)

    G = nx.DiGraph()

    for _, r in df.iterrows():
        G.add_edge(
            r["doador_origem_par_id"],
            r["receptor_destino_par_id"],
            weight=r["score_clinico_logistico"]
        )

    net = Network(height="600px", width="100%", directed=True)
    net.from_nx(G)

    path = BASE_DIR / "grafo.html"
    net.save_graph(str(path))

    components.html(path.read_text(), height=650)

# ======================
# 🔁 SIMULADOR
# ======================
elif menu == "Simulador":
    par = st.selectbox("Escolha um par", pares["par_id"])

    st.subheader("Para quem pode doar")
    st.dataframe(matches[matches["doador_origem_par_id"] == par].head(20))

    st.subheader("Quem pode doar para ele")
    st.dataframe(matches[matches["receptor_destino_par_id"] == par].head(20))

# ======================
# 🤖 RANKING
# ======================
elif menu == "Ranking":
    st.subheader("Melhores matches")

    df = matches.sort_values("score_clinico_logistico", ascending=False)

    st.dataframe(df.head(100))

# ======================
# 🧠 NOVA ABA (OURO)
# ======================
elif menu == "Insights clínicos":

    st.subheader("Impacto da distância")
    st.line_chart(matches["distancia_km"].sort_values())

    st.subheader("Desistência do doador")
    st.histogram = st.bar_chart(pares["prob_desistencia_doador"])

    st.subheader("Score vs distância")
    st.scatter_chart(
        matches[["distancia_km", "score_clinico_logistico"]]
    )

# ======================
# 📘 EXPLICAÇÃO
# ======================
elif menu == "Como interpretar":
    st.markdown("""
    ## 📘 Guia rápido

    **Par** → paciente + doador  
    **Match** → possibilidade de troca  
    **Score** → chance de dar certo  
    **Distância** → impacto logístico  
    **Desistência** → risco humano real  

    👉 O sistema encontra caminhos onde antes não existiam.
    """)