---
name: Corrigir extração nome vendedor
overview: "Aplicar limpeza cirúrgica nas funções de extração do nome do vendedor para remover texto concatenado (ex: \"HenriqueÚltimo acesso\") usando função _clean_name e separator no get_text."
todos:
  - id: setup-dependencies
    content: Criar requirements.txt com requests, beautifulsoup4, lxml e selenium (opcional)
    status: completed
  - id: create-main-script
    content: Criar main.py com função CLI que recebe URL e configura headers HTTP personalizados (User-Agent, Accept, Referer)
    status: completed
    dependencies:
      - setup-dependencies
  - id: implement-extraction
    content: Implementar funções de extração para nome do vendedor, modelo, valor e preço FIPE usando BeautifulSoup, com tratamento opcional para FIPE
    status: completed
    dependencies:
      - create-main-script
  - id: add-fallback-logic
    content: Adicionar lógica de fallback que detecta dados ausentes, registra avisos e sugere Selenium se conteúdo dinâmico for detectado
    status: completed
    dependencies:
      - implement-extraction
  - id: add-error-handling
    content: Adicionar tratamento robusto de erros para URLs inválidas, páginas não encontradas e dados ausentes
    status: completed
    dependencies:
      - implement-extraction
  - id: test-scraping
    content: Testar o scraper com a URL fornecida, ajustar seletores CSS e validar extração de todos os campos
    status: completed
    dependencies:
      - add-fallback-logic
      - add-error-handling
---

# Plano: Corrigir Extração do Nome do Vendedor

## Problema Identificado

O nome do vendedor está sendo capturado com texto concatenado (ex: "HenriqueÚltimo acesso") porque:

- HTML tem elementos separados `<span>Henrique</span><span>Último acesso...</span>` que são lidos juntos
- Não há limpeza específica para remover frases administrativas do OLX
- Falta uso de separator no get_text() para separar elementos grudados

## Solução Proposta

### 1. Atualizar extract_vendor_name_selenium

**Arquivo**: `main.py` (linhas ~161-230)

**Mudanças**:

- Adicionar função interna `_clean_name()` que remove cirurgicamente:
- "Último acesso" e tudo depois (case-insensitive)
- "Conta verificada"
- "Na OLX desde"
- Quebras de linha e espaços extras
- Melhorar seletores: usar `.ad__sc-ypp2u2-12, div[data-testid="account-box"]` em um único seletor
- Adicionar XPaths específicos para buscar spans dentro do box de perfil
- Aplicar `_clean_name()` em todos os resultados antes de retornar

### 2. Atualizar extract_vendor_name (BeautifulSoup)

**Arquivo**: `main.py` (linhas ~232-296)

**Mudanças**:

- Adicionar função interna `_clean_name()` (mesma lógica do Selenium)
- Usar `separator=' | '` no `get_text()` para separar elementos grudados
- Dividir por `|` e pegar apenas a primeira parte (nome)
- Melhorar regex patterns para capturar nome antes de frases administrativas
- Aplicar filtro extra para evitar palavras de menu

## Estrutura das Funções

### extract_vendor_name_selenium

1. Função interna `_clean_name(raw_name)` para limpeza
2. Tentativa 1: Seletores oficiais com limpeza
3. Tentativa 2: XPaths específicos para spans dentro do box
4. Fallback: chama `extract_vendor_name(soup)`

### extract_vendor_name

1. Função interna `_clean_name(raw_name)` para limpeza
2. Tentativa 1: Busca estrutural com `separator=' | '`
3. Tentativa 2: Regex refinado no texto da página
4. Retorna None se não encontrar

## Padrões de Limpeza

A função `_clean_name` remove:

- `(?i)último\s*acesso.*` - Remove "Último acesso" e tudo depois
- `(?i)conta\s*verificada.*` - Remove "Conta verificada"
- `(?i)na\s*olx\s*desde.*` - Remove "Na OLX desde"
-  `- .*` - Remove sufixos com hífen
- `split('\n')[0]` - Pega apenas primeira linha
- `strip()` - Remove espaços extras

## Arquivos a Modificar

- `main.py`: Substituir completamente as funções `extract_vendor_name_selenium` e `extract_vendor_name`

## Resultado Esperado

Após as correções, o nome do vendedor deve ser extraído limpo, sem frases administrativas concatenadas, mesmo quando o HTML tem elementos grudados.