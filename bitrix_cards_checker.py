#!/usr/bin/env python3
"""
Script para buscar cards do Bitrix em etapas específicas e verificar tarefas
"""

import requests
import csv
from datetime import datetime
from typing import List, Dict, Any
import json

# Configurações
BITRIX_WEBHOOK_URL = "https://gowebby.bitrix24.com.br/rest/611/tx46pdllsik6n6xy/"  # Substitua com sua URL de webhook
ETAPAS = ["C1:4", "C1:LOSE"]  # Etapas: inadimplente e LOSE
GRUPOS_TAREFA = [519, 521, 513, 523]  # IDs dos grupos
DATA_MINIMA = datetime(2024, 11, 19)  # Data mínima para filtrar tarefas


def fazer_requisicao(metodo: str, params: Dict[str, Any] = None) -> Dict:
    """
    Faz uma requisição à API do Bitrix24

    Args:
        metodo: Método da API (ex: 'crm.deal.list')
        params: Parâmetros da requisição

    Returns:
        Resposta da API em formato dict
    """
    url = f"{BITRIX_WEBHOOK_URL}{metodo}"

    if params is None:
        params = {}

    try:
        response = requests.post(url, json=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição: {e}")
        return {"result": []}


def buscar_deals_por_etapa(etapa: str) -> List[Dict]:
    """
    Busca todos os deals de uma etapa específica

    Args:
        etapa: ID da etapa (ex: 'C1:4')

    Returns:
        Lista de deals
    """
    print(f"Buscando deals na etapa {etapa}...")

    deals = []
    start = 0

    # Busca com paginação
    while True:
        params = {
            "filter": {"STAGE_ID": etapa},
            "select": ["ID", "TITLE", "STAGE_ID", "DATE_CREATE", "ASSIGNED_BY_ID"],
            "start": start
        }

        resultado = fazer_requisicao("crm.deal.list", params)

        if "result" in resultado and resultado["result"]:
            deals.extend(resultado["result"])
            start += 50  # Bitrix retorna 50 por vez por padrão

            # Se retornou menos que 50, chegamos ao fim
            if len(resultado["result"]) < 50:
                break
        else:
            break

    print(f"Encontrados {len(deals)} deals na etapa {etapa}")
    return deals


def buscar_tarefas_do_deal(deal_id: int) -> List[Dict]:
    """
    Busca tarefas associadas a um deal

    Args:
        deal_id: ID do deal

    Returns:
        Lista de tarefas
    """
    params = {
        "filter": {
            "UF_CRM_TASK": f"D_{deal_id}"  # Formato de vinculação deal-tarefa no Bitrix
        },
        "select": ["ID", "TITLE", "GROUP_ID", "CREATED_DATE", "CREATED_BY", "STATUS"]
    }

    resultado = fazer_requisicao("tasks.task.list", params)

    if "result" in resultado and "tasks" in resultado["result"]:
        return resultado["result"]["tasks"]

    return []


def filtrar_tarefas_por_grupo_e_data(tarefas: List[Dict]) -> List[Dict]:
    """
    Filtra tarefas pelos grupos especificados e data mínima

    Args:
        tarefas: Lista de tarefas

    Returns:
        Lista de tarefas filtradas
    """
    tarefas_filtradas = []

    for tarefa in tarefas:
        # Verifica se pertence aos grupos especificados
        grupo_id = int(tarefa.get("groupId", 0))
        if grupo_id not in GRUPOS_TAREFA:
            continue

        # Verifica data de criação
        try:
            data_criacao_str = tarefa.get("createdDate", "")
            # Formato: "2024-11-20T10:30:00+03:00"
            data_criacao = datetime.fromisoformat(data_criacao_str)

            # Remove timezone para comparação (converte para naive datetime)
            if data_criacao.tzinfo is not None:
                data_criacao = data_criacao.replace(tzinfo=None)

            if data_criacao >= DATA_MINIMA:
                tarefas_filtradas.append(tarefa)
        except (ValueError, AttributeError):
            continue

    return tarefas_filtradas


def processar_deals():
    """
    Processa todos os deals e suas tarefas, retornando os resultados
    """
    resultados = []

    # Busca deals de ambas as etapas
    for etapa in ETAPAS:
        deals = buscar_deals_por_etapa(etapa)

        for deal in deals:
            deal_id = deal.get("ID")
            deal_titulo = deal.get("TITLE", "Sem título")

            print(f"Verificando tarefas do deal #{deal_id}: {deal_titulo}")

            # Busca tarefas do deal
            tarefas = buscar_tarefas_do_deal(deal_id)

            # Filtra tarefas
            tarefas_filtradas = filtrar_tarefas_por_grupo_e_data(tarefas)

            if tarefas_filtradas:
                for tarefa in tarefas_filtradas:
                    resultados.append({
                        "deal_id": deal_id,
                        "deal_titulo": deal_titulo,
                        "deal_etapa": etapa,
                        "tarefa_id": tarefa.get("id"),
                        "tarefa_titulo": tarefa.get("title"),
                        "grupo_id": tarefa.get("groupId"),
                        "data_criacao": tarefa.get("createdDate"),
                        "status": tarefa.get("status")
                    })

    return resultados


def exportar_csv(resultados: List[Dict], arquivo: str = "bitrix_resultados.csv"):
    """
    Exporta os resultados para CSV

    Args:
        resultados: Lista de resultados
        arquivo: Nome do arquivo de saída
    """
    if not resultados:
        print("Nenhum resultado encontrado para exportar.")
        return

    with open(arquivo, 'w', newline='', encoding='utf-8-sig') as f:
        campos = ["deal_id", "deal_titulo", "deal_etapa", "tarefa_id",
                  "tarefa_titulo", "grupo_id", "data_criacao", "status"]

        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(resultados)

    print(f"\n✓ Resultados exportados para '{arquivo}'")
    print(f"Total de registros: {len(resultados)}")


def main():
    """
    Função principal
    """
    print("=" * 60)
    print("BITRIX - VERIFICADOR DE CARDS E TAREFAS")
    print("=" * 60)
    print(f"Etapas: {', '.join(ETAPAS)}")
    print(f"Grupos de tarefa: {', '.join(map(str, GRUPOS_TAREFA))}")
    print(f"Data mínima: {DATA_MINIMA.strftime('%d/%m/%Y')}")
    print("=" * 60)
    print()

    # Processa os deals e tarefas
    resultados = processar_deals()

    # Exporta para CSV
    exportar_csv(resultados)

    print("\n✓ Processamento concluído!")


if __name__ == "__main__":
    main()
