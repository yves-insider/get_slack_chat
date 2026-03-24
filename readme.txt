# Exportador de mensagens do Slack por semestre

Este script exporta mensagens de um canal do Slack para arquivos `.txt`, separando o conteúdo por semestre.

Ele:

- busca mensagens do canal com a API do Slack
- pagina automaticamente todos os resultados do período
- inclui respostas de threads
- respeita rate limit com retry automático
- salva cada semestre em um arquivo `.txt` separado

## Requisitos

- Python 3.9+
- token válido do Slack
- acesso ao canal desejado

## Dependências

Instale as bibliotecas necessárias:

```bash
pip install requests python-dotenv