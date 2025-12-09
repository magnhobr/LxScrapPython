#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper OLX - Otimizado (Fast Version)
"""

import sys
import re
import argparse
import logging
import os
import time
from datetime import datetime
from typing import Dict, Optional
import requests
from bs4 import BeautifulSoup

# Selenium imports
SELENIUM_AVAILABLE = False
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


def setup_logging():
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_filename = os.path.join(log_dir, f'olx_scraper_{datetime.now().strftime("%Y%m%d")}.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler(log_filename, encoding='utf-8'), logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def setup_selenium_driver() -> Optional[webdriver.Chrome]:
    if not SELENIUM_AVAILABLE:
        return None
    
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        # User agent comum para evitar bloqueios simples
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # --- OTIMIZAÇÃO 1: ESTRATÉGIA DE CARREGAMENTO ---
        # 'eager': O DOMContentLoaded disparou? Libera o script. Não espera imagens/css/ads.
        chrome_options.page_load_strategy = 'eager' 
        
        # --- OTIMIZAÇÃO 2: BLOQUEAR IMAGENS E CSS ---
        prefs = {
            "profile.managed_default_content_settings.images": 2,  # Bloqueia imagens
            "profile.default_content_setting_values.notifications": 2,
            "profile.managed_default_content_settings.stylesheets": 2,
            "profile.managed_default_content_settings.cookies": 1,
            "profile.managed_default_content_settings.javascript": 1,
            "profile.managed_default_content_settings.plugins": 1,
            "profile.managed_default_content_settings.popups": 2,
            "profile.managed_default_content_settings.geolocation": 2,
            "profile.managed_default_content_settings.media_stream": 2,
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Timeout reduzido para ser mais ágil na falha
        driver.implicitly_wait(2) 
        
        return driver
    except Exception as e:
        logger.error(f"Erro driver: {e}")
        return None

def clean_text(text):
    if not text: return None
    # Limpeza geral rápida
    text = re.sub(r'[\n\r\t]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def extract_data_selenium(url: str) -> Dict[str, Optional[str]]:
    driver = None
    data = {
        'id_anuncio': None,  # ID extraído da URL
        'nome_vendedor': None, 
        'marca_veiculo': None,
        'modelo_veiculo': None,  # Modelo extraído da URL
        'versao_veiculo': None,  # Versão extraída do H1
        'valor_anuncio': None, 
        'preco_fipe': None,
        'telefone': None,
        'quilometragem': None,
        'bairro': None,
        'cidade_estado_cep': None,
        'ano_veiculo': None,
        'preco_medio_olx': None,
        'link': None  # Link do anúncio no formato https://olx.com.br/vi/{id}
    }
    
    # Extração do ID do anúncio e MARCA da URL principal
    # Padrão: Número grande (8-10 dígitos) após hífen, pode estar no final ou antes de ? ou #
    # Exemplos:
    # .../mini-cooper-1-6-impecavel-1460372718
    # .../fiat-uno-mille-1-0-fire-f-flex-economy-2p-2002-1460309392?rec=h...
    # Remove query string e fragmento para buscar apenas no path
    url_path = url.split('?')[0].split('#')[0]
    # Busca números de 8-10 dígitos após hífen (para evitar pegar anos como 2002 que tem 4 dígitos)
    # Pode estar no final ou antes de ? ou #
    id_match = re.search(r'-(\d{8,10})(?:[?/#]|$)', url_path)
    if id_match:
        data['id_anuncio'] = id_match.group(1)
        logger.debug(f"ID do anúncio extraído da URL: {data['id_anuncio']}")
    else:
        # Fallback: busca números de 6+ dígitos (caso o ID tenha formato diferente)
        id_match = re.search(r'-(\d{6,})(?:[?/#]|$)', url_path)
        if id_match:
            data['id_anuncio'] = id_match.group(1)
            logger.debug(f"ID do anúncio extraído da URL (fallback): {data['id_anuncio']}")
    
    # Construção do link no formato https://olx.com.br/vi/{id}
    if data['id_anuncio']:
        data['link'] = f"https://olx.com.br/vi/{data['id_anuncio']}"
        logger.debug(f"Link construído: {data['link']}")
    
    # Extração da MARCA da URL principal (se disponível)
    # Padrão: .../autos-e-pecas/carros-vans-e-utilitarios/MARCA/...
    marca_url_match = re.search(r'/autos-e-pecas/carros-vans-e-utilitarios/([^/]+)/', url_path)
    if marca_url_match:
        marca_url = marca_url_match.group(1)
        marcas_validas = ['volkswagen', 'vw', 'fiat', 'chevrolet', 'ford', 'toyota', 'honda', 'hyundai', 'renault', 'peugeot', 'citroen', 'nissan', 'mitsubishi', 'suzuki', 'kia', 'jeep', 'ram', 'dodge', 'bmw', 'mercedes', 'audi', 'mini']
        if marca_url.lower() in [m.lower() for m in marcas_validas] or any(m.lower() in marca_url.lower() for m in marcas_validas):
            data['marca_veiculo'] = marca_url.replace('-', ' ').title()
            logger.debug(f"Marca encontrada na URL principal: {data['marca_veiculo']} (de: {marca_url})")
    
    try:
        logger.info("Iniciando Selenium (Modo Turbo)...")
        driver = setup_selenium_driver()
        if not driver: return data

        driver.get(url)
        
        # Espera explícita curta apenas pelo elemento principal (H1 ou Preço)
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
        except TimeoutException:
            logger.warning("Tempo limite aguardando H1, tentando extrair mesmo assim...")

        # --- ESTRATÉGIA RÁPIDA: PARSE VIA BEAUTIFULSOUP ---
        # Em vez de pedir pro Selenium buscar elemento por elemento (lento),
        # pegamos o HTML atual e processamos com BS4 (instantâneo).
        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')

        # 1. Extração PREÇO (Prioridade: span.typo-title-large)
        price_elem = soup.select_one('span.typo-title-large')
        if price_elem:
            val = clean_text(price_elem.get_text())
            # Regex para garantir que pegamos só o dinheiro
            match = re.search(r'R\$\s*[\d.,]+', val)
            if match: 
                data['valor_anuncio'] = match.group(0)
                logger.debug(f"Preço encontrado com seletor span.typo-title-large: {data['valor_anuncio']}")
        
        # Fallback: Tenta outros seletores se o principal não funcionar
        if not data['valor_anuncio']:
            price_elem = soup.find('h2', string=re.compile(r'R\$\s*[\d.,]+')) 
            if not price_elem:
                price_elem = soup.select_one('h2.ad__sc-1leoitd-0, h2[class*="price"]')
            
            if price_elem:
                val = clean_text(price_elem.get_text())
                match = re.search(r'R\$\s*[\d.,]+', val)
                if match: 
                    data['valor_anuncio'] = match.group(0)
                    logger.debug(f"Preço encontrado com fallback: {data['valor_anuncio']}")

        # 2. Extração VERSÃO (Prioridade H1 ou campos específicos)
        # O H1 no OLX geralmente é "Versão do Carro - Ano"
        h1 = soup.find('h1')
        if h1:
            title = clean_text(h1.get_text())
            # Remove sufixos comuns do OLX no título para limpar a versão
            title = re.sub(r'\s*-\s*\d+\s*\|\s*OLX.*', '', title, flags=re.I)
            title = re.sub(r'\s*\|\s*OLX.*', '', title, flags=re.I)
            data['versao_veiculo'] = title
        
        if not data['versao_veiculo']:
            # Fallback: Procura label "Modelo" ou "Versão"
            model_label = soup.find(string=re.compile(r'^Modelo$', re.I))
            if model_label:
                # Tenta o próximo link ou span
                next_elem = model_label.find_next(['a', 'span', 'p'])
                if next_elem: data['versao_veiculo'] = clean_text(next_elem.get_text())

        # 3. Extração VENDEDOR
        # Procura por "Nome | Último acesso" ou classes de perfil
        vendor_elem = soup.select_one('span.typo-body-large.ad__sc-ypp2u2-4')
        if vendor_elem:
            data['nome_vendedor'] = clean_text(vendor_elem.get_text())
        else:
            # Busca genérica por conteiner de perfil
            profile_box = soup.select_one('div[data-testid="account-box"], .ad__sc-ypp2u2-12')
            if profile_box:
                # O nome geralmente é o primeiro texto forte ou span grande
                txt = profile_box.get_text(separator='|', strip=True)
                parts = txt.split('|')
                if parts:
                    # Filtra lixo como "Último acesso"
                    nome = parts[0]
                    if "acesso" not in nome.lower() and len(nome) > 1:
                        data['nome_vendedor'] = nome

        # 4. Extração FIPE e PREÇO MÉDIO OLX
        # Busca pelos containers LkJa2kno e identifica pelo label dentro de cada um
        
        # Busca todos os containers com a classe LkJa2kno
        containers = soup.select('div.LkJa2kno')
        logger.debug(f"Containers LkJa2kno encontrados: {len(containers)}")
        
        for container in containers:
            # Busca o label dentro do container (span com data-variant="overline")
            label_elem = container.find('span', {'data-variant': 'overline'})
            if not label_elem:
                continue
            
            label_text = clean_text(label_elem.get_text()).upper()
            
            # Busca o preço dentro do container (span com as classes específicas)
            preco_elem = container.select_one('span[data-ds-component="DS-Text"].olx-text.olx-text--body-medium.olx-text--block.olx-text--bold')
            if not preco_elem:
                continue
            
            preco_text = clean_text(preco_elem.get_text())
            preco_match = re.search(r'R\$\s*[\d.,]+', preco_text)
            if not preco_match:
                continue
            
            preco_value = preco_match.group(0)
            
            # Identifica se é FIPE ou Preço Médio OLX pelo label
            if 'FIPE' in label_text and not data['preco_fipe']:
                data['preco_fipe'] = preco_value
                logger.debug(f"Preço FIPE encontrado: {data['preco_fipe']}")
            elif ('MÉDIO' in label_text or 'MEDIO' in label_text) and 'OLX' in label_text and not data['preco_medio_olx']:
                data['preco_medio_olx'] = preco_value
                logger.debug(f"Preço Médio OLX encontrado: {data['preco_medio_olx']}")
            
            # Se já encontrou ambos, pode parar
            if data['preco_fipe'] and data['preco_medio_olx']:
                break

        # 5. Extração TELEFONE
        # Seletor específico: span.ad__sc-14mcmsd-7.hORwFH ou span.typo-body-large.font-light.ad__sc-14mcmsd-7
        telefone_elem = soup.select_one('span.ad__sc-14mcmsd-7.hORwFH, span.typo-body-large.font-light.ad__sc-14mcmsd-7')
        if telefone_elem:
            telefone_text = clean_text(telefone_elem.get_text())
            telefone_match = re.search(r'\(?\d{2}\)?\s*\d{4,5}-?\d{4}', telefone_text)
            if telefone_match:
                data['telefone'] = telefone_match.group(0)
                logger.debug(f"Telefone encontrado: {data['telefone']}")
        
        # Fallback: Tenta o seletor anterior se o específico não funcionar
        if not data['telefone']:
            telefone_elem = soup.select_one('span.typo-body-large.text-neutral-120')
            if telefone_elem:
                telefone_text = clean_text(telefone_elem.get_text())
                telefone_match = re.search(r'\(?\d{2}\)?\s*\d{4,5}-?\d{4}', telefone_text)
                if telefone_match:
                    data['telefone'] = telefone_match.group(0)
                    logger.debug(f"Telefone encontrado (fallback): {data['telefone']}")

        # 6. Extração QUILOMETRAGEM
        km_elems = soup.select('span.ad__sc-hj0yqs-0.ekhFnR')
        logger.debug(f"Elementos de quilometragem encontrados: {len(km_elems)}")
        for km_elem in km_elems:
            # Pega apenas o texto direto do span (antes dos divs internos)
            # O valor está no texto principal do span, não nos divs filhos
            km_text = ''
            
            # Método 1: Itera pelos conteúdos diretos e pega apenas strings (texto direto)
            for content in km_elem.contents:
                if isinstance(content, str):
                    km_text += content.strip()
            
            # Método 2: Se não encontrou texto direto, pega o texto e filtra
            if not km_text or not km_text.strip():
                # Pega todo o texto do elemento
                km_text = km_elem.get_text(separator='', strip=True)
                # Remove tudo que não seja número (limpa divs internos e espaços)
                km_text = re.sub(r'[^\d]', '', km_text)
            
            # Extrai o primeiro número encontrado (o valor principal)
            if km_text and km_text.strip():
                km_match = re.search(r'\d+', km_text)
                if km_match:
                    km_value = km_match.group(0)
                    # Valida se é um número razoável de quilometragem (entre 0 e 9999999)
                    if km_value.isdigit() and 0 <= int(km_value) <= 9999999:
                        data['quilometragem'] = km_value
                        logger.debug(f"Quilometragem encontrada: {data['quilometragem']}")
                        break  # Para no primeiro elemento válido encontrado
        
        # Fallback: Se não encontrou, busca por texto "Quilometragem" e pega o próximo elemento
        if not data['quilometragem']:
            quilometragem_label = soup.find(string=re.compile(r'Quilometragem', re.I))
            if quilometragem_label:
                parent = quilometragem_label.find_parent()
                if parent:
                    # Procura o span com a classe específica no mesmo container
                    km_elem = parent.find('span', class_=re.compile(r'ad__sc-hj0yqs-0|ekhFnR'))
                    if km_elem:
                        km_text = ''
                        for content in km_elem.contents:
                            if isinstance(content, str):
                                km_text += content.strip()
                        if not km_text:
                            km_text = re.sub(r'[^\d]', '', km_elem.get_text(separator='', strip=True))
                        if km_text:
                            km_match = re.search(r'\d+', km_text)
                            if km_match:
                                km_value = km_match.group(0)
                                if km_value.isdigit() and 0 <= int(km_value) <= 9999999:
                                    data['quilometragem'] = km_value
                                    logger.debug(f"Quilometragem encontrada (fallback): {data['quilometragem']}")

        # 7. Extração BAIRRO
        bairro_elems = soup.select('span.typo-body-medium.font-semibold')
        for elem in bairro_elems:
            # Verifica se não é um link e não contém marca/ano
            if elem.name != 'a':
                bairro_text = clean_text(elem.get_text())
                # Filtra: não deve ser numérico de 4 dígitos (ano) nem marca conhecida
                if bairro_text and not re.match(r'^\d{4}$', bairro_text) and len(bairro_text) > 5:
                    # Verifica se não é marca conhecida (pode ser expandido)
                    marcas_conhecidas = ['volkswagen', 'fiat', 'chevrolet', 'ford', 'toyota', 'honda', 'hyundai', 'renault', 'peugeot', 'citroen']
                    if not any(marca.lower() in bairro_text.lower() for marca in marcas_conhecidas):
                        data['bairro'] = bairro_text
                        logger.debug(f"Bairro encontrado: {data['bairro']}")
                        break

        # 8. Extração CIDADE/ESTADO/CEP
        local_elem = soup.select_one('span.typo-body-small.font-semibold.text-neutral-110')
        if local_elem:
            local_text = clean_text(local_elem.get_text())
            if local_text:
                data['cidade_estado_cep'] = local_text
                logger.debug(f"Cidade/Estado/CEP encontrado: {data['cidade_estado_cep']}")

        # 9. Extração ANO, MARCA e MODELO (usam o mesmo seletor, diferenciar por conteúdo e URL)
        ano_marca_elems = soup.select('a.ad__sc-2h9gkk-3.lkkHCr')
        logger.debug(f"Elementos a.ad__sc-2h9gkk-3.lkkHCr encontrados: {len(ano_marca_elems)}")
        
        for elem in ano_marca_elems:
            text = clean_text(elem.get_text())
            href = elem.get('href', '')
            
            if text:
                # Verifica se é ano (4 dígitos numéricos)
                if re.match(r'^\d{4}$', text):
                    if not data['ano_veiculo']:
                        data['ano_veiculo'] = text
                        logger.debug(f"Ano encontrado: {data['ano_veiculo']}")
                # Se não é ano e não é muito curto, pode ser marca
                elif len(text) > 2 and not re.match(r'^\d+$', text):
                    # Verifica se não é versão (geralmente versões são mais longas e específicas)
                    if not data['marca_veiculo'] and len(text) < 20:
                        # Lista básica de marcas conhecidas para validação
                        marcas_validas = ['volkswagen', 'vw', 'fiat', 'chevrolet', 'ford', 'toyota', 'honda', 'hyundai', 'renault', 'peugeot', 'citroen', 'nissan', 'mitsubishi', 'suzuki', 'kia', 'jeep', 'ram', 'dodge', 'bmw', 'mercedes', 'audi', 'mini']
                        # Verifica se o texto contém ou é uma marca conhecida
                        text_lower = text.lower()
                        for marca in marcas_validas:
                            if marca.lower() == text_lower or marca.lower() in text_lower or text_lower in marca.lower():
                                data['marca_veiculo'] = text
                                logger.debug(f"Marca encontrada no texto: {data['marca_veiculo']}")
                                break
            
            # Extração da MARCA e MODELO da URL
            # Padrão da URL: .../autos-e-pecas/carros-vans-e-utilitarios/MARCA/MODELO/...
            if href:
                # Procura o padrão na URL: /autos-e-pecas/carros-vans-e-utilitarios/MARCA/MODELO/
                url_match = re.search(r'/autos-e-pecas/carros-vans-e-utilitarios/([^/]+)/([^/]+)/', href)
                if url_match:
                    marca_url = url_match.group(1)
                    modelo_url = url_match.group(2)
                    
                    # Extração da MARCA da URL (se ainda não foi encontrada)
                    if not data['marca_veiculo'] and marca_url:
                        # Lista de marcas conhecidas para validar
                        marcas_validas = ['volkswagen', 'vw', 'fiat', 'chevrolet', 'ford', 'toyota', 'honda', 'hyundai', 'renault', 'peugeot', 'citroen', 'nissan', 'mitsubishi', 'suzuki', 'kia', 'jeep', 'ram', 'dodge', 'bmw', 'mercedes', 'audi', 'mini']
                        if marca_url.lower() in [m.lower() for m in marcas_validas] or any(m.lower() in marca_url.lower() for m in marcas_validas):
                            data['marca_veiculo'] = marca_url.replace('-', ' ').title()
                            logger.debug(f"Marca encontrada na URL: {data['marca_veiculo']} (de: {marca_url})")
                    
                    # Extração do MODELO da URL
                    # Lista de segmentos que NÃO são modelo (estados, regiões, etc.)
                    segmentos_excluidos = [
                        'estado-sp', 'estado-pr', 'estado-rj', 'estado-mg', 'estado-sc', 'estado-rs', 
                        'estado-ba', 'estado-go', 'estado-pe', 'estado-ce', 'estado-df', 'estado-es',
                        'estado-ma', 'estado-ms', 'estado-mt', 'estado-pa', 'estado-pb', 'estado-pi',
                        'regiao-de-sorocaba', 'regiao', 'sao-paulo-e-regiao', 'zona-leste', 'zona-norte',
                        'zona-sul', 'zona-oeste', 'centro', 'grande-sao-paulo', 'abc'
                    ]
                    # Verifica se o modelo não é um segmento excluído e ainda não foi encontrado
                    if not data['modelo_veiculo'] and modelo_url and modelo_url.lower() not in [s.lower() for s in segmentos_excluidos]:
                        # Formata o modelo: substitui hífens por espaços e capitaliza
                        data['modelo_veiculo'] = modelo_url.replace('-', ' ').title()
                        logger.debug(f"Modelo encontrado na URL: {data['modelo_veiculo']} (de: {modelo_url} em href: {href[:80]})")

        logger.info(f"Dados extraídos: {data}")
        return data

    except Exception as e:
        logger.error(f"Erro Selenium: {e}")
        return data
    finally:
        if driver:
            try:
                # No modo eager, o quit às vezes trava se a página ainda estiver carregando scripts
                # Forçamos o fechamento.
                driver.quit()
            except:
                pass

def main():
    parser = argparse.ArgumentParser(description='OLX Scraper Fast')
    parser.add_argument('url', nargs='?', help='URL do anúncio')
    args = parser.parse_args()
    
    url = args.url
    if not url:
        # Se não tem argumento, pede input (modo interativo)
        print("="*60)
        print("🔍 SCRAPER OLX - Extração de Dados de Anúncios")
        print("="*60)
        print()
        print("📋 Cole a URL do anúncio do OLX e pressione Enter:")
        url = input().strip()
        
        # Remove caracteres invisíveis e espaços extras
        url = re.sub(r'[\s\u200b\u200c\u200d\ufeff]+', '', url)
        
        if not url:
            print("\n❌ Erro: URL não fornecida.")
            return

    # Validação melhorada da URL
    url_pattern = re.compile(
        r'^https?://'  # http:// ou https://
        r'(?:[a-z0-9-]+\.)?'  # subdomínio opcional (sp., www., etc.)
        r'olx\.com\.br'  # domínio olx.com.br
        r'.*',  # resto da URL
        re.IGNORECASE
    )
    
    if not url_pattern.match(url):
        print(f"\n❌ Erro: URL inválida ou não é do OLX.")
        print(f"   URL recebida: {url[:80]}...")
        print("   A URL deve começar com https://www.olx.com.br ou https://sp.olx.com.br")
        return

    print("🚀 Iniciando extração rápida...")
    start_time = time.time()
    
    data = extract_data_selenium(url)
    
    end_time = time.time()
    
    print("\n" + "="*40)
    print(f"🆔 ID:       {data['id_anuncio'] or 'Não encontrado'}")
    print(f"🏭 Marca:    {data['marca_veiculo'] or 'Não encontrado'}")
    print(f"🚗 Modelo:   {data['modelo_veiculo'] or 'Não encontrado'}")
    print(f"📋 Versão:   {data['versao_veiculo'] or 'Não encontrado'}")
    print(f"📅 Ano:      {data['ano_veiculo'] or 'Não encontrado'}")
    print(f"📏 KM:       {data['quilometragem'] or 'Não encontrado'}")
    print(f"💰 Anunciado: {data['valor_anuncio'] or 'Não encontrado'}")
    print(f"📊 FIPE:     {data['preco_fipe'] or 'Não encontrado'}")
    print(f"📈 Médio:    {data['preco_medio_olx'] or 'Não encontrado'}")
    print(f"👤 Vendedor: {data['nome_vendedor'] or 'Não encontrado'}")
    print(f"📞 Telefone:  {data['telefone'] or 'Não encontrado'}")
    print(f"📍 Bairro:   {data['bairro'] or 'Não encontrado'}")
    print(f"🌍 Local:    {data['cidade_estado_cep'] or 'Não encontrado'}")
    print(f"🔗 Link:     {data['link'] or 'Não encontrado'}")
    print("="*40)
    print(f"⏱️  Tempo total: {end_time - start_time:.2f} segundos")

if __name__ == '__main__':
    main()