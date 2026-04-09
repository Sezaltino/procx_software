# Configuração de exemplo para o script do Bitrix
# Copie este arquivo e renomeie para config.py, depois preencha com suas credenciais

# URL do Webhook do Bitrix24
# Formato: https://SEU_DOMINIO.bitrix24.com.br/rest/USER_ID/WEBHOOK_CODE/
BITRIX_WEBHOOK_URL = "https://suaempresa.bitrix24.com.br/rest/123/abc123def456/"

# Etapas dos deals a serem verificadas
ETAPAS = ["C1:4", "C1:LOSE"]

# IDs dos grupos de tarefas
GRUPOS_TAREFA = [519, 521, 513, 523]

# Data mínima para filtrar tarefas (ano, mês, dia)
DATA_MINIMA_ANO = 2024
DATA_MINIMA_MES = 11
DATA_MINIMA_DIA = 19
