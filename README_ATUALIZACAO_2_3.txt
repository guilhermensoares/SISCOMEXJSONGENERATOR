Atualização 2.3 - SISCOMEX JSON Generator

Objetivo desta versão:
- Incorporar ao app Streamlit dois scripts que antes eram usados por fora do fluxo:
  1. Compactador de Aplicações.
  2. Vinculador SKU x Código Siscomex.
- Remover da interface as features de:
  1. Corrigir JSON de Lote.
  2. Gerar Body de Retificação.

Arquivos alterados/adicionados:
- app.py
- process_compactador_aplicacoes.py
- process_vinculador_siscomex.py

Arquivos mantidos sem alteração lógica:
- process_catalogo.py
- process_vinculos.py
- requirements.txt

Novas operações no app:
1. Compactador de Aplicações
- Upload de planilha .xlsx.
- Coluna padrão: DESCRIÇÃO.
- Compacta aplicações repetidas por ano dentro da descrição.
- Exemplo: BMW X1 2012 / BMW X1 2013 / BMW X1 2014 -> BMW X1 2012 a 2014.
- Gera download em .xlsx.
- Mostra prévia e log das descrições alteradas.

2. Vinculador Código Siscomex
- Upload múltiplo de CSVs exportados do Catálogo de Produtos Siscomex.
- Filtra apenas registros com Situação = Ativado.
- Gera planilha SKU x código SISCOMEX.
- Nome de saída: SKU_SISCOMEX_ATIVADOS_TODOS_ARQUIVOS.xlsx.
- Mostra prévia e log de inconsistências quando algum CSV não tem as colunas esperadas.

Observações:
- As rotinas de Catálogo de Produtos e Vínculo Fabricante-Exportador continuam com loteamento fixo de 100 registros por arquivo.
- O módulo process_edicao_json.py deixou de ser chamado pelo app.py nesta versão.
- O arquivo process_edicao_json.py pode permanecer no repositório sem afetar o app, mas as features foram removidas da interface.
