#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper OLX - Turbo V5 (Deep JSON Extraction)
Autor: Gemini & User
"""

import sys
import re
import json
import html
import argparse
import logging
import time
import os
from typing import Dict, Optional

# Verifica dependências
try:
    from curl_cffi import requests as cffi_requests
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ ERRO: Instale: pip install curl-cffi beautifulsoup4 lxml")
    sys.exit(1)

# --- Configuração ---
BROWSER_IMPERSONATE = "chrome124"

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - [%(levelname)s] - %(message)s',
        datefmt='%H:%M:%S',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger("OLX_TURBO")

logger = setup_logging()

def clean_text(text):
    if not text: return None
    text = re.sub(r'[\n\r\t]', ' ', str(text))
    return re.sub(r'\s+', ' ', text).strip()

def get_digits(text):
    if not text: return None
    match = re.search(r'\d+', str(text))
    return match.group(0) if match else None

def format_currency(value):
    """Converte 99900 em R$ 99.900"""
    try:
        if not value: return None
        if isinstance(value, str) and 'R$' in value: return value
        val_float = float(value)
        return f"R$ {val_float:,.0f}".replace(',', '.')
    except:
        return str(value)

def extract_from_json(ad_data: Dict, data_dict: Dict):
    """Extrai dados do objeto JSON do anúncio de forma resiliente"""
    
    # 1. Dados Básicos (Raiz)
    data_dict['id_anuncio'] = str(ad_data.get('listId', ad_data.get('adId', data_dict['id_anuncio'])))
    data_dict['versao_veiculo'] = ad_data.get('subject', ad_data.get('title', ''))
    data_dict['valor_anuncio'] = ad_data.get('priceValue', ad_data.get('price', ''))
    
    # Se preço vier apenas numérico, formata
    if data_dict['valor_anuncio'] and 'R$' not in str(data_dict['valor_anuncio']):
         data_dict['valor_anuncio'] = format_currency(data_dict['valor_anuncio'])

    # 2. Vendedor
    user = ad_data.get('user', {})
    data_dict['nome_vendedor'] = user.get('name', '')

    # 3. Varredura de Propriedades (Lista de props)
    # Transforma lista [{'name': 'mileage', 'value': '1000'}] em dict {'mileage': '1000'}
    properties = {}
    
    # Tenta pegar propriedades da lista 'properties'
    if 'properties' in ad_data and isinstance(ad_data['properties'], list):
        for p in ad_data['properties']:
            # Mapeia pelo 'name' (chave interna)
            if p.get('name'):
                properties[p.get('name')] = p.get('value')
            # Mapeia também pelo 'label' para garantir (ex: 'Marca')
            if p.get('label'):
                properties[p.get('label')] = p.get('value')

    # Dados da raiz têm prioridade, depois properties
    data_dict['quilometragem'] = str(ad_data.get('mileage', properties.get('mileage', '')))
    data_dict['ano_veiculo'] = str(ad_data.get('regdate', properties.get('regdate', '')))
    data_dict['modelo_veiculo'] = ad_data.get('model', properties.get('vehicle_model', properties.get('Modelo', '')))
    
    # --- MARCA (Lógica Reforçada) ---
    # 1. Tenta raiz 'brand'
    # 2. Tenta raiz 'vehicle_brand'
    # 3. Tenta properties 'vehicle_brand'
    # 4. Tenta properties 'Marca'
    data_dict['marca_veiculo'] = ad_data.get('brand') or \
                                 ad_data.get('vehicle_brand') or \
                                 properties.get('vehicle_brand') or \
                                 properties.get('Marca')

    # 4. Localização
    loc = ad_data.get('location', {})
    data_dict['bairro'] = loc.get('neighbourhood', '')
    if loc.get('municipality'):
        data_dict['cidade_estado_cep'] = f"{loc.get('municipality')} - {loc.get('uf')}, {loc.get('zipcode', '')}"

    # 5. Preços de Referência (FIPE e Médio)
    
    # Tenta estrutura priceStats (Padrão A)
    price_stats = ad_data.get('priceStats', {})
    if price_stats:
        if 'fipePrice' in price_stats: 
            data_dict['preco_fipe'] = format_currency(price_stats['fipePrice'])
        if 'averagePrice' in price_stats: 
            data_dict['preco_medio_olx'] = format_currency(price_stats['averagePrice'])

    # Tenta estrutura abuyFipePrice / abuyPriceRef (Padrão B - Encontrado no seu debug)
    if not data_dict['preco_fipe']:
        fipe_obj = ad_data.get('abuyFipePrice')
        if fipe_obj and 'fipePrice' in fipe_obj:
            data_dict['preco_fipe'] = format_currency(fipe_obj['fipePrice'])
            
    if not data_dict['preco_medio_olx']:
        ref_obj = ad_data.get('abuyPriceRef')
        if ref_obj:
            # Tenta pegar a mediana (p50) ou média se existir
            val = ref_obj.get('price_p50') or ref_obj.get('average_price')
            if val:
                data_dict['preco_medio_olx'] = format_currency(val)

    # 6. Telefone
    phone_obj = ad_data.get('phone', {})
    if phone_obj.get('phone'):
        data_dict['telefone'] = phone_obj.get('phone')


def extract_data_turbo(url: str) -> Dict[str, Optional[str]]:
    data = {
        'id_anuncio': None, 'nome_vendedor': None, 'marca_veiculo': None,
        'modelo_veiculo': None, 'versao_veiculo': None, 'valor_anuncio': None,
        'preco_fipe': None, 'preco_medio_olx': None, 'telefone': None,
        'quilometragem': None, 'bairro': None, 'cidade_estado_cep': None,
        'ano_veiculo': None, 'link': None, 'origem_dados': 'N/A'
    }

    # 1. Regex de URL (Fallback inicial)
    clean_url = url.split('?')[0]
    id_match = re.search(r'-(\d{8,10})', clean_url)
    if id_match:
        data['id_anuncio'] = id_match.group(1)
        data['link'] = f"https://olx.com.br/vi/{data['id_anuncio']}"
    
    # Tenta marca da URL também
    marca_match = re.search(r'/autos-e-pecas/(?:carros-vans-e-utilitarios/)?([^/]+)', clean_url)
    if marca_match and "estado-" not in marca_match.group(1):
        data['marca_veiculo'] = marca_match.group(1).replace('-', ' ').title()

    try:
        logger.info("⚡ Conectando via Curl CFFI...")
        
        response = cffi_requests.get(
            url, 
            impersonate=BROWSER_IMPERSONATE, 
            headers={
                "Referer": "https://www.google.com/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            },
            timeout=15
        )

        if response.status_code != 200:
            logger.error(f"❌ Erro HTTP: {response.status_code}")
            return data

        soup = BeautifulSoup(response.content, 'lxml')
        json_found = False

        # --- ESTRATÉGIA A: INITIAL DATA (Novo Padrão) ---
        initial_data_tag = soup.select_one('#initial-data')
        if initial_data_tag and initial_data_tag.get('data-json'):
            try:
                raw_json = html.unescape(initial_data_tag['data-json'])
                json_content = json.loads(raw_json)
                if 'ad' in json_content:
                    extract_from_json(json_content['ad'], data)
                    data['origem_dados'] = 'JSON (Initial Data)'
                    json_found = True
                    logger.info("✅ Dados extraídos de #initial-data")
            except Exception as e:
                logger.warning(f"Erro parser Initial Data: {e}")

        # --- ESTRATÉGIA B: NEXT DATA (Padrão Antigo) ---
        if not json_found:
            next_data_tag = soup.select_one('#__NEXT_DATA__')
            if next_data_tag:
                try:
                    json_content = json.loads(next_data_tag.string)
                    ad_data = json_content.get('props', {}).get('pageProps', {}).get('ad', {})
                    if ad_data:
                        extract_from_json(ad_data, data)
                        data['origem_dados'] = 'JSON (Next Data)'
                        json_found = True
                        logger.info("✅ Dados extraídos de #__NEXT_DATA__")
                except Exception as e:
                    logger.warning(f"Erro parser Next Data: {e}")

        # --- ESTRATÉGIA C: FALLBACK CSS (Se JSON falhar ou dados faltarem) ---
        if not json_found or not data['marca_veiculo'] or not data['preco_medio_olx']:
            logger.info("⚠️ Complementando com Fallback CSS...")
            if not json_found: data['origem_dados'] = 'HTML/CSS (Fallback)'

            # Marca (Fallback)
            if not data['marca_veiculo']:
                # Tenta link de marca
                marca_elem = soup.find('a', href=re.compile(r'/autos-e-pecas/carros-vans-e-utilitarios/[^/]+/$'))
                if marca_elem:
                    data['marca_veiculo'] = clean_text(marca_elem.get_text())
            
            # Preço (Fallback)
            if not data['valor_anuncio']:
                elem = soup.select_one('span.typo-title-large, h2.ad__sc-1leoitd-0')
                if elem: data['valor_anuncio'] = clean_text(elem.get_text())

            # Preço Médio / FIPE (Fallback CSS)
            if not data['preco_medio_olx'] or not data['preco_fipe']:
                containers = soup.select('div.LkJa2kno')
                for container in containers:
                    txt = container.get_text().upper()
                    val_elem = container.select_one('span.olx-text--bold')
                    if not val_elem: continue
                    val = clean_text(val_elem.get_text())
                    
                    if 'FIPE' in txt and not data['preco_fipe']:
                        data['preco_fipe'] = val
                    elif ('MÉDIO' in txt or 'MEDIO' in txt) and 'OLX' in txt and not data['preco_medio_olx']:
                        data['preco_medio_olx'] = val

        return data

    except Exception as e:
        logger.error(f"Erro Crítico: {e}")
        return data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('url', nargs='?')
    args = parser.parse_args()
    
    url = args.url
    if not url:
        print("="*50)
        print("🚀 OLX SCRAPER TURBO V5 (Deep JSON)")
        print("="*50)
        url = input("URL: ").strip()

    if not url: return

    print(f"\n⏳ Processando: {url[:60]}...")
    start = time.time()
    data = extract_data_turbo(url)
    
    print("\n" + "="*40)
    print(f"FONTE: {data['origem_dados']}")
    print("-" * 40)
    
    # Ordem de exibição
    keys = ['versao_veiculo', 'valor_anuncio', 'quilometragem', 'ano_veiculo', 
            'marca_veiculo', 'modelo_veiculo', 'preco_fipe', 'preco_medio_olx', 
            'nome_vendedor', 'bairro', 'cidade_estado_cep', 'telefone', 'link']
            
    for k in keys:
        label = k.replace('_', ' ').title()
        val = data.get(k)
        print(f"{label.ljust(20)}: {val if val else '---'}")
        
    print("="*40)
    print(f"Tempo: {time.time() - start:.4f}s")

if __name__ == '__main__':
    main()