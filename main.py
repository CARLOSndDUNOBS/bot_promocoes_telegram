import os
import json
import re
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    dados = {
        "chat_id": CHAT_ID,
        "text": mensagem
    }

    resposta = requests.post(url, data=dados)

    if resposta.status_code == 200:
        print("Mensagem enviada com sucesso.")
    else:
        print("Erro ao enviar mensagem.")
        print(resposta.text)


def limpar_preco(preco_texto):
    """
    Converte textos como:
    'R$ 1.199,90' -> 1199.90
    'R$ 799,99'   -> 799.99
    """
    preco_limpo = re.sub(r"[^\d,]", "", preco_texto)
    preco_limpo = preco_limpo.replace(",", ".")

    return float(preco_limpo)


def pegar_preco(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Language": "pt-BR,pt;q=0.9",
        "Accept": "text/html,application/xhtml+xml",
        "Connection": "keep-alive"
    }

    resposta = requests.get(url, headers=headers)

    print("Status code:", resposta.status_code)

    if resposta.status_code != 200:
        print("Erro ao acessar o site")
        return None

    soup = BeautifulSoup(resposta.text, "html.parser")

    preco_elemento = (
        soup.find("h4", {"class": "text-secondary-500"}) or
        soup.find("div", {"class": "mui-1jk88bq-price_vista-extraSpacePriceVista"})
    )

    print("Elemento encontrado:", preco_elemento)

    if preco_elemento:
        preco_texto = preco_elemento.text
        print("Preço em texto:", preco_texto)

        preco_atual = limpar_preco(preco_texto)
        print("Preço convertido:", preco_atual)

        return preco_atual

    return None


def carregar_produtos():
    with open("produtos.json", "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def carregar_historico():
    try:
        with open("historico.json", "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except FileNotFoundError:
        return {}


def salvar_historico(historico):
    with open("historico.json", "w", encoding="utf-8") as arquivo:
        json.dump(historico, arquivo, indent=4, ensure_ascii=False)


def verificar_promocoes():
    produtos = carregar_produtos()
    historico = carregar_historico()

    for produto in produtos:
        nome = produto["nome"]
        preco_alvo = produto["preco_alvo"]
        link = produto["link"]

        preco_atual = pegar_preco(link)

        if preco_atual is None:
            print(f"Erro ao pegar preço de {nome}")
            continue

        print(f"{nome} → R$ {preco_atual}")

        preco_antigo = historico.get(nome)

        if preco_atual <= preco_alvo:
            status = "🔥 PROMOÇÃO"
        else:
            status = "❌ Acima do preço"

        if preco_antigo != preco_atual:
            mensagem = f"""
{status}

Produto: {nome}
Preço atual: R$ {preco_atual}
Preço anterior: {preco_antigo}
Preço alvo: R$ {preco_alvo}

Link: {link}
"""
            enviar_telegram(mensagem)

            historico[nome] = preco_atual
        else:
            print(f"Sem mudança para {nome}")

    salvar_historico(historico)


verificar_promocoes()