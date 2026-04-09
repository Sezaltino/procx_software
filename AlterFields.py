import pandas as pd
import requests
import time

# --- CONFIGURAÇÕES ---
# Substitua pelo seu webhook completo (com a barra no final)
BITRIX_WEBHOOK_URL = "https://gowebby.bitrix24.com.br/rest/611/tx46pdllsik6n6xy/"
CAMINHO_PLANILHA = "/Users/gabrielsezaltino/Downloads/PAGOS - ENTRADA PAGA NÃO.xlsx" 
COLUNA_ID = "ID" 

def atualizar_deal(deal_id):
    url = f"{BITRIX_WEBHOOK_URL}crm.deal.update"
    
    # Payload configurado para o campo boolean UF_CRM_1769009854
    payload = {
        "id": deal_id,
        "fields": {
            "UF_CRM_1769009854": 1  # 1 para 'True' / Marcado
        }
    }
    
    try:
        response = requests.post(url, json=payload)
        data = response.json()
        
        if response.status_code == 200 and "result" in data:
            if data["result"] is True:
                return True, "Atualizado com sucesso"
            else:
                return False, "ID não encontrado ou sem permissão"
        else:
            erro = data.get("error_description", "Erro na API")
            return False, erro
            
    except Exception as e:
        return False, f"Erro de conexão: {str(e)}"

def main():
    print("--- INICIANDO PROCESSO DE ATUALIZAÇÃO ---")
    
    # 1. Leitura da planilha
    try:
        df = pd.read_excel(CAMINHO_PLANILHA)
        if COLUNA_ID not in df.columns:
            print(f"Erro: A coluna '{COLUNA_ID}' não foi encontrada na planilha.")
            return
    except Exception as e:
        print(f"Erro ao ler o arquivo: {e}")
        return

    relatorio = []
    total = len(df)

    # 2. Loop de processamento
    for i, row in df.iterrows():
        deal_id = int(row[COLUNA_ID])
        
        print(f"[{i+1}/{total}] Processando Deal ID: {deal_id}...", end="\r")
        
        sucesso, mensagem = atualizar_deal(deal_id)
        
        relatorio.append({
            "ID_DEAL": deal_id,
            "STATUS": "SUCESSO" if sucesso else "FALHA",
            "MOTIVO": mensagem
        })
        
        # Pausa de 0.2s (limite de 2 descritores por segundo para segurança)
        time.sleep(0.2)

    # 3. Geração do Relatório de saída
    df_result = pd.DataFrame(relatorio)
    nome_saida = "resultado_atualizacao_bitrix.xlsx"
    df_result.to_excel(nome_saida, index=False)
    
    print(f"\n\n--- PROCESSO CONCLUÍDO ---")
    print(f"Sucessos: {len(df_result[df_result['STATUS'] == 'SUCESSO'])}")
    print(f"Falhas: {len(df_result[df_result['STATUS'] == 'FALHA'])}")
    print(f"Relatório salvo como: {nome_saida}")

if __name__ == "__main__":
    main()