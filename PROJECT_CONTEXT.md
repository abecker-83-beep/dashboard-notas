# Dashboard Notas - Contexto do Projeto

## Stack
- Streamlit
- Estrutura modular (pages + utils)

## Estrutura atual
- pages/
  - 1_Resumo.py
  - 2_Mapa.py
  - 3_Transportadoras.py
  - 4_Consulta.py
- utils/
  - business.py
  - load_data.py
  - ui.py

## Funcionalidades já implementadas

### Resumo
- KPIs operacionais
- Score de transportadoras (%)
- Classificação:
  - >=95 → Excelente
  - 89–94 → Atenção
  - <89 → Crítica
- Gráficos com cores semânticas
- Tabela "Onde agir agora"

### Consulta
- Filtros:
  - NF
  - UF
  - Cidade
  - Cliente
  - Transportadora
- KPIs dinâmicos
- Tabela detalhada
- Status com cores

### Transportadoras
- Filtro por transportadora
- KPIs dinâmicos por seleção
- Score médio
- Tabela executiva

## Padrões adotados
- Sempre usar df_filtrado após filtros
- Layout com card_kpi
- Cores:
  - vermelho → problema
  - amarelo → atenção
  - verde → ok
- Funções centralizadas em utils

## Próximos passos planejados
- Filtros globais
- Exportação Excel
- Ordenação inteligente
- Drill-down por transportadora
