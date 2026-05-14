
import pandas as pd
from itertools import permutations
from pathlib import Path

BASE_DIR = Path(__file__).parent

PARES_CSV = BASE_DIR / "pares_doador_receptor.csv"
MATCHES_CSV = BASE_DIR / "matches_cruzados.csv"

SAIDA_CICLOS_2 = BASE_DIR / "ciclos_2_pares.csv"
SAIDA_CICLOS_3 = BASE_DIR / "ciclos_3_pares.csv"
SAIDA_RESUMO = BASE_DIR / "resumo_matching.txt"


def carregar_dados():
    pares = pd.read_csv(PARES_CSV)
    matches = pd.read_csv(MATCHES_CSV)
    viaveis = matches[matches["match_viavel"] == 1].copy()
    return pares, viaveis


def criar_mapa_arestas(matches_viaveis):
    """
    Cria um dicionário:
    (par_origem, par_destino) -> score_predito_sucesso
    """
    arestas = {}

    for _, row in matches_viaveis.iterrows():
        origem = row["doador_origem_par_id"]
        destino = row["receptor_destino_par_id"]
        score = float(row["score_predito_sucesso"])

        arestas[(origem, destino)] = score

    return arestas


def encontrar_ciclos_2(pares_ids, arestas):
    ciclos = []

    for a, b in permutations(pares_ids, 2):
        if (a, b) in arestas and (b, a) in arestas:
            ciclo_ordenado = tuple(sorted([a, b]))

            score_total = arestas[(a, b)] + arestas[(b, a)]
            score_medio = score_total / 2

            ciclos.append({
                "par_1": ciclo_ordenado[0],
                "par_2": ciclo_ordenado[1],
                "score_total": round(score_total, 3),
                "score_medio": round(score_medio, 3),
                "tipo_ciclo": "2_pares"
            })

    df = pd.DataFrame(ciclos).drop_duplicates(subset=["par_1", "par_2"])
    return df.sort_values(by="score_total", ascending=False)


def encontrar_ciclos_3(pares_ids, arestas):
    ciclos = []
    visitados = set()

    for a, b, c in permutations(pares_ids, 3):
        if (a, b) in arestas and (b, c) in arestas and (c, a) in arestas:
            chave_canonica = tuple(sorted([a, b, c]))

            if chave_canonica in visitados:
                continue

            visitados.add(chave_canonica)

            score_total = arestas[(a, b)] + arestas[(b, c)] + arestas[(c, a)]
            score_medio = score_total / 3

            ciclos.append({
                "par_1": a,
                "par_2": b,
                "par_3": c,
                "fluxo": f"{a} → {b} → {c} → {a}",
                "score_total": round(score_total, 3),
                "score_medio": round(score_medio, 3),
                "tipo_ciclo": "3_pares"
            })

    df = pd.DataFrame(ciclos)
    return df.sort_values(by="score_total", ascending=False)


def selecionar_ciclos_sem_sobreposicao(df_ciclos, colunas_pares, limite=10):
    """
    Seleciona os melhores ciclos sem repetir pares.
    Isso evita que o mesmo par seja usado em duas cadeias diferentes.
    """
    selecionados = []
    pares_usados = set()

    for _, row in df_ciclos.iterrows():
        pares_do_ciclo = {row[col] for col in colunas_pares if pd.notna(row[col])}

        if pares_do_ciclo.isdisjoint(pares_usados):
            selecionados.append(row)
            pares_usados.update(pares_do_ciclo)

        if len(selecionados) >= limite:
            break

    return pd.DataFrame(selecionados)


def main():
    pares, matches_viaveis = carregar_dados()
    pares_ids = pares["par_id"].tolist()
    arestas = criar_mapa_arestas(matches_viaveis)

    ciclos_2 = encontrar_ciclos_2(pares_ids, arestas)
    ciclos_3 = encontrar_ciclos_3(pares_ids, arestas)

    melhores_2 = selecionar_ciclos_sem_sobreposicao(
        ciclos_2,
        ["par_1", "par_2"],
        limite=20
    )

    melhores_3 = selecionar_ciclos_sem_sobreposicao(
        ciclos_3,
        ["par_1", "par_2", "par_3"],
        limite=20
    )

    ciclos_2.to_csv(SAIDA_CICLOS_2, index=False, encoding="utf-8-sig")
    ciclos_3.to_csv(SAIDA_CICLOS_3, index=False, encoding="utf-8-sig")

    resumo = []
    resumo.append("MOTOR DE MATCHING - DOAÇÃO CRUZADA INTERVIVOS")
    resumo.append("=" * 55)
    resumo.append(f"Total de pares avaliados: {len(pares)}")
    resumo.append(f"Matches cruzados viáveis: {len(matches_viaveis)}")
    resumo.append(f"Ciclos de 2 pares encontrados: {len(ciclos_2)}")
    resumo.append(f"Ciclos de 3 pares encontrados: {len(ciclos_3)}")
    resumo.append("")
    resumo.append("TOP 10 ciclos de 2 pares:")
    resumo.append(str(ciclos_2.head(10).to_string(index=False)))
    resumo.append("")
    resumo.append("TOP 10 ciclos de 3 pares:")
    resumo.append(str(ciclos_3.head(10).to_string(index=False)))
    resumo.append("")
    resumo.append("Melhores ciclos de 2 pares sem sobreposição:")
    resumo.append(str(melhores_2.head(10).to_string(index=False)))
    resumo.append("")
    resumo.append("Melhores ciclos de 3 pares sem sobreposição:")
    resumo.append(str(melhores_3.head(10).to_string(index=False)))

    SAIDA_RESUMO.write_text("\n".join(resumo), encoding="utf-8")

    print("\n".join(resumo))


if __name__ == "__main__":
    main()
