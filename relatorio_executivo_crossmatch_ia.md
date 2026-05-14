# CrossMatch IA  
## Sistema Inteligente de Apoio à Doação Renal Intervivos Cruzada

### 1. Problema

Muitos pacientes renais possuem familiares ou pessoas próximas dispostas a doar um rim, mas a doação direta pode não ser possível por incompatibilidade sanguínea, imunológica ou crossmatch positivo.

Nesses casos, a doação cruzada permite que pares incompatíveis sejam combinados com outros pares, formando ciclos nos quais cada doador beneficia um receptor compatível de outro núcleo familiar.

### 2. Solução proposta

O **CrossMatch IA** é um MVP de apoio à decisão para identificar, ranquear e simular combinações de doação renal intervivos cruzada.

O sistema não substitui a avaliação médica. Ele atua como ferramenta de inteligência para:

- organizar pares doador-receptor;
- identificar incompatibilidade original;
- avaliar possíveis matches cruzados;
- calcular probabilidade de viabilidade;
- encontrar ciclos de 2 e 3 pares;
- visualizar a rede de doação em grafo;
- apoiar comitês clínicos na priorização de análises.

### 3. Componentes do MVP

#### 3.1 Dataset sintético realista

Foram criados dados simulados com:

- tipo sanguíneo ABO;
- idade do doador e receptor;
- PRA do receptor;
- HLA simplificado;
- crossmatch;
- tempo de diálise;
- diabetes e hipertensão;
- risco cirúrgico;
- prioridade clínica;
- manifesto de doação;
- elegibilidade para doação cruzada.

#### 3.2 Motor de matching

O sistema constrói uma rede direcionada:

- nó: par doador-receptor;
- aresta: possibilidade do doador de um par doar para o receptor de outro;
- peso: score/probabilidade de sucesso.

O motor identifica:

- ciclos de 2 pares;
- ciclos de 3 pares;
- melhores combinações sem sobreposição.

#### 3.3 Modelo de IA

Foi treinado um modelo de classificação para prever a viabilidade de um match cruzado.

Modelo usado no MVP:

- Random Forest Classifier;
- variáveis clínicas e imunológicas sintéticas;
- saída: probabilidade de match viável.

Métricas obtidas no experimento:

- Acurácia: 89,59%;
- Precisão: 84,90%;
- Recall: 100%;
- ROC-AUC: 96,95%.

### 4. Dashboard

O dashboard Streamlit permite:

- visão geral dos pares;
- ranking inteligente de matches;
- análise individual por par;
- simulador de cadeia;
- grafo interativo;
- relatório técnico;
- aba de governança.

### 5. Impacto esperado

Uma versão real do sistema poderia apoiar:

- centrais de transplante;
- hospitais transplantadores;
- equipes de nefrologia;
- comissões de bioética;
- gestão pública de saúde.

Benefícios esperados:

- aumentar oportunidades de transplante intervivos;
- reduzir tempo em diálise;
- melhorar aproveitamento de doadores voluntários;
- apoiar decisões com dados;
- ampliar transparência e rastreabilidade.

### 6. Governança e limites éticos

O sistema deve obedecer princípios rígidos:

- não comercialização de órgãos;
- decisão final humana;
- consentimento informado;
- proteção de dados sensíveis;
- auditoria;
- explicabilidade;
- validação clínica;
- conformidade com legislação brasileira.

### 7. Próximos passos técnicos

1. Validar regras clínicas com especialistas em transplante renal.
2. Substituir dados sintéticos por dados anonimizados autorizados.
3. Incluir HLA real com maior granularidade.
4. Adicionar otimização matemática para ciclos múltiplos.
5. Criar API FastAPI para integração hospitalar.
6. Criar módulo de explicabilidade da IA.
7. Preparar submissão para edital de inovação em saúde.

### 8. Nome do produto

**CrossMatch IA**  
Inteligência aplicada à doação renal intervivos cruzada.
