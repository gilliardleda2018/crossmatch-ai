
import pandas as pd
import numpy as np
from pathlib import Path
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)

BASE_DIR = Path(__file__).parent

PARES_CSV = BASE_DIR / "pares_doador_receptor.csv"
MATCHES_CSV = BASE_DIR / "matches_cruzados.csv"

SAIDA_PREDICOES = BASE_DIR / "matches_com_ia.csv"
SAIDA_MODELO = BASE_DIR / "modelo_crossmatch_ia.joblib"
SAIDA_RELATORIO = BASE_DIR / "relatorio_modelo_ia.txt"


def carregar_base():
    pares = pd.read_csv(PARES_CSV)
    matches = pd.read_csv(MATCHES_CSV)

    pares_receptor = pares.add_prefix("receptor_")
    pares_doador = pares.add_prefix("doador_")

    base = matches.merge(
        pares_doador,
        left_on="doador_origem_par_id",
        right_on="doador_par_id",
        how="left"
    )

    base = base.merge(
        pares_receptor,
        left_on="receptor_destino_par_id",
        right_on="receptor_par_id",
        how="left"
    )

    return base


def preparar_features(base):
    colunas_numericas = [
        "compatibilidade_abo_cruzada",
        "hla_match_cruzado",
        "crossmatch_cruzado_positivo",
        "score_predito_sucesso",

        "doador_idade_doador",
        "receptor_idade_receptor",
        "receptor_pra_receptor_pct",
        "receptor_tempo_dialise_meses",
        "receptor_diabetes_receptor",
        "receptor_hipertensao_receptor",
        "receptor_creatinina_receptor",
    ]

    colunas_categoricas = [
        "abo_doador",
        "abo_receptor_destino",
        "receptor_prioridade_clinica",
        "receptor_risco_cirurgico",
        "doador_parentesco",
        "doador_cidade_origem",
        "receptor_cidade_origem",
    ]

    alvo = "match_viavel"

    X = base[colunas_numericas + colunas_categoricas].copy()
    y = base[alvo].astype(int)

    return X, y, colunas_numericas, colunas_categoricas


def treinar_modelo(X, y, colunas_numericas, colunas_categoricas):
    pre_processador = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), colunas_categoricas),
            ("num", "passthrough", colunas_numericas)
        ]
    )

    modelo = RandomForestClassifier(
        n_estimators=350,
        max_depth=8,
        min_samples_split=6,
        min_samples_leaf=3,
        class_weight="balanced",
        random_state=42
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessamento", pre_processador),
            ("modelo", modelo)
        ]
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y
    )

    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]

    metricas = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "f1": f1_score(y_test, y_pred),
        "roc_auc": roc_auc_score(y_test, y_prob),
        "confusion_matrix": confusion_matrix(y_test, y_pred),
        "classification_report": classification_report(y_test, y_pred)
    }

    return pipeline, metricas


def aplicar_modelo(base, X, pipeline):
    base_saida = base.copy()

    prob = pipeline.predict_proba(X)[:, 1]
    pred = pipeline.predict(X)

    base_saida["ia_probabilidade_match_viavel"] = np.round(prob, 4)
    base_saida["ia_classificacao_match"] = pred

    base_saida["ia_faixa_confianca"] = pd.cut(
        base_saida["ia_probabilidade_match_viavel"],
        bins=[0, 0.40, 0.60, 0.80, 1.00],
        labels=[
            "baixa",
            "moderada",
            "alta",
            "muito_alta"
        ],
        include_lowest=True
    )

    colunas_saida = [
        "doador_origem_par_id",
        "receptor_destino_par_id",
        "abo_doador",
        "abo_receptor_destino",
        "compatibilidade_abo_cruzada",
        "hla_match_cruzado",
        "crossmatch_cruzado_positivo",
        "score_predito_sucesso",
        "match_viavel",
        "ia_probabilidade_match_viavel",
        "ia_classificacao_match",
        "ia_faixa_confianca",

        "receptor_idade_receptor",
        "receptor_pra_receptor_pct",
        "receptor_tempo_dialise_meses",
        "receptor_prioridade_clinica",
        "receptor_risco_cirurgico",
        "receptor_diabetes_receptor",
        "receptor_hipertensao_receptor",
        "doador_idade_doador",
        "doador_parentesco",
        "doador_cidade_origem",
        "receptor_cidade_origem",
    ]

    return base_saida[colunas_saida].sort_values(
        by="ia_probabilidade_match_viavel",
        ascending=False
    )


def gerar_relatorio(metricas, base_predita):
    texto = []
    texto.append("RELATÓRIO DO MODELO DE IA - CROSSMATCH IA")
    texto.append("=" * 60)
    texto.append("")
    texto.append("Objetivo:")
    texto.append("Prever a viabilidade de um match cruzado entre doador e receptor.")
    texto.append("")
    texto.append("Métricas do modelo:")
    texto.append(f"Acurácia:  {metricas['accuracy']:.4f}")
    texto.append(f"Precisão:  {metricas['precision']:.4f}")
    texto.append(f"Recall:    {metricas['recall']:.4f}")
    texto.append(f"F1-score:  {metricas['f1']:.4f}")
    texto.append(f"ROC-AUC:   {metricas['roc_auc']:.4f}")
    texto.append("")
    texto.append("Matriz de confusão:")
    texto.append(str(metricas["confusion_matrix"]))
    texto.append("")
    texto.append("Relatório de classificação:")
    texto.append(metricas["classification_report"])
    texto.append("")
    texto.append("Top 20 matches com maior probabilidade segundo a IA:")
    texto.append(
        base_predita[
            [
                "doador_origem_par_id",
                "receptor_destino_par_id",
                "ia_probabilidade_match_viavel",
                "ia_faixa_confianca",
                "score_predito_sucesso",
                "match_viavel"
            ]
        ].head(20).to_string(index=False)
    )

    return "\n".join(texto)


def main():
    base = carregar_base()
    X, y, colunas_numericas, colunas_categoricas = preparar_features(base)

    pipeline, metricas = treinar_modelo(
        X,
        y,
        colunas_numericas,
        colunas_categoricas
    )

    base_predita = aplicar_modelo(base, X, pipeline)

    base_predita.to_csv(SAIDA_PREDICOES, index=False, encoding="utf-8-sig")
    joblib.dump(pipeline, SAIDA_MODELO)

    relatorio = gerar_relatorio(metricas, base_predita)
    SAIDA_RELATORIO.write_text(relatorio, encoding="utf-8")

    print(relatorio)
    print("")
    print(f"Arquivo de predições salvo em: {SAIDA_PREDICOES}")
    print(f"Modelo salvo em: {SAIDA_MODELO}")
    print(f"Relatório salvo em: {SAIDA_RELATORIO}")


if __name__ == "__main__":
    main()
