#!/usr/bin/env python3
"""
Script para reprocessar deals que falharam no processamento anterior
"""

import csv
import requests
from typing import List, Dict
import time

# Configurações
API_BASE_URL = "https://bitrix.prime2b.digital/api/canceldeal"
SECRET = "prime2b"
CSV_INPUT = "resultados_processamento.csv"
CSV_OUTPUT = "reprocessamento_resultados.csv"

# Delay entre requisições (em segundos)
DELAY_ENTRE_REQUISICOES = 3.0  # Delay maior para evitar rate limiting

# Configurações de retry
MAX_RETRIES = 3
RETRY_DELAY = 10  # Delay mais longo para reprocessamento


def ler_falhas_do_csv(arquivo: str) -> List[Dict]:
    """
    Lê o CSV e filtra apenas os deals que falharam

    Args:
        arquivo: Caminho do arquivo CSV

    Returns:
        Lista de deals que falharam
    """
    falhas = []

    try:
        with open(arquivo, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            for linha in reader:
                sucesso = linha.get('sucesso', '').lower()

                # Filtra apenas os que falharam (sucesso = False)
                if sucesso == 'false':
                    falhas.append({
                        'deal_id': linha.get('deal_id'),
                        'action': linha.get('action'),
                        'erro_anterior': linha.get('resposta', '')
                    })

        return falhas

    except FileNotFoundError:
        print(f"Erro: Arquivo '{arquivo}' não encontrado!")
        print("Execute primeiro o script processar_deals.py")
        return []


def processar_deal(deal_id: str, action: str) -> Dict:
    """
    Faz requisição para processar um deal com retry automático

    Args:
        deal_id: ID do deal
        action: Ação a ser executada (Pause ou Cancel)

    Returns:
        Dicionário com resultado da requisição
    """
    url = f"{API_BASE_URL}/{deal_id}"
    params = {
        "secret": SECRET,
        "action": action
    }

    ultimo_erro = None

    # Tenta até MAX_RETRIES vezes
    for tentativa in range(MAX_RETRIES):
        try:
            response = requests.post(url, params=params, timeout=15)

            # Se for 429 (rate limit), espera e tenta novamente
            if response.status_code == 429 and tentativa < MAX_RETRIES - 1:
                delay = RETRY_DELAY * (tentativa + 1)
                print(f"    ⏳ Rate limit. Aguardando {delay}s...")
                time.sleep(delay)
                continue

            return {
                "deal_id": deal_id,
                "action": action,
                "status_code": response.status_code,
                "sucesso": response.status_code == 200,
                "resposta": response.text[:200],
                "tentativas": tentativa + 1
            }

        except requests.exceptions.RequestException as e:
            ultimo_erro = str(e)
            if tentativa < MAX_RETRIES - 1:
                delay = RETRY_DELAY * (tentativa + 1)
                print(f"    ⏳ Erro. Aguardando {delay}s...")
                time.sleep(delay)
            continue

    # Se chegou aqui, todas as tentativas falharam
    return {
        "deal_id": deal_id,
        "action": action,
        "status_code": 0,
        "sucesso": False,
        "resposta": f"Erro após {MAX_RETRIES} tentativas: {ultimo_erro}",
        "tentativas": MAX_RETRIES
    }


def reprocessar_falhas(falhas: List[Dict]) -> List[Dict]:
    """
    Reprocessa os deals que falharam

    Args:
        falhas: Lista de deals que falharam

    Returns:
        Lista com resultados do reprocessamento
    """
    resultados = []
    total = len(falhas)

    print(f"\nIniciando reprocessamento de {total} deals que falharam...\n")

    for i, falha in enumerate(falhas, 1):
        deal_id = falha['deal_id']
        action = falha['action']

        print(f"[{i}/{total}] Reprocessando Deal #{deal_id} (action={action})...")

        resultado = processar_deal(deal_id, action)
        resultados.append(resultado)

        status = "✓" if resultado["sucesso"] else "✗"
        print(f"  {status} Deal #{deal_id} - Status: {resultado['status_code']}")

        # Aguarda antes da próxima requisição
        if i < total:
            time.sleep(DELAY_ENTRE_REQUISICOES)

    return resultados


def exportar_resultados(resultados: List[Dict], arquivo: str):
    """
    Exporta os resultados do reprocessamento para CSV

    Args:
        resultados: Lista de resultados
        arquivo: Nome do arquivo de saída
    """
    if not resultados:
        print("Nenhum resultado para exportar.")
        return

    with open(arquivo, 'w', newline='', encoding='utf-8-sig') as f:
        campos = ["deal_id", "action", "status_code", "sucesso", "resposta", "tentativas"]
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(resultados)

    print(f"\n✓ Resultados exportados para '{arquivo}'")


def gerar_resumo(resultados: List[Dict]):
    """
    Gera e exibe resumo do reprocessamento

    Args:
        resultados: Lista de resultados
    """
    total = len(resultados)
    sucessos = sum(1 for r in resultados if r["sucesso"])
    falhas = total - sucessos

    pause_total = sum(1 for r in resultados if r["action"] == "Pause")
    pause_sucesso = sum(1 for r in resultados if r["action"] == "Pause" and r["sucesso"])

    cancel_total = sum(1 for r in resultados if r["action"] == "Cancel")
    cancel_sucesso = sum(1 for r in resultados if r["action"] == "Cancel" and r["sucesso"])

    print("\n" + "=" * 60)
    print("RESUMO DO REPROCESSAMENTO")
    print("=" * 60)
    print(f"Total de deals reprocessados: {total}")
    print(f"  ✓ Sucessos: {sucessos} ({sucessos/total*100:.1f}%)")
    print(f"  ✗ Falhas: {falhas} ({falhas/total*100:.1f}%)")
    print()
    print(f"Action=Pause:")
    print(f"  Total: {pause_total}")
    print(f"  Sucesso: {pause_sucesso}")
    print(f"  Falhas: {pause_total - pause_sucesso}")
    print()
    print(f"Action=Cancel:")
    print(f"  Total: {cancel_total}")
    print(f"  Sucesso: {cancel_sucesso}")
    print(f"  Falhas: {cancel_total - cancel_sucesso}")
    print("=" * 60)


def main():
    """
    Função principal
    """
    print("=" * 60)
    print("REPROCESSAMENTO DE DEALS QUE FALHARAM")
    print("=" * 60)
    print(f"CSV de entrada: {CSV_INPUT}")
    print(f"API: {API_BASE_URL}")
    print(f"Delay entre requisições: {DELAY_ENTRE_REQUISICOES}s")
    print(f"Máximo de tentativas por deal: {MAX_RETRIES}")
    print("=" * 60)

    # Lê falhas do CSV
    falhas = ler_falhas_do_csv(CSV_INPUT)

    if not falhas:
        print("\n✓ Não há deals que falharam para reprocessar!")
        return

    print(f"\nEncontrados {len(falhas)} deals que falharam")

    # Confirmação
    print("\n⚠️  Este script fará requisições para a API!")
    resposta = input("Deseja continuar? (sim/não): ").strip().lower()

    if resposta not in ['sim', 's', 'yes', 'y']:
        print("\nOperação cancelada pelo usuário.")
        return

    # Reprocessa os deals que falharam
    resultados = reprocessar_falhas(falhas)

    # Exporta resultados
    exportar_resultados(resultados, CSV_OUTPUT)

    # Gera resumo
    gerar_resumo(resultados)

    print("\n✓ Reprocessamento concluído!")


if __name__ == "__main__":
    main()
