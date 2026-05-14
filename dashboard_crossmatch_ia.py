
import pandas as pd
import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).parent

PARES_CSV = BASE_DIR / "pares_doador_receptor.csv"
MATCHES_IA_CSV = BASE_DIR / "matches_com_ia.csv"
CICLOS_2_CSV = BASE_DIR / "ciclos_2_pares.csv"
CICLOS_3_CSV = BASE_DIR / "ciclos_3_pares.csv"
RELATORIO_IA = BASE_DIR / "relatorio_modelo_ia.txt"


st.set_page_config(
    page_title="CrossMatch IA - Doação Cruzada Inteligente",
    page_icon="🧬",
    layout="wide"
)


@st.cache_data
def carregar_dados():
    pares = pd.read_csv(PARES_CSV)
    matches_ia = pd.read_csv(MATCHES_IA_CSV)
    ciclos_2 = pd.read_csv(CICLOS_2_CSV)
    ciclos_3 = pd.read_csv(CICLOS_3_CSV)

    if RELATORIO_IA.exists():
        relatorio = RELATORIO_IA.read_text(encoding="utf-8")
    else:
        relatorio = "Relatório de IA não encontrado."

    return pares, matches_ia, ciclos_2, ciclos_3, relatorio


def card_metricas(pares, matches_ia, ciclos_2, ciclos_3):
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Pares cadastrados", len(pares))

    with col2:
        st.metric("Pares aptos", int(pares["apto_para_doacao_cruzada"].sum()))

    with col3:
        st.metric("Matches viáveis", int(matches_ia["match_viavel"].sum()))

    with col4:
        media_ia = matches_ia["ia_probabilidade_match_viavel"].mean()
        st.metric("Prob. média IA", f"{media_ia:.2%}")

    with col5:
        st.metric("Ciclos detectados", len(ciclos_2) + len(ciclos_3))


def pagina_visao_geral(pares, matches_ia):
    st.header("📊 Visão geral inteligente")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Distribuição ABO dos receptores")
        st.bar_chart(pares["abo_receptor"].value_counts())

    with col2:
        st.subheader("Distribuição de confiança da IA")
        st.bar_chart(matches_ia["ia_faixa_confianca"].value_counts())

    st.subheader("Top 25 matches sugeridos pela IA")
    top = matches_ia.sort_values(
        "ia_probabilidade_match_viavel",
        ascending=False
    ).head(25)

    st.dataframe(top, use_container_width=True)

    st.info(
        "A IA não substitui a equipe médica. Ela atua como camada de apoio para triagem, "
        "priorização e simulação de combinações em doação cruzada intervivos."
    )


def pagina_ranking_ia(matches_ia):
    st.header("🤖 Ranking inteligente de matches")

    min_prob = st.slider(
        "Probabilidade mínima segundo a IA",
        0.0,
        1.0,
        0.75,
        0.01
    )

    faixa = st.multiselect(
        "Faixa de confiança",
        sorted(matches_ia["ia_faixa_confianca"].dropna().unique()),
        default=list(sorted(matches_ia["ia_faixa_confianca"].dropna().unique()))
    )

    somente_viaveis = st.checkbox("Mostrar apenas matches viáveis originais", value=True)

    filtrado = matches_ia[
        matches_ia["ia_probabilidade_match_viavel"] >= min_prob
    ].copy()

    if faixa:
        filtrado = filtrado[filtrado["ia_faixa_confianca"].isin(faixa)]

    if somente_viaveis:
        filtrado = filtrado[filtrado["match_viavel"] == 1]

    st.metric("Matches após filtro", len(filtrado))

    st.dataframe(
        filtrado.sort_values("ia_probabilidade_match_viavel", ascending=False),
        use_container_width=True
    )


def pagina_analise_par(pares, matches_ia):
    st.header("🔎 Análise individual por par")

    par_id = st.selectbox("Selecione um par", pares["par_id"].tolist())
    par = pares[pares["par_id"] == par_id].iloc[0]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### Receptor")
        st.write(f"**ID:** {par['receptor_id']}")
        st.write(f"**ABO:** {par['abo_receptor']}")
        st.write(f"**Idade:** {par['idade_receptor']}")
        st.write(f"**PRA:** {par['pra_receptor_pct']}%")
        st.write(f"**Tempo de diálise:** {par['tempo_dialise_meses']} meses")
        st.write(f"**Prioridade:** {par['prioridade_clinica']}")

    with col2:
        st.markdown("### Doador")
        st.write(f"**ID:** {par['doador_id']}")
        st.write(f"**ABO:** {par['abo_doador']}")
        st.write(f"**Idade:** {par['idade_doador']}")
        st.write(f"**Parentesco:** {par['parentesco']}")

    with col3:
        st.markdown("### Situação original")
        st.write(f"**Compatibilidade ABO:** {bool(par['compatibilidade_abo_original'])}")
        st.write(f"**Crossmatch positivo:** {bool(par['crossmatch_original_positivo'])}")
        st.write(f"**Incompatível:** {bool(par['par_original_incompativel'])}")
        st.write(f"**Apto para cruzada:** {bool(par['apto_para_doacao_cruzada'])}")

    st.subheader("Melhores receptores para o doador deste par")
    candidatos = matches_ia[
        matches_ia["doador_origem_par_id"] == par_id
    ].sort_values("ia_probabilidade_match_viavel", ascending=False)

    st.dataframe(candidatos.head(30), use_container_width=True)

    st.subheader("Melhores doadores para o receptor deste par")
    doadores = matches_ia[
        matches_ia["receptor_destino_par_id"] == par_id
    ].sort_values("ia_probabilidade_match_viavel", ascending=False)

    st.dataframe(doadores.head(30), use_container_width=True)


def calcular_score_ia_ciclo(ciclo, matches_ia):
    pares = []

    if "par_3" in ciclo and pd.notna(ciclo["par_3"]):
        sequencia = [ciclo["par_1"], ciclo["par_2"], ciclo["par_3"], ciclo["par_1"]]
    else:
        sequencia = [ciclo["par_1"], ciclo["par_2"], ciclo["par_1"]]

    probs = []

    for i in range(len(sequencia) - 1):
        origem = sequencia[i]
        destino = sequencia[i + 1]

        linha = matches_ia[
            (matches_ia["doador_origem_par_id"] == origem)
            & (matches_ia["receptor_destino_par_id"] == destino)
        ]

        if len(linha) > 0:
            probs.append(float(linha.iloc[0]["ia_probabilidade_match_viavel"]))

    if not probs:
        return 0

    return sum(probs) / len(probs)


def pagina_ciclos_ia(ciclos_2, ciclos_3, matches_ia):
    st.header("🔗 Ciclos priorizados pela IA")

    tipo = st.radio("Tipo de ciclo", ["2 pares", "3 pares"], horizontal=True)

    if tipo == "2 pares":
        df = ciclos_2.copy()
    else:
        df = ciclos_3.copy()

    df["score_medio_ia"] = df.apply(
        lambda row: calcular_score_ia_ciclo(row, matches_ia),
        axis=1
    )

    min_score = st.slider("Score médio mínimo da IA no ciclo", 0.0, 1.0, 0.75, 0.01)

    df = df[df["score_medio_ia"] >= min_score]
    df = df.sort_values("score_medio_ia", ascending=False)

    st.metric("Ciclos após filtro", len(df))
    st.dataframe(df.head(100), use_container_width=True)


def pagina_relatorio_ia(relatorio):
    st.header("📄 Relatório do modelo de IA")
    st.text(relatorio)


def pagina_governanca():
    st.header("⚖️ Governança, ética e segurança")

    st.markdown(
        """
        Este MVP deve ser entendido como **sistema de apoio à decisão**, nunca como decisão automática.

        Pontos essenciais para uma versão real:

        1. **LGPD e dados sensíveis de saúde**  
           Dados clínicos e genéticos exigem segurança, consentimento, finalidade clara e auditoria.

        2. **Comitê clínico e bioético**  
           Nenhum match deve ser efetivado sem validação médica, imunológica, jurídica e ética.

        3. **Explicabilidade**  
           O sistema deve explicar por que um match foi sugerido.

        4. **Não comercialização**  
           A doação deve permanecer voluntária, gratuita e juridicamente protegida.

        5. **Auditoria pública**  
           Toda sugestão de match precisa deixar rastros de decisão, critérios usados e responsáveis pela validação.
        """
    )


def main():
    pares, matches_ia, ciclos_2, ciclos_3, relatorio = carregar_dados()

    st.title("🧬 CrossMatch IA")
    st.caption("Sistema inteligente de apoio à doação renal intervivos cruzada")

    card_metricas(pares, matches_ia, ciclos_2, ciclos_3)

    st.sidebar.title("Navegação")
    pagina = st.sidebar.radio(
        "Escolha uma seção",
        [
            "Visão geral IA",
            "Ranking inteligente",
            "Análise por par",
            "Ciclos com IA",
            "Relatório do modelo",
            "Governança"
        ]
    )

    if pagina == "Visão geral IA":
        pagina_visao_geral(pares, matches_ia)

    elif pagina == "Ranking inteligente":
        pagina_ranking_ia(matches_ia)

    elif pagina == "Análise por par":
        pagina_analise_par(pares, matches_ia)

    elif pagina == "Ciclos com IA":
        pagina_ciclos_ia(ciclos_2, ciclos_3, matches_ia)

    elif pagina == "Relatório do modelo":
        pagina_relatorio_ia(relatorio)

    elif pagina == "Governança":
        pagina_governanca()


if __name__ == "__main__":
    main()
