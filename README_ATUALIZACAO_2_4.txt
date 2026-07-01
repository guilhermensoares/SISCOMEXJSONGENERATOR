Atualização 2.4 - SISCOMEX JSON Generator

Ajustes desta versão:

1. Compactador de Aplicações
- A prévia deixou de mostrar a planilha inteira processada.
- Agora a tela mostra apenas as descrições que realmente foram alteradas.
- Foi adicionada uma tabela-resumo com linha do Excel, SKU, código fabricante, NCM, descrição em português e redução de caracteres.
- Foi adicionado um comparativo "Antes x Depois" em blocos expansíveis, para permitir auditoria visual da descrição original e da descrição compactada.
- O app agora também gera um arquivo "log_comparativo_aplicacoes.xlsx" com todas as alterações.

2. Interface
- Layout alterado para wide, melhorando a visualização das descrições longas e tabelas.
- Rodapé atualizado para Versão 2.4.

3. Regras preservadas
- A lógica original do compactador foi mantida.
- As rotinas de Catálogo de Produtos e Vínculo Fabricante-Exportador continuam sem refatoração operacional.
- As features de Corrigir JSON de Lote e Gerar Body de Retificação continuam removidas da interface.
