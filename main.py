#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper OLX - Extração de Dados de Anúncios
Extrai informações de anúncios do OLX usando Selenium (Chrome headless)
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
    from selenium.common.exceptions import (
        TimeoutException, 
        NoSuchElementException, 
        WebDriverException
    )
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


def setup_logging():
    """
    Configura o sistema de logging do projeto.
    Cria arquivo de log na pasta logs/ e também exibe no console.
    """
    # Cria pasta logs se não existir
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Nome do arquivo de log com data/hora
    log_filename = os.path.join(log_dir, f'olx_scraper_{datetime.now().strftime("%Y%m%d")}.log')
    
    # Configura formato do log
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Configura logging
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("="*60)
    logger.info("Sistema de logging inicializado")
    logger.info(f"Arquivo de log: {log_filename}")
    logger.info("="*60)
    
    return logger


# Inicializa o logger global
logger = setup_logging()

# Log sobre disponibilidade do Selenium
if not SELENIUM_AVAILABLE:
    logger.warning("Selenium não está disponível. Instale com: pip install selenium webdriver-manager")
    logger.warning("O script usará apenas requests como fallback (pode não funcionar com conteúdo dinâmico)")
else:
    logger.info("Selenium disponível - será usado como método principal de extração")


def get_headers() -> Dict[str, str]:
    """
    Retorna headers HTTP personalizados para simular um navegador real.
    
    Returns:
        Dict com headers HTTP configurados
    """
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.olx.com.br/',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Cache-Control': 'max-age=0'
    }


def fetch_page(url: str) -> Optional[BeautifulSoup]:
    """
    Faz requisição HTTP para a URL e retorna o HTML parseado.
    
    Args:
        url: URL do anúncio do OLX
        
    Returns:
        BeautifulSoup object com o HTML parseado ou None em caso de erro
    """
    try:
        logger.info(f"Iniciando requisição HTTP para: {url}")
        headers = get_headers()
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        logger.info(f"Requisição bem-sucedida. Status: {response.status_code}")
        logger.debug(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        # Verifica se a resposta é HTML válido
        if 'text/html' not in response.headers.get('Content-Type', ''):
            warning_msg = f"A resposta não parece ser uma página HTML válida. Content-Type: {response.headers.get('Content-Type', 'N/A')}"
            logger.warning(warning_msg)
            print("⚠️  Aviso: A resposta não parece ser uma página HTML válida.")
            return None
            
        soup = BeautifulSoup(response.content, 'lxml')
        logger.info("HTML parseado com sucesso")
        return soup
        
    except requests.exceptions.Timeout as e:
        error_msg = f"Timeout ao fazer requisição HTTP para {url}: {e}"
        logger.error(error_msg, exc_info=True)
        print(f"❌ Erro: Timeout ao buscar a página. Tente novamente.")
        return None
    except requests.exceptions.HTTPError as e:
        error_msg = f"Erro HTTP ao fazer requisição para {url}: {e} - Status: {e.response.status_code if hasattr(e, 'response') else 'N/A'}"
        logger.error(error_msg, exc_info=True)
        print(f"❌ Erro ao fazer requisição HTTP: {e}")
        return None
    except requests.exceptions.RequestException as e:
        error_msg = f"Erro de requisição para {url}: {e}"
        logger.error(error_msg, exc_info=True)
        print(f"❌ Erro ao fazer requisição HTTP: {e}")
        return None
    except Exception as e:
        error_msg = f"Erro inesperado ao buscar página {url}: {e}"
        logger.error(error_msg, exc_info=True)
        print(f"❌ Erro inesperado ao buscar página: {e}")
        return None


def extract_vendor_name_selenium(driver: webdriver.Chrome, soup: BeautifulSoup) -> Optional[str]:
    """
    Extrai o nome do vendedor usando Selenium com limpeza agressiva de "sujeira" (ex: Último acesso).
    
    Args:
        driver: WebDriver do Selenium
        soup: BeautifulSoup object com o HTML parseado
        
    Returns:
        Nome do vendedor ou None se não encontrado
    """
    
    def _clean_name(raw_name):
        """Remove cirurgicamente frases administrativas do OLX do nome."""
        if not raw_name:
            return None
        # Remove "Último acesso" e tudo que vem depois (mesmo se estiver colado: HenriqueÚltimo)
        clean = re.sub(r'(?i)último\s*acesso.*', '', raw_name)
        # Remove "Conta verificada"
        clean = re.sub(r'(?i)conta\s*verificada.*', '', clean)
        # Remove "Na OLX desde"
        clean = re.sub(r'(?i)na\s*olx\s*desde.*', '', clean)
        # Remove quebras de linha e espaços extras
        clean = clean.split('\n')[0]
        return clean.strip()
    
    # --- TENTATIVA 1: Seletor Específico do Nome do Vendedor (Prioridade) ---
    try:
        # Seletor específico encontrado: span.typo-body-large.ad__sc-ypp2u2-4.TTTuh
        elements = driver.find_elements(By.CSS_SELECTOR, 'span.typo-body-large.ad__sc-ypp2u2-4.TTTuh')
        for elem in elements:
            try:
                text = elem.text.strip()
                if text:
                    nome = _clean_name(text)
                    if nome and 2 < len(nome) < 50:
                        logger.debug(f"Nome encontrado (Selenium Seletor Específico): {nome}")
                        return nome
            except Exception:
                continue
    except Exception:
        pass
    
    # --- TENTATIVA 2: Seletores Oficiais (Fallback) ---
    try:
        # Seletor do box do vendedor
        elements = driver.find_elements(By.CSS_SELECTOR, '.ad__sc-ypp2u2-12, div[data-testid="account-box"]')
        for elem in elements:
            try:
                # Tenta pegar apenas o texto direto ou primeiro filho
                text = elem.text.strip()
                if text:
                    nome = _clean_name(text)
                    if nome and 2 < len(nome) < 50:
                        logger.debug(f"Nome encontrado (Selenium Box): {nome}")
                        return nome
            except Exception:
                continue
    except Exception:
        pass
    
    # --- TENTATIVA 3: XPath Específico para o Nome (H1/H2 ou Strong dentro do box) ---
    try:
        # Procura tags de texto dentro do box de perfil
        xpaths = [
            "//div[contains(@class, 'ad__sc-ypp2u2-12')]//span",
            "//div[@data-testid='account-box']//span",
            "//div[contains(text(), 'Último acesso')]/preceding-sibling::span",  # Span antes do "Último acesso"
            "//div[contains(text(), 'Último acesso')]/..//span"  # Span vizinho
        ]
        
        for xpath in xpaths:
            elements = driver.find_elements(By.XPATH, xpath)
            for el in elements:
                txt = el.text.strip()
                # O nome não deve conter "Último acesso"
                if txt and "acesso" not in txt.lower() and "olx" not in txt.lower() and len(txt) > 2:
                    nome = _clean_name(txt)
                    if nome and 2 < len(nome) < 50:
                        logger.debug(f"Nome encontrado (Selenium XPath): {nome}")
                        return nome
    except Exception:
        pass

    # Fallback para o BS4 se o Selenium não pegar limpo
    return extract_vendor_name(soup)


def extract_vendor_name(soup: BeautifulSoup) -> Optional[str]:
    """
    Extrai o nome do vendedor usando BeautifulSoup com separator para evitar concatenação.
    
    Args:
        soup: BeautifulSoup object com o HTML parseado
        
    Returns:
        Nome do vendedor ou None se não encontrado
    """
    
    def _clean_name(raw_name):
        """Remove cirurgicamente frases administrativas do OLX do nome."""
        if not raw_name:
            return None
        # Remove "Último acesso" (Case insensitive)
        clean = re.sub(r'(?i)último\s*acesso.*', '', raw_name)
        clean = re.sub(r'(?i)conta\s*verificada.*', '', clean)
        clean = re.sub(r'(?i)na\s*olx\s*desde.*', '', clean)
        # Remove sufixos comuns de captura errada
        clean = re.sub(r' - .*', '', clean)
        clean = clean.split('\n')[0]
        return clean.strip()
    
    # --- TENTATIVA 1: Seletor Específico do Nome do Vendedor (Prioridade) ---
    try:
        # Seletor específico encontrado: span.typo-body-large.ad__sc-ypp2u2-4.TTTuh
        elements = soup.select('span.typo-body-large.ad__sc-ypp2u2-4.TTTuh')
        for elem in elements:
            text = elem.get_text(strip=True)
            if text:
                nome = _clean_name(text)
                if nome and 2 < len(nome) < 50:
                    logger.debug(f"Nome encontrado (BS4 Seletor Específico): {nome}")
                    return nome
    except Exception:
        pass
    
    # --- TENTATIVA 2: Busca Estrutural com Separator ---
    try:
        # Procura o container do perfil
        # Seletores comuns de containers de perfil no OLX
        profile_containers = soup.select('.ad__sc-ypp2u2-12, div[data-testid="account-box"]')
        
        for container in profile_containers:
            # get_text com separator é CRUCIAL para separar "Henrique" de "Último acesso"
            text = container.get_text(separator=' | ', strip=True)
            
            # Agora o texto deve vir algo como: "Henrique | Último acesso há..."
            parts = text.split('|')
            if parts:
                nome = _clean_name(parts[0])
                if nome and 2 < len(nome) < 50:
                    logger.debug(f"Nome encontrado (BS4 Container): {nome}")
                    return nome
    except Exception:
        pass

    # --- TENTATIVA 3: Regex no Texto da Página (Fallback) ---
    try:
        all_text = soup.get_text(separator=' ')
        
        # Procura padrões como "Henrique Na OLX desde..."
        # Regex captura a palavra ANTES de "Na OLX desde" ou "Último acesso"
        patterns = [
            r'([A-ZÁÉÍÓÚÂÊÔÇ][a-záéíóúâêôç]+(?:\s+[A-ZÁÉÍÓÚÂÊÔÇ][a-záéíóúâêôç]+)?)\s+(?:Na OLX desde|Último acesso)',
            r'Conta verificada\s+([A-ZÁÉÍÓÚÂÊÔÇ][a-záéíóúâêôç]+(?:\s+[A-ZÁÉÍÓÚÂÊÔÇ][a-záéíóúâêôç]+)?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, all_text, re.IGNORECASE)
            if match:
                nome = _clean_name(match.group(1))
                if nome and 2 < len(nome) < 50:
                    # Filtro extra para garantir que não pegamos palavras de menu
                    if not any(x in nome.lower() for x in ['menu', 'buscar', 'chat', 'entrar']):
                        logger.debug(f"Nome encontrado (BS4 Regex): {nome}")
                        return nome
    except Exception:
        pass

    logger.warning("Nome do vendedor não encontrado após tentar todos os padrões")
    return None


def extract_vehicle_model_selenium(driver: webdriver.Chrome, soup: BeautifulSoup) -> Optional[str]:
    """
    Extrai o modelo do veículo usando Selenium com seletores oficiais do OLX.
    Baseado nos seletores oficiais: .ad__sc-wuor06-0.hfcCRQ span.olx-color-neutral-120 (busca por texto "MODELO") ou h1
    
    Args:
        driver: WebDriver do Selenium
        soup: BeautifulSoup object com o HTML parseado
        
    Returns:
        Modelo do veículo ou None se não encontrado
    """
    # Método 1: Seletor oficial do OLX
    # Conforme seletores_olx.md: .ad__sc-wuor06-0.hfcCRQ span.olx-color-neutral-120 - Busca por texto "MODELO", fallback para título h1
    try:
        # Primeiro tenta o seletor oficial direto
        spans = driver.find_elements(By.CSS_SELECTOR, '.ad__sc-wuor06-0.hfcCRQ span.olx-color-neutral-120')
        for span in spans:
            try:
                # Verifica se está próximo a um elemento que contenha "Modelo" (conforme observação)
                parent = span.find_element(By.XPATH, './ancestor::*[contains(@class, "ad__sc-wuor06-0") or contains(@class, "hfcCRQ")]')
                parent_text = parent.text
                if 'Modelo' in parent_text or 'MODELO' in parent_text:
                    text = span.text.strip()
                    if text and len(text) > 3:
                        # Remove ano se estiver no final
                        text = re.sub(r'\s+\d{4}$', '', text)
                        text = re.sub(r'\s+', ' ', text).strip()
                        logger.debug(f"Modelo do veículo encontrado com seletor oficial .ad__sc-wuor06-0.hfcCRQ span.olx-color-neutral-120: {text}")
                        return text
            except (NoSuchElementException, Exception):
                continue
        
        # Se não encontrou, busca elementos que contenham "Modelo" e procura o span próximo
        modelo_elements = driver.find_elements(By.XPATH, '//*[contains(text(), "Modelo") or contains(text(), "MODELO")]')
        for elem in modelo_elements:
            try:
                # Procura o span com o seletor oficial no mesmo container
                parent = elem.find_element(By.XPATH, './ancestor::*[contains(@class, "ad__sc-wuor06-0") or contains(@class, "hfcCRQ")]')
                span = parent.find_element(By.CSS_SELECTOR, 'span.olx-color-neutral-120')
                text = span.text.strip()
                if text and len(text) > 3:
                    text = re.sub(r'\s+\d{4}$', '', text)
                    text = re.sub(r'\s+', ' ', text).strip()
                    logger.debug(f"Modelo do veículo encontrado próximo a texto MODELO: {text}")
                    return text
            except (NoSuchElementException, Exception):
                continue
    except Exception as e:
        logger.debug(f"Erro ao buscar modelo com seletores oficiais: {e}")
    
    # Método 2: Priorizar H1 (título do anúncio) - mais confiável que regex
    try:
        h1 = driver.find_element(By.CSS_SELECTOR, 'h1')
        text = h1.text.strip()
        if text and len(text) > 5:
            # Remove partes indesejadas: ID do anúncio, "| OLX", preço, ano, etc.
            text = re.sub(r'\s*-\s*\d+\s*\|.*', '', text, flags=re.I)  # Remove "- 1457220451 | OLX"
            text = re.sub(r'\s*\|\s*OLX.*', '', text, flags=re.I)  # Remove "| OLX"
            text = re.sub(r'\s*-\s*OLX.*', '', text, flags=re.I)  # Remove "- OLX"
            text = re.sub(r'\s*-\s*R\$\s*[\d.,]+.*', '', text)  # Remove "- R$..."
            text = re.sub(r'\s*R\$\s*[\d.,]+.*', '', text)  # Remove "R$..."
            text = re.sub(r'\s*-\s*\d{4}.*', '', text)  # Remove "- 2020..." e tudo depois
            text = re.sub(r'\s+\d{4}.*', '', text)  # Remove ano e tudo depois
            text = re.sub(r'\s+', ' ', text).strip()
            if text and len(text) > 3:
                logger.debug(f"Modelo do veículo encontrado no título h1: {text}")
                return text
    except (NoSuchElementException, Exception) as e:
        logger.debug(f"Erro ao buscar modelo no h1: {e}")
    
    # Método 3: Abordagem estrutural - busca por label "Modelo" e pega próximo elemento
    try:
        # Procura elementos com texto exato "Modelo" (case-insensitive)
        modelo_labels = driver.find_elements(By.XPATH, '//*[normalize-space(text())="Modelo" or normalize-space(text())="MODELO"]')
        for label in modelo_labels:
            try:
                parent = label.find_element(By.XPATH, './parent::*')
                if parent:
                    # Tenta pegar o próximo irmão (estrutura comum em grids)
                    try:
                        next_sibling = parent.find_element(By.XPATH, './following-sibling::*[1]')
                        text = next_sibling.text.strip()
                        if text and len(text) > 3 and len(text) < 100:  # Validação: não muito longo
                            text = re.sub(r'\s+\d{4}$', '', text)  # Remove ano
                            text = re.sub(r'\s+', ' ', text).strip()
                            logger.debug(f"Modelo do veículo encontrado por abordagem estrutural (irmão): {text}")
                            return text
                    except:
                        pass
                    
                    # Ou tenta pegar link/span dentro do mesmo container
                    try:
                        value_link = parent.find_element(By.XPATH, './/a | .//span[contains(@class, "color")]')
                        text = value_link.text.strip()
                        if text and len(text) > 3 and len(text) < 100:
                            text = re.sub(r'\s+\d{4}$', '', text)
                            text = re.sub(r'\s+', ' ', text).strip()
                            logger.debug(f"Modelo do veículo encontrado por abordagem estrutural (container): {text}")
                            return text
                    except:
                        pass
            except:
                continue
    except Exception as e:
        logger.debug(f"Erro na abordagem estrutural: {e}")
    
    # Método 4: Regex refinado (fallback) - para antes de palavras-chave
    try:
        page_text = driver.find_element(By.TAG_NAME, 'body').text
        # Regex que para ao encontrar "Marca", "Tipo", "Ano", "Potência", "Cor" ou fim da string
        model_match = re.search(r'Modelo\s*:?\s*(.+?)(?=\s*(?:Marca|Tipo|Ano|Potência|Cor|Combustível|$))', page_text, re.I)
        if model_match:
            text = model_match.group(1).strip()
            # Remove ano e limpa
            text = re.sub(r'\s+\d{4}.*', '', text)
            text = re.sub(r'\s+', ' ', text).strip()
            if text and len(text) > 3 and len(text) < 100:  # Validação: não muito longo
                logger.debug(f"Modelo do veículo encontrado por regex refinado: {text}")
                return text
    except Exception as e:
        logger.debug(f"Erro ao buscar modelo com regex: {e}")
    
    # Método 4: Fallback para BeautifulSoup
    return extract_vehicle_model(soup)


def extract_vehicle_model(soup: BeautifulSoup) -> Optional[str]:
    """
    Extrai o modelo do veículo usando BeautifulSoup com seletores oficiais do OLX.
    Baseado nos seletores oficiais: .ad__sc-wuor06-0.hfcCRQ span.olx-color-neutral-120 (busca por texto "MODELO") ou h1
    
    Args:
        soup: BeautifulSoup object com o HTML parseado
        
    Returns:
        Modelo do veículo ou None se não encontrado
    """
    # Método 1: Seletor oficial do OLX
    # Conforme seletores_olx.md: .ad__sc-wuor06-0.hfcCRQ span.olx-color-neutral-120 - Busca por texto "MODELO", fallback para título h1
    try:
        # Tenta o seletor oficial direto primeiro
        spans = soup.select('.ad__sc-wuor06-0.hfcCRQ span.olx-color-neutral-120')
        for span in spans:
            # Verifica se está próximo a um elemento que contenha "Modelo" ou "MODELO" (conforme observação)
            parent = span.find_parent()
            if parent:
                parent_text = parent.get_text()
                if 'Modelo' in parent_text or 'MODELO' in parent_text:
                    text = span.get_text(strip=True)
                    if text and len(text) > 3:
                        # Remove ano se estiver no final
                        text = re.sub(r'\s+\d{4}$', '', text)
                        text = re.sub(r'\s+', ' ', text).strip()
                        logger.debug(f"Modelo do veículo encontrado com seletor oficial .ad__sc-wuor06-0.hfcCRQ span.olx-color-neutral-120: {text}")
                        return text
        
        # Se não encontrou, busca elementos que contenham "Modelo" e procura o span próximo
        modelo_labels = soup.find_all(string=re.compile(r'Modelo|MODELO', re.I))
        for label in modelo_labels:
            parent = label.find_parent()
            if parent:
                # Procura o span com a classe oficial no mesmo container
                container = parent.find_parent(class_=re.compile(r'ad__sc-wuor06-0|hfcCRQ'))
                if container:
                    span = container.find('span', class_=re.compile(r'olx-color-neutral-120'))
                    if span:
                        text = span.get_text(strip=True)
                        if text and len(text) > 3:
                            text = re.sub(r'\s+\d{4}$', '', text)
                            text = re.sub(r'\s+', ' ', text).strip()
                            logger.debug(f"Modelo do veículo encontrado próximo a texto MODELO: {text}")
                            return text
    except Exception as e:
        logger.debug(f"Erro ao buscar modelo com seletores oficiais: {e}")
    
    # Método 2: Priorizar H1 (título do anúncio) - mais confiável que regex
    h1 = soup.select_one('h1')
    if h1:
        text = h1.get_text(strip=True)
        if text and len(text) > 5:
            # Remove partes indesejadas: ID do anúncio, "| OLX", preço, ano, etc.
            text = re.sub(r'\s*-\s*\d+\s*\|.*', '', text, flags=re.I)  # Remove "- 1457220451 | OLX"
            text = re.sub(r'\s*\|\s*OLX.*', '', text, flags=re.I)  # Remove "| OLX"
            text = re.sub(r'\s*-\s*OLX.*', '', text, flags=re.I)  # Remove "- OLX"
            text = re.sub(r'\s*-\s*R\$\s*[\d.,]+.*', '', text)  # Remove "- R$..."
            text = re.sub(r'\s*R\$\s*[\d.,]+.*', '', text)  # Remove "R$..."
            text = re.sub(r'\s*-\s*\d{4}.*', '', text)  # Remove "- 2020..." e tudo depois
            text = re.sub(r'\s+\d{4}.*', '', text)  # Remove ano e tudo depois
            text = re.sub(r'\s+', ' ', text).strip()
            if text and len(text) > 3:
                logger.debug(f"Modelo do veículo encontrado no título h1: {text}")
                return text
    
    # Método 3: Abordagem estrutural - busca por label "Modelo" e pega próximo elemento
    try:
        # Procura elementos com texto exato "Modelo" (case-insensitive)
        modelo_labels = soup.find_all(string=re.compile(r'^Modelo$', re.I))
        for label in modelo_labels:
            parent = label.find_parent()
            if parent:
                # Tenta pegar o próximo irmão (estrutura comum em grids)
                next_sibling = parent.find_next_sibling()
                if next_sibling:
                    text = next_sibling.get_text(strip=True)
                    if text and len(text) > 3 and len(text) < 100:  # Validação: não muito longo
                        text = re.sub(r'\s+\d{4}$', '', text)  # Remove ano
                        text = re.sub(r'\s+', ' ', text).strip()
                        logger.debug(f"Modelo do veículo encontrado por abordagem estrutural (irmão): {text}")
                        return text
                
                # Ou tenta pegar link dentro do mesmo container
                value_link = parent.parent.find('a')
                if value_link:
                    text = value_link.get_text(strip=True)
                    if text and len(text) > 3 and len(text) < 100:
                        text = re.sub(r'\s+\d{4}$', '', text)
                        text = re.sub(r'\s+', ' ', text).strip()
                        logger.debug(f"Modelo do veículo encontrado por abordagem estrutural (container): {text}")
                        return text
    except Exception as e:
        logger.debug(f"Erro na abordagem estrutural: {e}")
    
    # Método 4: Regex refinado (fallback) - para antes de palavras-chave
    # Usa separator=' ' para evitar texto grudado (ex: "MarcaVolkswagen" -> "Marca Volkswagen")
    all_text = soup.get_text(separator=' ')
    # Regex que para ao encontrar "Marca", "Tipo", "Ano", "Potência", "Cor" ou fim da string
    model_match = re.search(r'Modelo\s*:?\s*(.+?)(?=\s*(?:Marca|Tipo|Ano|Potência|Cor|Combustível|$))', all_text, re.I)
    if model_match:
        text = model_match.group(1).strip()
        text = re.sub(r'\s+\d{4}.*', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        if text and len(text) > 3 and len(text) < 100:  # Validação: não muito longo
            logger.debug(f"Modelo do veículo encontrado por regex refinado: {text}")
            return text
    
    logger.warning("Modelo do veículo não encontrado após tentar todos os seletores")
    return None


def extract_price_selenium(driver: webdriver.Chrome, soup: BeautifulSoup) -> Optional[str]:
    """
    Extrai o valor do anúncio usando Selenium com seletores oficiais do OLX.
    Baseado nos seletores oficiais: h2.olx-text.olx-text--title-large.olx-text--block.ad__sc-1leoitd-0.bJHaGt ou h2.ad__sc-1leoitd-0
    
    Args:
        driver: WebDriver do Selenium
        soup: BeautifulSoup object com o HTML parseado
        
    Returns:
        Valor do anúncio formatado ou None se não encontrado
    """
    # Método 1: Seletores oficiais do OLX (prioridade)
    try:
        # Seletor oficial principal
        h2_elements = driver.find_elements(By.CSS_SELECTOR, 'h2.olx-text.olx-text--title-large.olx-text--block.ad__sc-1leoitd-0.bJHaGt')
        for h2 in h2_elements:
            text = h2.text.strip()
            price_match = re.search(r'R\$\s*[\d.,]+', text)
            if price_match:
                logger.debug(f"Valor do anúncio encontrado com seletor oficial principal: {price_match.group(0)}")
                return price_match.group(0)
        
        # Seletor alternativo oficial
        h2_elements = driver.find_elements(By.CSS_SELECTOR, 'h2.ad__sc-1leoitd-0')
        for h2 in h2_elements:
            text = h2.text.strip()
            price_match = re.search(r'R\$\s*[\d.,]+', text)
            if price_match:
                logger.debug(f"Valor do anúncio encontrado com seletor oficial alternativo: {price_match.group(0)}")
                return price_match.group(0)
    except Exception as e:
        logger.debug(f"Erro ao buscar preço com seletores oficiais: {e}")
    
    # Método 2: Seletores genéricos (fallback)
    selenium_selectors = [
        (By.CSS_SELECTOR, 'h2[data-ds-component="DS-Text"]'),
        (By.XPATH, '//h2[contains(text(), "R$")]'),
        (By.XPATH, '//span[contains(text(), "R$")]'),
    ]
    
    for by, selector in selenium_selectors:
        try:
            elements = driver.find_elements(by, selector)
            for element in elements:
                text = element.text.strip()
                price_match = re.search(r'R\$\s*[\d.,]+', text)
                if price_match:
                    logger.debug(f"Valor do anúncio encontrado com seletor genérico: {price_match.group(0)}")
                    return price_match.group(0)
        except (TimeoutException, NoSuchElementException):
            continue
    
    # Método 3: Fallback para BeautifulSoup
    return extract_price(soup)


def extract_price(soup: BeautifulSoup) -> Optional[str]:
    """
    Extrai o valor do anúncio usando BeautifulSoup com seletores oficiais do OLX.
    Baseado nos seletores oficiais: h2.olx-text.olx-text--title-large.olx-text--block.ad__sc-1leoitd-0.bJHaGt ou h2.ad__sc-1leoitd-0
    
    Args:
        soup: BeautifulSoup object com o HTML parseado
        
    Returns:
        Valor do anúncio formatado ou None se não encontrado
    """
    # Método 1: Seletores oficiais do OLX
    try:
        # Seletor oficial principal
        h2_elements = soup.select('h2.olx-text.olx-text--title-large.olx-text--block.ad__sc-1leoitd-0.bJHaGt')
        for h2 in h2_elements:
            text = h2.get_text(strip=True)
            price_match = re.search(r'R\$\s*[\d.,]+', text)
            if price_match:
                logger.debug(f"Valor do anúncio encontrado com seletor oficial principal: {price_match.group(0)}")
                return price_match.group(0)
        
        # Seletor alternativo oficial
        h2_elements = soup.select('h2.ad__sc-1leoitd-0')
        for h2 in h2_elements:
            text = h2.get_text(strip=True)
            price_match = re.search(r'R\$\s*[\d.,]+', text)
            if price_match:
                logger.debug(f"Valor do anúncio encontrado com seletor oficial alternativo: {price_match.group(0)}")
                return price_match.group(0)
    except Exception as e:
        logger.debug(f"Erro ao buscar preço com seletores oficiais: {e}")
    
    # Método 2: Seletores genéricos (fallback)
    price_selectors = [
        'h2[data-ds-component="DS-Text"]',
        'span[class*="price"]',
        'h2[class*="price"]',
    ]
    
    for selector in price_selectors:
        elements = soup.select(selector)
        for element in elements:
            text = element.get_text(strip=True)
            price_match = re.search(r'R\$\s*[\d.,]+', text)
            if price_match:
                logger.debug(f"Valor do anúncio encontrado usando seletor genérico: {price_match.group(0)}")
                return price_match.group(0)
    
    # Método 3: Busca por padrão em qualquer texto
    all_text = soup.get_text()
    price_matches = re.findall(r'R\$\s*[\d.,]+', all_text)
    if price_matches:
        logger.debug(f"Valor do anúncio encontrado usando busca por padrão: {price_matches[0]}")
        return price_matches[0]
    
    logger.warning("Valor do anúncio não encontrado após tentar todos os seletores")
    return None


def extract_fipe_price_selenium(driver: webdriver.Chrome, soup: BeautifulSoup) -> Optional[str]:
    """
    Extrai o preço FIPE usando Selenium com seletores oficiais do OLX.
    Baseado nos seletores oficiais: .LkJa2kno (children[0]) - mapeia valores, busca label "PREÇO FIPE"
    
    Args:
        driver: WebDriver do Selenium
        soup: BeautifulSoup object com o HTML parseado
        
    Returns:
        Preço FIPE formatado ou None se não encontrado
    """
    # Método 1: Seletor oficial do OLX - .LkJa2kno
    try:
        # Busca elementos com a classe .LkJa2kno
        fipe_containers = driver.find_elements(By.CSS_SELECTOR, '.LkJa2kno')
        for container in fipe_containers:
            try:
                # Verifica se contém o label "PREÇO FIPE" (children[1])
                container_text = container.text
                if 'PREÇO FIPE' in container_text.upper() or 'FIPE' in container_text.upper():
                    # Pega o primeiro filho (children[0]) que contém o valor
                    first_child = container.find_element(By.XPATH, './child::*[1]')
                    text = first_child.text.strip()
                    price_match = re.search(r'R\$\s*[\d.,]+', text)
                    if price_match:
                        logger.debug(f"Preço FIPE encontrado com seletor oficial .LkJa2kno: {price_match.group(0)}")
                        return price_match.group(0)
            except:
                continue
    except Exception as e:
        logger.debug(f"Erro ao buscar FIPE com seletor oficial: {e}")
    
    # Método 2: Busca por texto "PREÇO FIPE" ou "FIPE"
    try:
        fipe_elements = driver.find_elements(By.XPATH, '//*[contains(text(), "FIPE") or contains(text(), "fipe")]')
        for elem in fipe_elements:
            try:
                # Busca o preço próximo ao elemento
                parent = elem.find_element(By.XPATH, './ancestor::*[1]')
                text = parent.text
                price_match = re.search(r'R\$\s*[\d.,]+', text)
                if price_match:
                    logger.debug(f"Preço FIPE encontrado próximo a texto FIPE: {price_match.group(0)}")
                    return price_match.group(0)
            except:
                continue
    except:
        pass
    
    # Método 3: Fallback para BeautifulSoup
    return extract_fipe_price(soup)


def extract_fipe_price(soup: BeautifulSoup) -> Optional[str]:
    """
    Extrai o preço FIPE usando BeautifulSoup com seletores oficiais do OLX.
    Baseado nos seletores oficiais: .LkJa2kno (children[0]) - mapeia valores, busca label "PREÇO FIPE"
    
    Args:
        soup: BeautifulSoup object com o HTML parseado
        
    Returns:
        Preço FIPE formatado ou None se não encontrado
    """
    # Método 1: Seletor oficial do OLX - .LkJa2kno
    try:
        fipe_containers = soup.select('.LkJa2kno')
        for container in fipe_containers:
            container_text = container.get_text()
            # Verifica se contém o label "PREÇO FIPE"
            if 'PREÇO FIPE' in container_text.upper() or 'FIPE' in container_text.upper():
                # Pega o primeiro filho (children[0]) que contém o valor
                first_child = container.find(True)  # Primeiro elemento filho
                if first_child:
                    text = first_child.get_text(strip=True)
                    price_match = re.search(r'R\$\s*[\d.,]+', text)
                    if price_match:
                        logger.debug(f"Preço FIPE encontrado com seletor oficial .LkJa2kno: {price_match.group(0)}")
                        return price_match.group(0)
    except Exception as e:
        logger.debug(f"Erro ao buscar FIPE com seletor oficial: {e}")
    
    # Método 2: Busca por texto "PREÇO FIPE" ou "FIPE"
    fipe_elements = soup.find_all(string=re.compile(r'FIPE|fipe', re.I))
    for elem in fipe_elements:
        parent = elem.find_parent()
        if parent:
            # Procura pelo preço próximo ao texto FIPE
            for _ in range(3):
                if parent:
                    text = parent.get_text()
                    price_match = re.search(r'R\$\s*[\d.,]+', text)
                    if price_match:
                        logger.debug(f"Preço FIPE encontrado próximo a texto FIPE: {price_match.group(0)}")
                        return price_match.group(0)
                    parent = parent.parent
    
    logger.debug("Preço FIPE não encontrado (campo opcional)")
    return None


def setup_selenium_driver() -> Optional[webdriver.Chrome]:
    """
    Configura e retorna um driver Selenium com Chrome em modo headless.
    
    Returns:
        WebDriver do Chrome ou None em caso de erro
    """
    if not SELENIUM_AVAILABLE:
        logger.error("Selenium não está disponível. Instale com: pip install selenium webdriver-manager")
        return None
    
    try:
        logger.info("Configurando Selenium WebDriver (Chrome headless)...")
        
        # Opções do Chrome
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Modo headless (sem abrir janela)
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--lang=pt-BR')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Usa webdriver-manager para baixar/gerenciar ChromeDriver automaticamente
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.implicitly_wait(10)  # Espera implícita de 10 segundos
        
        logger.info("Selenium WebDriver configurado com sucesso")
        return driver
        
    except Exception as e:
        error_msg = f"Erro ao configurar Selenium WebDriver: {e}"
        logger.error(error_msg, exc_info=True)
        return None


def extract_data_selenium(url: str) -> Dict[str, Optional[str]]:
    """
    Extrai dados usando Selenium (método principal para conteúdo dinâmico).
    
    Args:
        url: URL do anúncio do OLX
        
    Returns:
        Dicionário com os dados extraídos
    """
    driver = None
    try:
        logger.info("Iniciando extração com Selenium...")
        driver = setup_selenium_driver()
        
        if not driver:
            logger.error("Não foi possível inicializar o Selenium WebDriver")
            return {
                'nome_vendedor': None,
                'modelo_veiculo': None,
                'valor_anuncio': None,
                'preco_fipe': None
            }
        
        # Acessa a URL
        logger.info(f"Acessando URL: {url}")
        driver.get(url)
        
        # Aguarda a página carregar completamente
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Aguarda elementos específicos carregarem (mais eficiente que sleep fixo)
        try:
            # Tenta aguardar pelo menos um elemento importante estar presente
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "R$")]'))
            )
        except TimeoutException:
            try:
                # Fallback: aguarda pelo menos o h1
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, "h1"))
                )
            except TimeoutException:
                logger.warning("Alguns elementos podem não ter carregado completamente")
        
        # Pequena espera adicional apenas se necessário
        time.sleep(1)
        
        # Obtém o HTML renderizado
        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')
        
        logger.info("HTML renderizado obtido com sucesso")
        
        # Extrai os dados usando os mesmos métodos, mas com HTML renderizado
        data = {
            'nome_vendedor': extract_vendor_name_selenium(driver, soup),
            'modelo_veiculo': extract_vehicle_model_selenium(driver, soup),
            'valor_anuncio': extract_price_selenium(driver, soup),
            'preco_fipe': extract_fipe_price_selenium(driver, soup)
        }
        
        # Log dos dados extraídos
        extracted_count = sum(1 for v in data.values() if v is not None)
        logger.info(f"Extração com Selenium concluída. {extracted_count}/4 campos extraídos com sucesso.")
        logger.debug(f"Dados extraídos: {data}")
        
        return data
        
    except TimeoutException as e:
        error_msg = f"Timeout ao carregar página com Selenium: {e}"
        logger.error(error_msg, exc_info=True)
        return {
            'nome_vendedor': None,
            'modelo_veiculo': None,
            'valor_anuncio': None,
            'preco_fipe': None
        }
    except Exception as e:
        error_msg = f"Erro ao extrair dados com Selenium: {e}"
        logger.error(error_msg, exc_info=True)
        return {
            'nome_vendedor': None,
            'modelo_veiculo': None,
            'valor_anuncio': None,
            'preco_fipe': None
        }
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Selenium WebDriver encerrado")
            except:
                pass


def extract_data(url: str) -> Dict[str, Optional[str]]:
    """
    Extrai todos os dados do anúncio.
    Tenta primeiro com Selenium, depois fallback para requests.
    
    Args:
        url: URL do anúncio do OLX
        
    Returns:
        Dicionário com os dados extraídos
    """
    logger.info("Iniciando extração de dados do anúncio")
    
    # Tenta primeiro com Selenium (método principal)
    if SELENIUM_AVAILABLE:
        logger.info("Tentando extração com Selenium (método recomendado)...")
        data = extract_data_selenium(url)
        
        # Se conseguiu extrair dados essenciais, retorna
        essential_fields = ['nome_vendedor', 'modelo_veiculo', 'valor_anuncio']
        if any(data.get(field) for field in essential_fields):
            return data
        else:
            logger.warning("Selenium não conseguiu extrair dados essenciais. Tentando fallback com requests...")
    
    # Fallback para requests (método antigo)
    logger.info("Usando método fallback (requests + BeautifulSoup)...")
    soup = fetch_page(url)
    
    if not soup:
        logger.error("Não foi possível obter o HTML da página. Abortando extração.")
        return {
            'nome_vendedor': None,
            'modelo_veiculo': None,
            'valor_anuncio': None,
            'preco_fipe': None
        }
    
    logger.info("Extraindo dados individuais...")
    data = {
        'nome_vendedor': extract_vendor_name(soup),
        'modelo_veiculo': extract_vehicle_model(soup),
        'valor_anuncio': extract_price(soup),
        'preco_fipe': extract_fipe_price(soup)
    }
    
    # Log dos dados extraídos
    extracted_count = sum(1 for v in data.values() if v is not None)
    logger.info(f"Extração concluída. {extracted_count}/4 campos extraídos com sucesso.")
    logger.debug(f"Dados extraídos: {data}")
    
    return data


def check_missing_data(data: Dict[str, Optional[str]]) -> bool:
    """
    Verifica se dados essenciais estão faltando e registra avisos.
    
    Args:
        data: Dicionário com os dados extraídos
        
    Returns:
        True se dados essenciais estão faltando, False caso contrário
    """
    essential_fields = ['nome_vendedor', 'modelo_veiculo', 'valor_anuncio']
    missing_fields = [field for field in essential_fields if not data.get(field)]
    
    if missing_fields:
        warning_msg = f"Dados essenciais não encontrados: {', '.join(missing_fields)}"
        logger.warning(warning_msg)
        logger.warning("Isso pode indicar que a página usa conteúdo dinâmico (JavaScript)")
        
        print("\n⚠️  AVISO: Alguns dados essenciais não foram encontrados:")
        for field in missing_fields:
            field_name = field.replace('_', ' ').title()
            print(f"   - {field_name}")
        print("\n💡 Isso pode indicar que a página usa conteúdo dinâmico (JavaScript).")
        print("   Se o problema persistir, considere usar Selenium para renderizar o JavaScript.")
        return True
    
    logger.info("Todos os dados essenciais foram encontrados com sucesso")
    return False


def display_results(data: Dict[str, Optional[str]]):
    """
    Exibe os resultados formatados no console.
    
    Args:
        data: Dicionário com os dados extraídos
    """
    print("\n" + "="*60)
    print("📋 DADOS DO ANÚNCIO")
    print("="*60)
    
    # Nome do vendedor
    nome = data.get('nome_vendedor') or "❌ Não encontrado"
    print(f"\n👤 Nome do Vendedor: {nome}")
    
    # Modelo do veículo
    modelo = data.get('modelo_veiculo') or "❌ Não encontrado"
    print(f"🚗 Modelo do Veículo: {modelo}")
    
    # Valor do anúncio
    valor = data.get('valor_anuncio') or "❌ Não encontrado"
    print(f"💰 Valor do Anúncio: {valor}")
    
    # Preço FIPE (opcional)
    fipe = data.get('preco_fipe') or "ℹ️  Não disponível"
    print(f"📊 Preço FIPE: {fipe}")
    
    print("="*60 + "\n")


def validate_url(url: str) -> bool:
    """
    Valida se a URL é uma URL válida do OLX.
    Aceita subdomínios como sp.olx.com.br, www.olx.com.br, etc.
    
    Args:
        url: URL a ser validada
        
    Returns:
        True se a URL é válida, False caso contrário
    """
    if not url:
        return False
    
    # Verifica se é uma URL válida do OLX (aceita qualquer subdomínio)
    url_pattern = re.compile(
        r'^https?://'  # http:// ou https://
        r'(?:[a-z0-9-]+\.)?'  # subdomínio opcional (sp., www., etc.)
        r'olx\.com\.br'  # domínio olx.com.br
        r'.*',  # resto da URL
        re.IGNORECASE
    )
    
    return bool(url_pattern.match(url))


def main():
    """Função principal do script CLI."""
    parser = argparse.ArgumentParser(
        description='Extrai dados de anúncios do OLX (nome do vendedor, modelo, valor e preço FIPE)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Exemplo de uso:\n  python main.py "https://sp.olx.com.br/regiao-de-sorocaba/autos-e-pecas/..."'
    )
    
    parser.add_argument(
        'url',
        nargs='?',
        help='URL do anúncio do OLX'
    )
    
    args = parser.parse_args()
    
    # Se não foi passada URL como argumento, tenta pegar da linha de comando
    url = args.url
    
    if not url:
        if len(sys.argv) > 1:
            url = sys.argv[1]
        else:
            # Solicita a URL interativamente
            print("="*60)
            print("🔍 SCRAPER OLX - Extração de Dados de Anúncios")
            print("="*60)
            print()
            url = input("📋 Cole a URL do anúncio do OLX: ").strip()
            
            if not url:
                print("\n❌ Erro: URL não fornecida.")
                sys.exit(1)
    
    # Valida a URL
    if not validate_url(url):
        error_msg = f"URL inválida ou não é do OLX: {url}"
        logger.error(error_msg)
        print(f"❌ Erro: URL inválida ou não é do OLX: {url}")
        print("   A URL deve começar com https://www.olx.com.br ou https://sp.olx.com.br")
        sys.exit(1)
    
    logger.info(f"Iniciando processamento do anúncio: {url}")
    print(f"🔍 Buscando dados do anúncio: {url}")
    print("⏳ Aguarde...\n")
    
    try:
        # Extrai os dados
        data = extract_data(url)
        
        # Verifica se há dados faltando
        has_missing = check_missing_data(data)
        
        # Exibe os resultados
        display_results(data)
        
        # Se houver dados faltando, sugere Selenium
        if has_missing:
            logger.info("Processamento concluído com dados faltando")
            print("💡 Dica: Se os dados não aparecerem, a página pode estar usando JavaScript.")
            print("   Considere implementar uma versão com Selenium para renderizar o conteúdo dinâmico.\n")
        else:
            logger.info("Processamento concluído com sucesso - todos os dados essenciais encontrados")
            
    except Exception as e:
        error_msg = f"Erro crítico durante o processamento: {e}"
        logger.critical(error_msg, exc_info=True)
        print(f"\n❌ Erro crítico: {e}")
        print("   Verifique o arquivo de log para mais detalhes.")
        sys.exit(1)


if __name__ == '__main__':
    main()

