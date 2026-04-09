# Scripts de Verificação e Processamento de Deals do Bitrix

Conjunto de scripts Python para buscar cards (deals) do Bitrix24 em etapas específicas, verificar tarefas associadas e processar cancelamento/pausa.

## Funcionalidades

### Script 1: bitrix_cards_checker.py
- Busca deals nas etapas **C1:4** (Inadimplente) e **C1:LOSE**
- Verifica tarefas pertencentes aos grupos: **519, 521, 513, 523**
- Filtra tarefas com data de criação >= **19/11/2024**
- Exporta resultados para arquivo CSV

### Script 2: processar_deals.py
- Lê os deals do CSV gerado
- Faz requisições para pausar deals da etapa C1:4
- Faz requisições para cancelar deals da etapa C1:LOSE
- Retry automático em caso de erro 429 (rate limiting)
- Gera relatório do processamento

### Script 3: reprocessar_falhas.py (opcional)
- Lê deals que falharam do relatório anterior
- Reprocessa apenas os que falharam
- Delay e retry mais agressivos para lidar com rate limiting
- Gera relatório separado do reprocessamento

## Pré-requisitos

1. Python 3.7 ou superior
2. Acesso à API do Bitrix24 via Webhook

## Instalação

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Configuração

### Obter URL do Webhook do Bitrix24

1. Acesse seu Bitrix24
2. Vá em **Aplicativos** > **Webhooks** > **Webhooks de entrada**
3. Clique em **Adicionar webhook**
4. Marque as permissões necessárias:
   - `crm` (CRM - Deals)
   - `task` (Tarefas)
5. Copie a URL gerada (formato: `https://seudominio.bitrix24.com.br/rest/123/abc123/`)

### Configurar o Script

Abra o arquivo `bitrix_cards_checker.py` e substitua a linha:

```python
BITRIX_WEBHOOK_URL = "https://SEU_DOMINIO.bitrix24.com.br/rest/USER_ID/WEBHOOK_CODE/"
```

Pela URL do seu webhook.

### Ajustar Data (opcional)

Se quiser usar uma data diferente de 19/11/2024, altere a linha:

```python
DATA_MINIMA = datetime(2024, 11, 19)
```

## Uso

### Passo 1: Buscar e filtrar deals

Execute o script de verificação:

```bash
python bitrix_cards_checker.py
```

O script vai:
1. Buscar todos os deals nas etapas especificadas
2. Verificar tarefas de cada deal
3. Filtrar tarefas pelos grupos e data
4. Gerar arquivo `bitrix_resultados.csv` com os resultados

### Passo 2: Processar deals (Pause/Cancel)

Execute o script de processamento:

```bash
python processar_deals.py
```

O script vai:
1. Ler os deals do arquivo `bitrix_resultados.csv`
2. Solicitar confirmação antes de processar
3. Fazer requisições com retry automático para:
   - **C1:4**: Pausar deals (action=Pause)
   - **C1:LOSE**: Cancelar deals (action=Cancel)
4. Gerar arquivo `resultados_processamento.csv` com o status das requisições

**Recursos de retry:**
- Delay de 2s entre requisições
- Até 3 tentativas automáticas em caso de erro 429 (rate limit)
- Backoff exponencial (5s, 10s, 15s)

⚠️ **ATENÇÃO**: O script de processamento faz alterações via API! Confirme os dados antes de executar.

### Passo 3 (opcional): Reprocessar falhas

Se alguns deals falharam (erro 429, timeout, etc.), use o script de reprocessamento:

```bash
python reprocessar_falhas.py
```

O script vai:
1. Ler o arquivo `resultados_processamento.csv`
2. Filtrar apenas os deals que falharam (sucesso=False)
3. Reprocessá-los com delay maior (3s) e retry mais agressivo
4. Gerar arquivo `reprocessamento_resultados.csv`

**Recursos adicionais:**
- Delay de 3s entre requisições (maior que o script original)
- Até 3 tentativas com delay de 10s, 20s, 30s
- Ideal para reprocessar deals que falharam por rate limiting

## Formato dos CSVs

### bitrix_resultados.csv (gerado pelo script 1)

- **deal_id**: ID do deal no Bitrix
- **deal_titulo**: Título do deal
- **deal_etapa**: Etapa do deal (C1:4 ou C1:LOSE)
- **tarefa_id**: ID da tarefa
- **tarefa_titulo**: Título da tarefa
- **grupo_id**: ID do grupo da tarefa
- **data_criacao**: Data de criação da tarefa
- **status**: Status da tarefa

### resultados_processamento.csv (gerado pelo script 2)

- **deal_id**: ID do deal processado
- **action**: Ação executada (Pause ou Cancel)
- **status_code**: Código HTTP da resposta (200 = sucesso)
- **sucesso**: True/False indicando se foi bem-sucedido
- **resposta**: Resposta da API (primeiros 200 caracteres)

## Solução de Problemas

### Script 1: bitrix_cards_checker.py

**Erro de autenticação**
- Verifique se a URL do webhook está correta
- Confirme se o webhook tem as permissões necessárias (CRM e Tarefas)

**Nenhum resultado encontrado**
- Verifique se existem deals nas etapas C1:4 e C1:LOSE
- Confirme se os IDs dos grupos estão corretos
- Verifique se há tarefas criadas após 19/11/2024

**Timeout ou lentidão**
- O script pode demorar se houver muitos deals
- Considere reduzir o escopo ou adicionar filtros adicionais

### Script 2: processar_deals.py

**Arquivo CSV não encontrado**
- Execute primeiro o `bitrix_cards_checker.py`
- Verifique se o arquivo `bitrix_resultados.csv` existe no diretório

**Erro 401/403 na API**
- Verifique se o secret está correto (`secret=prime2b`)
- Confirme que a API está acessível e funcionando

**Algumas requisições falharam**
- Verifique o arquivo `resultados_processamento.csv` para detalhes
- Confira a coluna `resposta` para ver mensagens de erro específicas
- Pode ser necessário reprocessar deals que falharam

## Personalização

### Script 1: bitrix_cards_checker.py

Você pode ajustar as seguintes constantes no início do script:

```python
BITRIX_WEBHOOK_URL = "..."  # URL do webhook do Bitrix
ETAPAS = ["C1:4", "C1:LOSE"]  # Etapas a buscar
GRUPOS_TAREFA = [519, 521, 513, 523]  # Grupos de tarefas
DATA_MINIMA = datetime(2024, 11, 19)  # Data mínima
```

### Script 2: processar_deals.py

Você pode ajustar as seguintes constantes:

```python
API_BASE_URL = "https://bitrix.prime2b.digital/api/canceldeal"  # URL da API
SECRET = "prime2b"  # Secret para autenticação
CSV_INPUT = "bitrix_resultados.csv"  # Arquivo CSV de entrada
CSV_OUTPUT = "resultados_processamento.csv"  # Arquivo CSV de saída
DELAY_ENTRE_REQUISICOES = 2.0  # Segundos entre cada requisição
MAX_RETRIES = 3  # Número máximo de tentativas
RETRY_DELAY = 5  # Delay base para retry
```

### Script 3: reprocessar_falhas.py

Você pode ajustar as seguintes constantes:

```python
API_BASE_URL = "https://bitrix.prime2b.digital/api/canceldeal"  # URL da API
SECRET = "prime2b"  # Secret para autenticação
CSV_INPUT = "resultados_processamento.csv"  # Arquivo CSV de entrada
CSV_OUTPUT = "reprocessamento_resultados.csv"  # Arquivo CSV de saída
DELAY_ENTRE_REQUISICOES = 3.0  # Segundos entre requisições (mais conservador)
MAX_RETRIES = 3  # Número máximo de tentativas
RETRY_DELAY = 10  # Delay maior para reprocessamento
```

## API do Bitrix24

Documentação oficial: https://dev.1c-bitrix.ru/rest_help/

Métodos utilizados:
- `crm.deal.list` - Lista deals
- `tasks.task.list` - Lista tarefas
