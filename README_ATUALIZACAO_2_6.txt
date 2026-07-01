Atualização 2.6 - SISCOMEX JSON Generator

Ajuste pontual na feature Vinculador Código Siscomex:

1. Seleção de pasta por janela nativa
- Adicionado botão "Selecionar pasta dos CSVs".
- O botão abre o seletor nativo de pasta do Windows no computador onde o Streamlit está rodando.
- Após selecionar a pasta, o caminho é preenchido automaticamente no campo da interface.

2. Fluxo operacional preservado
- Lê todos os CSVs da pasta selecionada.
- Abre/cria a planilha SKU_SISCOMEX_ATIVADOS_TODOS_ARQUIVOS.xlsx na mesma pasta.
- Preenche apenas vínculos faltantes.
- Preserva códigos já preenchidos.
- Adiciona SKUs novos encontrados nos CSVs.
- Mantém log de conflitos/inconsistências.

3. Sem refatoração do restante do app
- Catálogo de Produtos não alterado.
- Vínculo Fabricante-Exportador não alterado.
- Compactador de Aplicações não alterado.
- Processamento do vinculador não alterado, apenas a forma de selecionar a pasta.

Observação:
O seletor nativo depende de o app estar rodando localmente no Windows/desktop. Em servidor remoto ou nuvem, o navegador não consegue abrir a janela de pasta do computador do usuário por restrição de segurança.
