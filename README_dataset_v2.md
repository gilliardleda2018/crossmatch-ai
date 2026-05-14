# Dataset CrossMatch IA V2

Dataset sintético calibrado para MVP de doação renal intervivos cruzada.

## Importante
Os dados NÃO são dados reais de pacientes. São dados sintéticos calibrados com premissas clínicas e logísticas plausíveis.

## Arquivos
- pares_doador_receptor_v2.csv: pares doador-receptor.
- matches_cruzados_v2.csv: possibilidades cruzadas avaliadas.
- ciclos_2_pares_v2.csv: ciclos de 2 pares.
- ciclos_3_pares_v2.csv: ciclos de 3 pares.
- dataset_doacao_cruzada_v2.xlsx: workbook consolidado.

## Melhorias em relação à V1
- 250 pares simulados.
- Distribuição ABO ajustada.
- PRA com faixa baixo/intermediário/alto.
- HLA simplificado em A, B e DR.
- Probabilidade de crossmatch dependente de PRA e HLA.
- Distância logística entre cidades.
- Probabilidade de desistência do doador.
- Score clínico-logístico.
- Regras de match mais restritivas.

## Resumo
- Pares: 250
- Matches registrados: 7941
- Matches viáveis: 2462
- Ciclos de 2 pares: 247
- Ciclos de 3 pares: 3327
