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
    data = {'nome_vendedor': None, 'modelo_veiculo': None, 'valor_anuncio': None, 'preco_fipe': None}
    
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

        # 2. Extração MODELO (Prioridade H1 ou campos específicos)
        # O H1 no OLX geralmente é "Modelo do Carro - Ano"
        h1 = soup.find('h1')
        if h1:
            title = clean_text(h1.get_text())
            # Remove sufixos comuns do OLX no título para limpar o modelo
            title = re.sub(r'\s*-\s*\d+\s*\|\s*OLX.*', '', title, flags=re.I)
            title = re.sub(r'\s*\|\s*OLX.*', '', title, flags=re.I)
            data['modelo_veiculo'] = title
        
        if not data['modelo_veiculo']:
            # Fallback: Procura label "Modelo"
            model_label = soup.find(string=re.compile(r'^Modelo$', re.I))
            if model_label:
                # Tenta o próximo link ou span
                next_elem = model_label.find_next(['a', 'span', 'p'])
                if next_elem: data['modelo_veiculo'] = clean_text(next_elem.get_text())

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

        # 4. Extração FIPE
        fipe_container = soup.find(string=re.compile(r'FIPE', re.I))
        if fipe_container:
            parent = fipe_container.find_parent()
            # Sobe na árvore até achar o container que tem o valor
            for _ in range(3):
                if not parent: break
                txt = parent.get_text()
                match = re.search(r'R\$\s*[\d.,]+', txt)
                if match:
                    data['preco_fipe'] = match.group(0)
                    break
                parent = parent.parent

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
    print(f"👤 Vendedor: {data['nome_vendedor']}")
    print(f"🚗 Modelo:   {data['modelo_veiculo']}")
    print(f"💰 Preço:    {data['valor_anuncio']}")
    print(f"📊 FIPE:     {data['preco_fipe']}")
    print("="*40)
    print(f"⏱️  Tempo total: {end_time - start_time:.2f} segundos")

if __name__ == '__main__':
    main()