#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coletor de Links OLX - Versão V6 (Multi-Layer Detection)
Melhoria: Adiciona leitura visual (DOM) e Meta Tags para garantir a contagem de páginas.
"""

import sys
import os
import re
import argparse
import logging
import time
import json
import math
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# Verifica dependências
try:
    from curl_cffi import requests as cffi_requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("❌ Erro: Instale as dependências com: pip install curl-cffi beautifulsoup4")

# --- Configuração ---
BROWSER_IMPERSONATE = "chrome124"
MAX_WORKERS = 4
SAFE_FALLBACK_PAGES = 50 # Aumentado um pouco o fallback

HEADERS = {
    "Referer": "https://www.google.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
}

def setup_logging():
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(log_dir, f'coletor_links_{timestamp}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger("OLX_COLETOR")

logger = setup_logging()

def get_page_url(base_url, page_num):
    parsed = urlparse(base_url)
    query_params = parse_qs(parsed.query)
    query_params['o'] = [str(page_num)]
    new_query = urlencode(query_params, doseq=True)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

def extract_number(text):
    """Limpa string e retorna inteiro (ex: '1.200' -> 1200)"""
    if not text: return 0
    try:
        # Remove pontos de milhar e tudo que não for dígito
        clean = re.sub(r'\D', '', text)
        return int(clean) if clean else 0
    except:
        return 0

def find_deep_total(data):
    """Recursivo: Procura chaves de contagem no JSON"""
    if isinstance(data, dict):
        for key, value in data.items():
            if key in ['totalAdCount', 'totalCount', 'totalAdsFound', 'total']:
                if isinstance(value, (int, float, str)) and str(value).isdigit() and int(value) > 0:
                    return int(value)
            
            # Navegação específica
            if key in ['ads', 'pagination', 'paging', 'meta'] and isinstance(value, dict):
                found = find_deep_total(value)
                if found: return found

            if isinstance(value, (dict, list)):
                found = find_deep_total(value)
                if found: return found
            
    elif isinstance(data, list):
        for item in data:
            found = find_deep_total(item)
            if found: return found
    return None

def try_extract_visible_total(soup):
    """Tenta encontrar o número visível na página (HTML)"""
    # Estratégia A: Texto "X resultados" ou "X anúncios"
    # Procura em tags comuns de título/subtítulo
    candidates = soup.find_all(['span', 'h1', 'h2', 'p'], string=re.compile(r'(resultado|anúncio|oferta)', re.IGNORECASE))
    
    for tag in candidates:
        text = tag.get_text().strip()
        # Procura padrão numérico seguido de palavra chave
        match = re.search(r'(\d[\d\.]*)\s+(resultado|anúncio|oferta)', text, re.IGNORECASE)
        if match:
            num = extract_number(match.group(1))
            if num > 0: return num
            
    # Estratégia B: Texto "1 - 50 de X" (Paginação)
    pag_text = soup.find(string=re.compile(r'de\s+(\d[\d\.]*)', re.IGNORECASE))
    if pag_text:
        match = re.search(r'de\s+(\d[\d\.]*)', pag_text)
        if match:
            return extract_number(match.group(1))
            
    return 0

def try_extract_meta_total(soup):
    """Tenta encontrar o número nas meta tags ou título"""
    # Exemplo title: "Carros em SP ... - 12.394 ofertas | OLX"
    if soup.title:
        match = re.search(r'-\s*(\d[\d\.]*)\s+oferta', soup.title.string, re.IGNORECASE)
        if match: return extract_number(match.group(1))
        
    # Exemplo meta description
    meta = soup.find('meta', attrs={'name': 'description'})
    if meta and meta.get('content'):
        match = re.search(r'(\d[\d\.]*)\s+oferta', meta['content'], re.IGNORECASE)
        if match: return extract_number(match.group(1))
        
    return 0

def parse_data(content):
    """Extrai links e tenta achar o total usando 4 estratégias"""
    soup = BeautifulSoup(content, 'lxml')
    links = set()
    total_ads_found = 0
    
    # --- 1. Extração de Links (Prioridade) ---
    # Tenta via JSON primeiro (mais limpo)
    next_data = soup.select_one('#__NEXT_DATA__')
    json_success = False
    
    if next_data:
        try:
            data = json.loads(next_data.string)
            props = data.get('props', {}).get('pageProps', {})
            
            # Tenta pegar total do JSON
            total_ads_found = find_deep_total(props) or 0
            
            # Pega links do JSON
            ads_list = []
            if 'ads' in props:
                if isinstance(props['ads'], list): ads_list = props['ads']
                elif isinstance(props['ads'], dict): ads_list = props['ads'].get('data', [])
            elif 'req' in props and 'ads' in props['req']:
                 ads_list = props['req']['ads']

            for ad in ads_list:
                url = ad.get('url')
                if url and 'olx.com.br' in url:
                    links.add(url)
                    json_success = True
        except Exception:
            pass

    # Fallback de links via HTML (se JSON falhar ou vazio)
    if not links:
        # Busca links principais com padrão de anúncio
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Filtros para evitar links de rodapé/menu
            if 'olx.com.br' in href and ('autos-e-pecas' in href or 'carros' in href):
                # Anúncios geralmente terminam com ID numérico longo
                if re.search(r'-\d{8,}$', href):
                    links.add(href.split('?')[0])
    
    # --- 2. Detecção de Total (Se JSON falhou ou retornou 0) ---
    if total_ads_found == 0:
        # Tentativa 2: HTML Visual (Texto que o usuário vê)
        total_ads_found = try_extract_visible_total(soup)
        if total_ads_found > 0:
            logger.debug(f"Total encontrado via Visual DOM: {total_ads_found}")

    if total_ads_found == 0:
        # Tentativa 3: Meta Tags (SEO costuma ter a contagem)
        total_ads_found = try_extract_meta_total(soup)
        if total_ads_found > 0:
            logger.debug(f"Total encontrado via Meta Tags: {total_ads_found}")

    if total_ads_found == 0:
        # Tentativa 4: Regex Bruto no Código Fonte (Último recurso)
        try:
            html_text = content.decode('utf-8', errors='ignore')
            patterns = [
                r'"totalAdCount":\s*(\d+)',
                r'"totalCount":\s*(\d+)',
                r'"total":\s*(\d+)',
                r'totalAds\s*=\s*(\d+)'
            ]
            for pattern in patterns:
                match = re.search(pattern, html_text)
                if match:
                    val = int(match.group(1))
                    if val > 5: # Filtra falsos positivos
                        total_ads_found = val
                        logger.debug(f"Total encontrado via Regex Bruto: {val}")
                        break
        except Exception:
            pass
                
    return list(links), total_ads_found

def fetch_page(session, url, page_num):
    try:
        # Delay leve para evitar 429
        time.sleep(0.1 + (0.05 * (page_num % 3))) 
        resp = session.get(url, impersonate=BROWSER_IMPERSONATE, headers=HEADERS, timeout=15)
        
        if resp.status_code == 200:
            links, _ = parse_data(resp.content)
            return links
        return []
    except Exception:
        return []

def main():
    parser = argparse.ArgumentParser(description="Coletor Turbo OLX - V6")
    parser.add_argument('url', nargs='?', help="URL inicial")
    parser.add_argument('-p', '--pages', type=int, default=0, help="Forçar páginas")
    args = parser.parse_args()
    
    start_url = args.url
    if not start_url:
        print("="*60)
        print("🏎️  COLETOR OLX TURBO - V6 (MULTI-LAYER DETECTION)")
        print("="*60)
        start_url = input("URL da busca: ").strip()

    if not start_url: return

    logger.info("="*60)
    logger.info("🚀 Iniciando Coletor V6")
    logger.info(f"📍 URL: {start_url}")
    logger.info("="*60)

    start_time = time.time()
    all_links = set()
    session = cffi_requests.Session()

    logger.info("🔎 Analisando página 1 e buscando total...")
    try:
        resp = session.get(start_url, impersonate=BROWSER_IMPERSONATE, headers=HEADERS, timeout=20)
    except Exception as e:
        logger.error(f"Erro conexao: {e}")
        return

    if resp.status_code != 200:
        logger.error(f"Erro status: {resp.status_code}")
        # Se falhar a primeira, nem continua
        return

    page1_links, total_ads = parse_data(resp.content)
    all_links.update(page1_links)
    
    logger.info(f"✅ Página 1 processada: {len(page1_links)} links encontrados.")

    # --- LÓGICA DE DECISÃO V6 ---
    total_pages = 1
    
    if args.pages > 0:
        total_pages = args.pages
        logger.info(f"⚙️ Manual: {total_pages} páginas forçadas pelo usuário.")
    elif total_ads > 0:
        # OLX exibe aprox 50 por página
        total_pages = math.ceil(total_ads / 50)
        # Limite de segurança da OLX (geralmente param de servir resultados na pág 100)
        if total_pages > 100: total_pages = 100 
        logger.info(f"📊 Automático: {total_ads} anúncios detectados -> {total_pages} páginas.")
    else:
        total_pages = SAFE_FALLBACK_PAGES
        logger.warning(f"⚠️ Total ainda indetectável. Usando Fallback Seguro ({total_pages} páginas).")
        logger.warning("   -> Dica: Verifique se a URL já não é uma busca vazia ou com erro.")

    # Loop principal
    if total_pages > 1:
        pages_to_fetch = range(2, total_pages + 1)
        logger.info(f"🚀 Baixando {len(pages_to_fetch)} páginas restantes...")
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_page = {executor.submit(fetch_page, session, get_page_url(start_url, p), p): p for p in pages_to_fetch}
            
            processed = 0
            for future in as_completed(future_to_page):
                processed += 1
                new_links = future.result()
                if new_links:
                    all_links.update(new_links)
                
                # Feedback visual na mesma linha
                sys.stdout.write(f"\r⏳ {processed}/{len(pages_to_fetch)} pág | Links Coletados: {len(all_links)}")
                sys.stdout.flush()

    elapsed = time.time() - start_time
    print("\n")
    logger.info("="*60)
    logger.info(f"🏁 FIM DO PROCESSO")
    logger.info(f"🔗 TOTAL FINAL: {len(all_links)} links únicos")
    logger.info(f"⏱️  Tempo: {elapsed:.2f}s")
    logger.info("="*60)

    # Salva ordenado
    with open("links_olx_final.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(all_links)))
    logger.info("💾 Arquivo salvo: links_olx_final.txt")

if __name__ == '__main__':
    main()