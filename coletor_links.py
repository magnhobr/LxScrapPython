#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coletor de Links OLX - Extrai URLs de anúncios de páginas de busca (Via JSON/NextData)
Autor: Gemini & User
"""

import sys
import re
import argparse
import logging
import time
import json
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# Verifica dependências
try:
    from curl_cffi import requests as cffi_requests
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ ERRO: Instale: pip install curl-cffi beautifulsoup4 lxml")
    sys.exit(1)

# --- Configuração ---
BROWSER_IMPERSONATE = "chrome124"
MAX_PAGES_DEFAULT = 100

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - [%(levelname)s] - %(message)s',
        datefmt='%H:%M:%S',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger("OLX_LINKS")

logger = setup_logging()

def get_next_page_url(base_url, current_page):
    """Gera a URL para a próxima página mantendo os filtros"""
    parsed = urlparse(base_url)
    query_params = parse_qs(parsed.query)
    
    # Atualiza ou adiciona o parâmetro 'o' (offset/página)
    query_params['o'] = [str(current_page)]
    
    new_query = urlencode(query_params, doseq=True)
    new_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))
    return new_url

def extract_from_json(soup):
    """Tenta extrair links do JSON __NEXT_DATA__"""
    links = []
    
    # Tenta __NEXT_DATA__
    next_data = soup.select_one('#__NEXT_DATA__')
    if next_data:
        try:
            data = json.loads(next_data.string)
            # Caminho comum: props -> pageProps -> ads
            ads = data.get('props', {}).get('pageProps', {}).get('ads', [])
            
            for ad in ads:
                # Pode ser um anúncio real ou publicidade/outros itens
                url = ad.get('url')
                if url and 'olx.com.br' in url:
                    links.append(url)
                    
            return links
        except Exception as e:
            logger.debug(f"Erro ao parsear Next Data: {e}")

    return links

def extract_ad_links_recursive(start_url: str, max_pages: int = MAX_PAGES_DEFAULT):
    all_links = []
    current_page = 1
    
    # Verifica se a URL inicial já tem página (param 'o')
    parsed = urlparse(start_url)
    qs = parse_qs(parsed.query)
    if 'o' in qs:
        current_page = int(qs['o'][0])
        logger.info(f"Começando da página {current_page}")

    while current_page <= max_pages:
        url_atual = get_next_page_url(start_url, current_page) if current_page > 1 else start_url
        logger.info(f"⚡ Coletando página {current_page}: {url_atual[:60]}...")
        
        try:
            response = cffi_requests.get(
                url_atual, 
                impersonate=BROWSER_IMPERSONATE, 
                headers={
                    "Referer": "https://www.google.com/",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                },
                timeout=20
            )

            if response.status_code != 200:
                logger.error(f"❌ Erro HTTP: {response.status_code} na página {current_page}")
                break

            soup = BeautifulSoup(response.content, 'lxml')
            page_links = []
            
            # --- ESTRATÉGIA 1: JSON (Ultra Rápido) ---
            json_links = extract_from_json(soup)
            if json_links:
                logger.info(f"🚀 Extraídos {len(json_links)} links via JSON")
                page_links = json_links
            
            # --- ESTRATÉGIA 2: HTML (Fallback) ---
            if not page_links:
                logger.info("⚠️ JSON falhou/vazio, usando fallback HTML...")
                anchors = soup.find_all('a', href=True)
                for link in anchors:
                    href = link['href']
                    if href.startswith('/'): href = "https://www.olx.com.br" + href
                    if re.search(r'-\d{8,}$', href) and ('autos-e-pecas' in href or 'carros' in href):
                        href_clean = href.split('?')[0]
                        if href_clean not in page_links:
                            page_links.append(href_clean)

            # Filtra duplicatas globais
            new_links = [l for l in page_links if l not in all_links]
            
            if not new_links and not page_links:
                logger.warning(f"⚠️ Nenhum anúncio encontrado na página {current_page}. Encerrando.")
                break
                
            all_links.extend(new_links)
            logger.info(f"✅ +{len(new_links)} novos links (Total: {len(all_links)})")

            # --- Verificação de Próxima Página ---
            # 1. Tenta achar botão "Próxima" (Seletor específico e Texto)
            # 2. Se não achar botão, mas encontrou links, CONTINUA (Assume que tem mais)
            
            next_btn = soup.find('a', string="Próxima página")
            if not next_btn:
                next_btn = soup.find('a', string=re.compile(r'Próxima página', re.IGNORECASE))
            if not next_btn:
                potential_btns = soup.find_all('a', class_='olx-core-button')
                for btn in potential_btns:
                    if 'Próxima' in btn.get_text():
                        next_btn = btn
                        break

            if next_btn:
                logger.info("➡️ Botão 'Próxima' detectado.")
            else:
                if len(page_links) >= 10:
                    logger.info("➡️ Botão 'Próxima' não visto, mas página tem conteúdo. Continuando...")
                else:
                    logger.info("⏹️ Fim da paginação (sem botão e poucos resultados).")
                    break
                
            current_page += 1
            # Pausa ligeiramente menor pois JSON é mais leve de processar, mas respeita servidor
            time.sleep(1.0)

        except Exception as e:
            logger.error(f"Erro na página {current_page}: {e}")
            break

    return all_links

def main():
    parser = argparse.ArgumentParser(description="Coletor de Links OLX (JSON/Fast)")
    parser.add_argument('url', nargs='?', help="URL da primeira página da busca")
    parser.add_argument('--max', type=int, default=MAX_PAGES_DEFAULT, help="Máximo de páginas a percorrer")
    args = parser.parse_args()
    
    url = args.url
    if not url:
        print("="*50)
        print("🔗 COLETOR DE LINKS OLX (FAST JSON)")
        print("="*50)
        url = input("URL da busca: ").strip()

    if not url: return

    start = time.time()
    links = extract_ad_links_recursive(url, args.max)
    
    print("\n" + "="*50)
    print(f"🔗 TOTAL DE LINKS ENCONTRADOS: {len(links)}")
    print("="*50)
    
    for i, link in enumerate(links, 1):
        print(f"{str(i).zfill(3)}. {link}")
        
    print("="*50)
    print(f"⏱️ Tempo: {time.time() - start:.4f}s")
    
    with open("links_olx.txt", "w", encoding="utf-8") as f:
        for link in links:
            f.write(link + "\n")
    print(f"💾 Links salvos em 'links_olx.txt'")

if __name__ == '__main__':
    main()
