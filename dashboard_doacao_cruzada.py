
import pandas as pd
import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).parent

PARES_CSV = BASE_DIR / "pares_doador_receptor.csv"
MATCHES_CSV = BASE_DIR / "matches_cruzados.csv"
CICLOS_2_CSV = BASE_DIR / "ciclos_2_pares.csv"
CICLOS_3_CSV = BASE_DIR / "ciclos_3_pares.csv"


st.set_page_config(
    page_title="CrossMatch IA - Doação Cruzada",
    page_icon="🧬",
    layout="wide"
)


@st.cache_data
def carregar_dados():
    pares = pd.read_csv(PARES_CSV)
    matches = pd.read_csv(MATCHES_CSV)
    ciclos_2 = pd.read_csv(CICLOS_2_CSV)
    ciclos_3 = pd.read_csv(CICLOS_3_CSV)
    return pares, matches, ciclos_2, ciclos_3


def explicar_score():
    st.info(
        """
        O score predito de sucesso é uma métrica sintética criada para o MVP.
        Ele combina compatibilidade ABO, similaridade HLA simplificada, idade do doador,
        PRA do receptor, tempo de diálise e risco cirúrgico.

        Em um sistema real, esse score deveria ser validado por equipe médica,
        comitê de ética, legislação vigente e dados clínicos oficiais.
        """
    )


def card_metricas(pares, matches, ciclos_2, ciclos_3):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Pares cadastrados", len(pares))

    with col2:
        st.metric("Pares aptos", int(pares["apto_para_doacao_cruzada"].sum()))

    with col3:
        st.metric("Matches viáveis", int(matches["match_viavel"].sum()))

    with col4:
        st.metric("Ciclos encontrados", len(ciclos_2) + len(ciclos_3))


def mostrar_top_ciclos(ciclos_2, ciclos_3):
    st.subheader("🏆 Melhores ciclos de doação cruzada")

    tipo = st.radio(
        "Tipo de ciclo",
        ["2 pares", "3 pares"],
        horizontal=True
    )

    if tipo == "2 pares":
        df = ciclos_2.sort_values("score_total", ascending=False).copy()
        st.dataframe(
            df.head(30),
            use_container_width=True
        )
    else:
        df = ciclos_3.sort_values("score_total", ascending=False).copy()
        st.dataframe(
            df.head(30),
            use_container_width=True
        )


def analisar_par(pares, matches):
    st.subheader("🔎 Análise individual de um par")

    par_id = st.selectbox(
        "Selecione um par doador-receptor",
        pares["par_id"].tolist()
    )

    par = pares[pares["par_id"] == par_id].iloc[0]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### Receptor")
        st.write(f"**ID:** {par['receptor_id']}")
        st.write(f"**ABO:** {par['abo_receptor']}")
        st.write(f"**Idade:** {par['idade_receptor']}")
        st.write(f"**PRA:** {par['pra_receptor_pct']}%")
        st.write(f"**Tempo de diálise:** {par['tempo_dialise_meses']} meses")

    with col2:
        st.markdown("### Doador")
        st.write(f"**ID:** {par['doador_id']}")
        st.write(f"**ABO:** {par['abo_doador']}")
        st.write(f"**Idade:** {par['idade_doador']}")
        st.write(f"**Parentesco:** {par['parentesco']}")

    with col3:
        st.markdown("### Situação original")
        st.write(f"**ABO compatível:** {bool(par['compatibilidade_abo_original'])}")
        st.write(f"**Crossmatch positivo:** {bool(par['crossmatch_original_positivo'])}")
        st.write(f"**Par incompatível:** {bool(par['par_original_incompativel'])}")
        st.write(f"**Apto para doação cruzada:** {bool(par['apto_para_doacao_cruzada'])}")

    st.markdown("### Possíveis receptores para o doador deste par")
    candidatos = matches[
        (matches["doador_origem_par_id"] == par_id)
        & (matches["match_viavel"] == 1)
    ].sort_values("score_predito_sucesso", ascending=False)

    st.dataframe(candidatos.head(20), use_container_width=True)

    st.markdown("### Possíveis doadores para o receptor deste par")
    doadores = matches[
        (matches["receptor_destino_par_id"] == par_id)
        & (matches["match_viavel"] == 1)
    ].sort_values("score_predito_sucesso", ascending=False)

    st.dataframe(doadores.head(20), use_container_width=True)


def simulador_filtros(pares, matches, ciclos_2, ciclos_3):
    st.subheader("⚙️ Simulador de critérios")

    min_score = st.slider(
        "Score mínimo de sucesso",
        min_value=0.50,
        max_value=0.90,
        value=0.60,
        step=0.01
    )

    somente_baixo_moderado = st.checkbox(
        "Excluir receptores com risco cirúrgico alto",
        value=True
    )

    matches_filtrados = matches[
        (matches["match_viavel"] == 1)
        & (matches["score_predito_sucesso"] >= min_score)
    ].copy()

    if somente_baixo_moderado:
        pares_validos = pares[pares["risco_cirurgico"] != "alto"]["par_id"].tolist()
        matches_filtrados = matches_filtrados[
            matches_filtrados["receptor_destino_par_id"].isin(pares_validos)
        ]

    col1, col2, col3 = st.columns(3)
    col1.metric("Matches após filtro", len(matches_filtrados))
    col2.metric("Doadores únicos", matches_filtrados["doador_origem_par_id"].nunique())
    col3.metric("Receptores únicos", matches_filtrados["receptor_destino_par_id"].nunique())

    st.dataframe(
        matches_filtrados.sort_values("score_predito_sucesso", ascending=False).head(50),
        use_container_width=True
    )


def matriz_abo(pares):
    st.subheader("🩸 Distribuição ABO")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Receptores**")
        st.bar_chart(pares["abo_receptor"].value_counts())

    with col2:
        st.markdown("**Doadores**")
        st.bar_chart(pares["abo_doador"].value_counts())


def pagina_sobre():
    st.subheader("📌 Sobre o MVP")

    st.markdown(
        """
        Este MVP demonstra um sistema de apoio à doação intervivos cruzada.

        **Ideia central:** quando um doador manifesta desejo de doar para um familiar,
        mas há incompatibilidade, o sistema procura outros pares incompatíveis que possam
        formar uma troca cruzada.

        **O sistema simula:**
        - cadastro de pares doador-receptor;
        - incompatibilidade original;
        - avaliação de compatibilidade cruzada;
        - score predito de sucesso;
        - ciclos de 2 e 3 pares;
        - ranking das melhores combinações.

        **Importante:** os dados são sintéticos e servem apenas para prototipagem,
        pesquisa e validação conceitual.
        """
    )


def main():
    pares, matches, ciclos_2, ciclos_3 = carregar_dados()

    st.title("🧬 CrossMatch IA")
    st.caption("MVP para apoio à doação renal intervivos cruzada")

    card_metricas(pares, matches, ciclos_2, ciclos_3)

    st.sidebar.title("Navegação")
    pagina = st.sidebar.radio(
        "Escolha uma seção",
        [
            "Visão geral",
            "Ranking de ciclos",
            "Análise por par",
            "Simulador",
            "Dados brutos",
            "Sobre"
        ]
    )

    if pagina == "Visão geral":
        st.header("📊 Visão geral")
        matriz_abo(pares)
        explicar_score()

        st.subheader("Pares aptos para doação cruzada")
        st.dataframe(
            pares[pares["apto_para_doacao_cruzada"] == 1].head(50),
            use_container_width=True
        )

    elif pagina == "Ranking de ciclos":
        mostrar_top_ciclos(ciclos_2, ciclos_3)

    elif pagina == "Análise por par":
        analisar_par(pares, matches)

    elif pagina == "Simulador":
        simulador_filtros(pares, matches, ciclos_2, ciclos_3)

    elif pagina == "Dados brutos":
        st.header("📁 Dados brutos")
        aba1, aba2, aba3, aba4 = st.tabs(
            ["Pares", "Matches", "Ciclos 2 pares", "Ciclos 3 pares"]
        )

        with aba1:
            st.dataframe(pares, use_container_width=True)

        with aba2:
            st.dataframe(matches, use_container_width=True)

        with aba3:
            st.dataframe(ciclos_2, use_container_width=True)

        with aba4:
            st.dataframe(ciclos_3, use_container_width=True)

    elif pagina == "Sobre":
        pagina_sobre()


if __name__ == "__main__":
    main()
