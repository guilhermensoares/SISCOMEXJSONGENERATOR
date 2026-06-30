Atualização 2.1 - SISCOMEX JSON Generator

Ajustes desta versão:

1. Loteamento travado em 100 registros por arquivo
- Catálogo de Produtos: sempre gera lotes de até 100 produtos.
- Vínculo Fabricante-Exportador: agora o limite considera a quantidade final de registros do JSON, não a quantidade de linhas do CSV. Uma linha pode gerar dois vínculos, por isso essa correção era necessária.
- Corrigir JSON de Lote: se o JSON corrigido tiver mais de 100 produtos, a saída é quebrada em Lote1, Lote2, etc.
- Gerar Body de Retificação: pacotes consolidados sem path e com path são quebrados em lotes de até 100 registros.

2. Campo Quantidade por lote removido da interface
- Para evitar erro operacional, o usuário não escolhe mais a quantidade do lote.
- A regra fica fixa em 100 registros por arquivo.

3. Normalização de SKU preservada
- 53907.0 -> 53907
- 1234.0 -> 01234
- 00123.0 -> 00123

4. Sem tela de login
- O app abre direto na tela principal.

Arquivos alterados:
- app.py
- process_catalogo.py
- process_vinculos.py
- process_edicao_json.py

Arquivo não alterado:
- requirements.txt
