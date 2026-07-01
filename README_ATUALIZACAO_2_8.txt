Atualização 2.8 - SISCOMEX JSON Generator

Ajuste desta versão:

1. Remoção temporária da feature "Vinculador Código Siscomex"
- A feature foi removida da interface do Streamlit porque o app está rodando em nuvem.
- Em ambiente de nuvem, o Streamlit não consegue acessar diretamente pastas locais/rede do computador do usuário, como K:\ ou C:\.
- A alternativa via ZIP/upload foi descartada por gerar retrabalho operacional e risco de divergência no fluxo de índice/corresp da base de itens.

2. Mantido sem refatoração o restante do app
- Catálogo de Produtos mantido.
- Vínculo Fabricante-Exportador mantido.
- Compactador de Aplicações mantido com prévia apenas das descrições alteradas.
- Cache de downloads mantido.
- Loteamento fixo de 100 registros mantido.

Arquivos mantidos no pacote:
- app.py
- process_catalogo.py
- process_vinculos.py
- process_compactador_aplicacoes.py
- requirements.txt
- Logo_branca_600px.png
- logo-novo-preto.png

Arquivo removido do pacote:
- process_vinculador_siscomex.py

Observação operacional:
O vinculador de código Siscomex deve continuar sendo usado localmente como script avulso, até uma futura solução mais integrada com API/armazenamento persistente.
