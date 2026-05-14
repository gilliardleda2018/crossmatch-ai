
import pandas as pd
import streamlit as st
from pathlib import Path
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components

BASE_DIR = Path(__file__).parent

PARES_CSV = BASE_DIR / "pares_doador_receptor_v2.csv"
MATCHES_CSV = BASE_DIR / "matches_cruzados_v2.csv"
CICLOS_2_CSV = BASE_DIR / "ciclos_2_pares_v2.csv"
CICLOS_3_CSV = BASE_DIR / "ciclos_3_pares_v2.csv"

st.set_page_config(
    page_title="CrossMatch IA V2",
    page_icon="🧬",
    layout="wide"
)

@st.cache_data
def carregar_dados():
    arquivos = [PARES_CSV, MATCHES_CSV, CICLOS_2_CSV, CICLOS_3_CSV]
    faltando = [str(a.name) for a in arquivos if not a.exists()]

    if faltando:
        st.error("Arquivos não encontrados na pasta do dashboard:")
        st.write(faltando)
        st.info("Coloque todos os arquivos CSV V2 na mesma pasta do dashboard.")
        st.stop()

    pares = pd.read_csv(PARES_CSV)
    matches = pd.read_csv(MATCHES_CSV)
    ciclos2 = pd.read_csv(CICLOS_2_CSV)
    ciclos3 = pd.read_csv(CICLOS_3_CSV)
    return pares, matches, ciclos2, ciclos3

def cards_metricas(pares, matches, ciclos2, ciclos3):
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Pares", len(pares))
    col2.metric("Pares aptos", int(pares["apto_para_doacao_cruzada"].sum()))
    col3.metric("Matches viáveis", int(matches["match_viavel"].sum()))
    col4.metric("Ciclos", len(ciclos2) + len(ciclos3))
    col5.metric("Distância média", f"{matches['distancia_km'].mean():.0f} km")

def pagina_visao_geral(pares, matches):
    st.header("📊 Visão geral V2")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Distribuição ABO dos receptores")
        st.bar_chart(pares["abo_receptor"].value_counts())

    with col2:
        st.subheader("Distribuição ABO dos doadores")
        st.bar_chart(pares["abo_doador"].value_counts())

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Faixa PRA dos receptores")
        st.bar_chart(pares["faixa_pra"].value_counts())

    with col4:
        st.subheader("Risco cirúrgico")
        st.bar_chart(pares["risco_cirurgico"].value_counts())

    st.subheader("Top 30 matches por score clínico-logístico")
    st.dataframe(
        matches.sort_values("score_clinico_logistico", ascending=False).head(30),
        use_container_width=True
    )

def pagina_grafo(matches):
    st.header("🕸️ Grafo interativo de doação cruzada")

    min_score = st.slider("Score clínico-logístico mínimo", 0.0, 1.0, 0.70, 0.01)
    max_edges = st.slider("Número máximo de conexões", 20, 300, 120, 10)

    df = matches[
        (matches["match_viavel"] == 1)
        & (matches["score_clinico_logistico"] >= min_score)
    ].sort_values("score_clinico_logistico", ascending=False).head(max_edges)

    if df.empty:
        st.warning("Nenhuma conexão encontrada com esse filtro.")
        return

    G = nx.DiGraph()

    for _, row in df.iterrows():
        origem = row["doador_origem_par_id"]
        destino = row["receptor_destino_par_id"]
        score = float(row["score_clinico_logistico"])

        G.add_node(origem, label=origem, title=f"Par: {origem}")
        G.add_node(destino, label=destino, title=f"Par: {destino}")

        G.add_edge(
            origem,
            destino,
            value=score,
            label=f"{score:.2f}",
            title=(
                f"{origem} → {destino}<br>"
                f"Score: {score:.2f}<br>"
                f"Distância: {row['distancia_km']} km"
            )
        )

    net = Network(
        height="650px",
        width="100%",
        directed=True,
        bgcolor="#ffffff",
        font_color="#222222"
    )

    net.from_nx(G)
    net.repulsion(node_distance=180, spring_length=160)

    html_path = BASE_DIR / "grafo_crossmatch_v2.html"
    net.save_graph(str(html_path))
    components.html(html_path.read_text(encoding="utf-8"), height=680)

    st.dataframe(df, use_container_width=True)

def pagina_simulador(pares, matches, ciclos2, ciclos3):
    st.header("🔁 Simulador de cadeia por par")

    par = st.selectbox("Escolha um par", pares["par_id"].tolist())

    st.subheader("Resumo do par")
    st.dataframe(pares[pares["par_id"] == par], use_container_width=True)

    st.subheader("Para quem o doador deste par pode doar")
    saida = matches[
        (matches["doador_origem_par_id"] == par)
        & (matches["match_viavel"] == 1)
    ].sort_values("score_clinico_logistico", ascending=False)
    st.dataframe(saida.head(30), use_container_width=True)

    st.subheader("Quem pode doar para o receptor deste par")
    entrada = matches[
        (matches["receptor_destino_par_id"] == par)
        & (matches["match_viavel"] == 1)
    ].sort_values("score_clinico_logistico", ascending=False)
    st.dataframe(entrada.head(30), use_container_width=True)

    st.subheader("Ciclos de 2 pares envolvendo este par")
    c2 = ciclos2[(ciclos2["par_1"] == par) | (ciclos2["par_2"] == par)]
    st.dataframe(c2.head(30), use_container_width=True)

    st.subheader("Ciclos de 3 pares envolvendo este par")
    c3 = ciclos3[
        (ciclos3["par_1"] == par)
        | (ciclos3["par_2"] == par)
        | (ciclos3["par_3"] == par)
    ]
    st.dataframe(c3.head(30), use_container_width=True)

def pagina_ranking(matches):
    st.header("🤖 Ranking dos melhores matches V2")

    min_score = st.slider("Score mínimo", 0.0, 1.0, 0.60, 0.01)
    max_dist = st.slider("Distância máxima em km", 0, 3000, 2500, 100)

    df = matches[
        (matches["match_viavel"] == 1)
        & (matches["score_clinico_logistico"] >= min_score)
        & (matches["distancia_km"] <= max_dist)
    ].sort_values("score_clinico_logistico", ascending=False)

    st.metric("Matches após filtro", len(df))
    st.dataframe(df.head(200), use_container_width=True)

def pagina_insights(pares, matches):
    st.header("🧠 Insights clínicos e logísticos")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Distribuição de distância logística")
        st.bar_chart(matches["distancia_km"].round(-2).value_counts().sort_index())

    with col2:
        st.subheader("Probabilidade de desistência do doador")
        st.bar_chart(pares["prob_desistencia_doador"].round(1).value_counts().sort_index())

    st.subheader("Score clínico-logístico x distância")
    st.scatter_chart(matches[["distancia_km", "score_clinico_logistico"]])

    st.subheader("PRA dos receptores")
    st.bar_chart(pares["faixa_pra"].value_counts())

def pagina_como_interpretar():
    st.header("📘 Como interpretar")

    st.markdown("""
    Este dashboard usa dados sintéticos calibrados para simular doação renal intervivos cruzada.

    ### 👨‍👩‍👧 Par
    Um par é formado por:
    - receptor: pessoa que precisa do rim;
    - doador: pessoa que deseja doar.

    ### 🔗 Match
    É quando o doador de um par pode doar para o receptor de outro par.

    ### 🧬 PRA
    Mede o grau de sensibilização imunológica do receptor.
    - baixo: menor dificuldade de compatibilidade;
    - intermediário: exige mais cuidado;
    - alto: tende a ser mais difícil encontrar doador compatível.

    ### 🩸 ABO
    Compatibilidade do tipo sanguíneo.

    ### 🧪 Crossmatch
    Teste que indica se há reação imunológica contra o doador.
    Crossmatch positivo geralmente inviabiliza o transplante direto.

    ### 📍 Distância logística
    Ajuda a estimar a dificuldade operacional entre centros/cidades.

    ### 🤝 Probabilidade de desistência
    Simula o risco humano de o doador desistir durante o processo.

    ### 📊 Score clínico-logístico
    Indicador sintético que combina compatibilidade, risco, distância e fatores clínicos.

    ### 🔁 Ciclos
    São cadeias de troca:
    - A doa para B;
    - B doa para A.

    Ou em ciclos maiores:
    - A → B → C → A.
    """)

    st.success("Em resumo: o sistema procura caminhos de compatibilidade onde a doação direta não seria possível.")

def pagina_governanca():
    st.header("⚖️ Governança")

    st.markdown("""
    Este MVP é apenas um sistema de apoio à decisão.

    Em uso real, seriam obrigatórios:
    - dados anonimizados;
    - consentimento informado;
    - validação médica;
    - avaliação imunológica;
    - aprovação ética;
    - conformidade com a LGPD;
    - decisão final humana.
    """)

def main():
    pares, matches, ciclos2, ciclos3 = carregar_dados()

    st.title("🧬 CrossMatch IA V2")
    st.caption("Dashboard com dataset sintético calibrado e variáveis clínicas/logísticas mais realistas")

    cards_metricas(pares, matches, ciclos2, ciclos3)

    pagina = st.sidebar.radio(
        "Navegação",
        [
            "Visão geral",
            "Grafo",
            "Simulador",
            "Ranking",
            "Insights clínicos",
            "Como interpretar",
            "Governança"
        ]
    )

    if pagina == "Visão geral":
        pagina_visao_geral(pares, matches)
    elif pagina == "Grafo":
        pagina_grafo(matches)
    elif pagina == "Simulador":
        pagina_simulador(pares, matches, ciclos2, ciclos3)
    elif pagina == "Ranking":
        pagina_ranking(matches)
    elif pagina == "Insights clínicos":
        pagina_insights(pares, matches)
    elif pagina == "Como interpretar":
        pagina_como_interpretar()
    elif pagina == "Governança":
        pagina_governanca()

if __name__ == "__main__":
    main()
