Atualização 2.5 - SISCOMEX JSON Generator

Ajuste pontual na feature "Vinculador Código Siscomex".

O que mudou:
1. O vinculador voltou a seguir o fluxo operacional original:
   - o usuário informa a pasta onde estão os CSVs exportados do Catálogo Siscomex;
   - o app lê todos os arquivos .csv dessa pasta;
   - filtra somente produtos com Situação = Ativado;
   - abre/cria a planilha SKU_SISCOMEX_ATIVADOS_TODOS_ARQUIVOS.xlsx na mesma pasta;
   - preenche apenas SKUs que estavam sem código Siscomex;
   - adiciona SKUs novos que ainda não existiam na planilha;
   - salva o arquivo atualizado na própria pasta.

2. O app não pede mais para selecionar CSV por CSV no vinculador.

3. Proteções adicionadas na atualização da planilha:
   - se um SKU já possui código Siscomex preenchido, o código existente é preservado;
   - se o CSV trouxer um código diferente para um SKU já vinculado, o caso vai para o log de conflito;
   - se o mesmo SKU aparecer com códigos diferentes entre CSVs, o primeiro código encontrado é mantido e o conflito é registrado no log.

Arquivos alterados:
- app.py
- process_vinculador_siscomex.py

Arquivos não alterados na lógica:
- process_catalogo.py
- process_vinculos.py
- process_compactador_aplicacoes.py
- requirements.txt
