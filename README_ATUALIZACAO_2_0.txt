Atualização SISCOMEX JSON Generator - Versão 2.0

Arquivos alterados/adicionados:
- app.py
- process_edicao_json.py
- process_catalogo.py
- process_vinculos.py
- requirements.txt

Principais mudanças:
1. App abre direto, sem tela de login.
2. Aba "Corrigir JSON de Lote": mantém a estrutura de cadastro em lote e corrige codigosInterno, removendo .0 e preservando 5 dígitos.
3. Aba "Gerar Body de Retificação": converte JSON de lote para o body de edição/retificação de produto existente, removendo campos que não pertencem ao body:
   - seq
   - cpfCnpjRaiz
   - situacao
   - fabricantesProdutores
4. Normalização de SKU aplicada em:
   - geração do catálogo;
   - correção de JSON de lote;
   - geração de body de retificação.
5. A geração de body de retificação pode opcionalmente receber uma planilha com SKU, Código Produto Siscomex e Versão para montar pacote com path + body.

Atenção:
Sem Código Produto Siscomex e Versão, o app gera apenas bodies de retificação, não um pacote pronto para envio via API.
