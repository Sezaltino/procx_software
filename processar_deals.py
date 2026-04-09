#!/usr/bin/env python3
"""
Script para processar deals do CSV e fazer requisições de cancelamento/pausa
"""

import csv
import requests
from typing import Dict, Set
from collections import defaultdict
import time

# Configurações
API_BASE_URL = "https://bitrix.prime2b.digital/api/canceldeal"
SECRET = "prime2b"
CSV_INPUT = "bitrix_resultados.csv"
CSV_OUTPUT = "resultados_processamento.csv"

# Delay entre requisições (em segundos) para evitar sobrecarga
DELAY_ENTRE_REQUISICOES = 2.0  # Aumentado para evitar rate limiting

# Configurações de retry
MAX_RETRIES = 3  # Número máximo de tentativas
RETRY_DELAY = 5  # Delay base para retry (será multiplicado a cada tentativa)


def ler_deals_do_csv(arquivo: str) -> Dict[str, Set[str]]:
    """
    Lê o CSV e agrupa deals únicos por etapa

    Args:
        arquivo: Caminho do arquivo CSV

    Returns:
        Dicionário com etapas como chave e set de IDs como valor
    """
    deals_por_etapa = defaultdict(set)

    try:
        with open(arquivo, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            for linha in reader:
                deal_id = linha.get('deal_id')
                etapa = linha.get('deal_etapa')

                if deal_id and etapa:
                    deals_por_etapa[etapa].add(deal_id)

        return dict(deals_por_etapa)

    except FileNotFoundError:
        print(f"Erro: Arquivo '{arquivo}' não encontrado!")
        print("Execute primeiro o script bitrix_cards_checker.py para gerar o CSV.")
        return {}


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
            response = requests.post(url, params=params, timeout=10)

            # Se for 429 (rate limit), espera e tenta novamente
            if response.status_code == 429 and tentativa < MAX_RETRIES - 1:
                delay = RETRY_DELAY * (tentativa + 1)
                print(f"    ⏳ Rate limit atingido. Aguardando {delay}s antes de tentar novamente...")
                time.sleep(delay)
                continue

            return {
                "deal_id": deal_id,
                "action": action,
                "status_code": response.status_code,
                "sucesso": response.status_code == 200,
                "resposta": response.text[:200],  # Primeiros 200 caracteres da resposta
                "tentativas": tentativa + 1
            }

        except requests.exceptions.RequestException as e:
            ultimo_erro = str(e)
            if tentativa < MAX_RETRIES - 1:
                delay = RETRY_DELAY * (tentativa + 1)
                print(f"    ⏳ Erro na requisição. Aguardando {delay}s antes de tentar novamente...")
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


def processar_todos_deals(deals_por_etapa: Dict[str, Set[str]]) -> list:
    """
    Processa todos os deals fazendo as requisições apropriadas

    Args:
        deals_por_etapa: Dicionário com deals agrupados por etapa

    Returns:
        Lista com resultados de todas as requisições
    """
    resultados = []
    total_deals = sum(len(deals) for deals in deals_por_etapa.values())
    processados = 0

    print(f"\nIniciando processamento de {total_deals} deals...\n")

    # Processa deals da etapa C1:4 (Pause)
    if "C1:4" in deals_por_etapa:
        deals_c1_4 = deals_por_etapa["C1:4"]
        print(f"Processando {len(deals_c1_4)} deals da etapa C1:4 (Pause)...")

        for deal_id in deals_c1_4:
            resultado = processar_deal(deal_id, "Pause")
            resultados.append(resultado)
            processados += 1

            status = "✓" if resultado["sucesso"] else "✗"
            print(f"  {status} Deal #{deal_id} - Status: {resultado['status_code']} [{processados}/{total_deals}]")

            time.sleep(DELAY_ENTRE_REQUISICOES)

    # Processa deals da etapa C1:LOSE (Cancel)
    if "C1:LOSE" in deals_por_etapa:
        deals_lose = deals_por_etapa["C1:LOSE"]
        print(f"\nProcessando {len(deals_lose)} deals da etapa C1:LOSE (Cancel)...")

        for deal_id in deals_lose:
            resultado = processar_deal(deal_id, "Cancel")
            resultados.append(resultado)
            processados += 1

            status = "✓" if resultado["sucesso"] else "✗"
            print(f"  {status} Deal #{deal_id} - Status: {resultado['status_code']} [{processados}/{total_deals}]")

            time.sleep(DELAY_ENTRE_REQUISICOES)

    return resultados


def exportar_resultados(resultados: list, arquivo: str):
    """
    Exporta os resultados do processamento para CSV

    Args:
        resultados: Lista de resultados
        arquivo: Nome do arquivo de saída
    """
    if not resultados:
        print("Nenhum resultado para exportar.")
        return

    with open(arquivo, 'w', newline='', encoding='utf-8-sig') as f:
        campos = ["deal_id", "action", "status_code", "sucesso", "resposta"]
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(resultados)

    print(f"\n✓ Resultados exportados para '{arquivo}'")


def gerar_resumo(resultados: list):
    """
    Gera e exibe resumo do processamento

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
    print("RESUMO DO PROCESSAMENTO")
    print("=" * 60)
    print(f"Total de deals processados: {total}")
    print(f"  ✓ Sucessos: {sucessos}")
    print(f"  ✗ Falhas: {falhas}")
    print()
    print(f"Action=Pause (C1:4):")
    print(f"  Total: {pause_total}")
    print(f"  Sucesso: {pause_sucesso}")
    print(f"  Falhas: {pause_total - pause_sucesso}")
    print()
    print(f"Action=Cancel (C1:LOSE):")
    print(f"  Total: {cancel_total}")
    print(f"  Sucesso: {cancel_sucesso}")
    print(f"  Falhas: {cancel_total - cancel_sucesso}")
    print("=" * 60)


def main():
    """
    Função principal
    """
    print("=" * 60)
    print("PROCESSADOR DE DEALS - PAUSE/CANCEL")
    print("=" * 60)
    print(f"CSV de entrada: {CSV_INPUT}")
    print(f"API: {API_BASE_URL}")
    print("=" * 60)

    # Lê deals do CSV
    deals_por_etapa = ler_deals_do_csv(CSV_INPUT)

    if not deals_por_etapa:
        print("\nNenhum deal encontrado para processar.")
        return

    # Mostra resumo do que será processado
    print("\nDeals encontrados:")
    for etapa, deals in deals_por_etapa.items():
        action = "Pause" if etapa == "C1:4" else "Cancel"
        print(f"  {etapa}: {len(deals)} deals → action={action}")

    # Confirmação
    print("\n⚠️  ATENÇÃO: Este script fará requisições para a API!")
    print(f"   - C1:4: {len(deals_por_etapa.get('C1:4', []))} deals serão PAUSADOS")
    print(f"   - C1:LOSE: {len(deals_por_etapa.get('C1:LOSE', []))} deals serão CANCELADOS")

    resposta = input("\nDeseja continuar? (sim/não): ").strip().lower()

    if resposta not in ['sim', 's', 'yes', 'y']:
        print("\nOperação cancelada pelo usuário.")
        return

    # Processa todos os deals
    resultados = processar_todos_deals(deals_por_etapa)

    # Exporta resultados
    exportar_resultados(resultados, CSV_OUTPUT)

    # Gera resumo
    gerar_resumo(resultados)

    print("\n✓ Processamento concluído!")


if __name__ == "__main__":
    main()
