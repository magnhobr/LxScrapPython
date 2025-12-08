# Seletores Oficiais do OLX - Referência

Este arquivo contém os seletores oficiais do OLX extraídos do código JavaScript do site, organizados por categoria.

## 📋 Dados do Anúncio

### Nome do Vendedor
- **Seletor Principal**: `.ad__sc-ypp2u2-12` (children[0])
- **Seletor Alternativo 1**: `div[data-testid="account-box"]`
- **Observações**: Primeiro filho do elemento, texto dividido por `\n`

### Descrição/Modelo do Veículo
- **Seletor Principal**: `.ad__sc-wuor06-0.hfcCRQ span.olx-color-neutral-120`
- **Seletor Alternativo 1**: `h1`
- **Observações**: Busca por texto "MODELO", fallback para título h1

### Ano do Veículo
- **Seletor Principal**: `.ad__sc-wuor06-0.hfcCRQ span.olx-color-neutral-120`
- **Observações**: Busca por texto "ANO"

### Preço do Veículo
- **Seletor Principal**: `h2.olx-text.olx-text--title-large.olx-text--block.ad__sc-1leoitd-0.bJHaGt`
- **Seletor Alternativo 1**: `h2.ad__sc-1leoitd-0`

### Valor do Anúncio
- **Seletor Principal**: `.ad__sc-q5xder-1.hoJpM .olx-d-flex.olx-fd-column`
- **Observações**: Remove "R$ " do texto

### Preço FIPE (Valor)
- **Seletor Principal**: `.LkJa2kno` (children[0])
- **Observações**: Mapeia valores, busca label "PREÇO FIPE"

### Preço FIPE (Label)
- **Seletor Principal**: `.LkJa2kno` (children[1])
- **Observações**: Busca texto "PREÇO FIPE"

### Preço Médio OLX (Valor)
- **Seletor Principal**: `.LkJa2kno` (children[0])
- **Observações**: Mapeia valores, busca label "PREÇO MÉDIO OLX"

### Preço Médio OLX (Label)
- **Seletor Principal**: `.LkJa2kno` (children[1])
- **Observações**: Busca texto "PREÇO MÉDIO OLX"

### Número de Telefone (Principal)
- **Seletor Principal**: `.ad__sc-14mcmsd-3.jojxFh`
- **Observações**: Regex: `\(\d{2}\)\s*\d{4,5}-?\d{4}`

### Número de Telefone (Alternativo 1)
- **Seletor Principal**: `span[data-ds-component="DS-Text"]`
- **Observações**: Regex para telefone

### Número de Telefone (Alternativo 2)
- **Seletor Principal**: `.olx-text--caption`
- **Observações**: Regex para telefone

### Número de Telefone (Alternativo 3)
- **Seletor Principal**: `span`
- **Observações**: Filtra por regex telefone

### Botão Ver números
- **Seletor Principal**: `span[data-ds-component="DS-Text"].olx-text.olx-text--caption.olx-text--block.olx-text--semibold.olx-color-secondary-110`
- **Seletor Alternativo 1**: `span` (filtro texto)
- **Observações**: Texto "Ver números"

---

## 📋 Listagem

### Container de Anúncios
- **Seletor Principal**: `section.olx-adcard.olx-adcard__horizontal`
- **Observações**: Todos os anúncios da página

### Título do Anúncio
- **Seletor Principal**: `h2.olx-adcard__title`
- **Observações**: Dentro do elemento anúncio

### Preço do Anúncio
- **Seletor Principal**: `h3.olx-adcard__price`
- **Observações**: Dentro do elemento anúncio

### Link do Anúncio
- **Seletor Principal**: `a.olx-adcard__link`
- **Observações**: Dentro do elemento anúncio

### Imagem do Anúncio
- **Seletor Principal**: `img`
- **Observações**: Primeira imagem encontrada

### Detalhes do Anúncio
- **Seletor Principal**: `.olx-adcard__detail`
- **Observações**: Múltiplos elementos

### Link do Anúncio (Alternativo)
- **Seletor Principal**: `[data-testid="adcard-link"]`

---

## 💬 Chat OLX

### Item da Lista de Chat
- **Seletor Principal**: `[data-testid="chat-list-item"]`
- **Observações**: Item individual do chat

### Remetente da Mensagem
- **Seletor Principal**: `.sc-lgpSej`
- **Observações**: Dentro do item de chat

### Produto do Chat
- **Seletor Principal**: `.sc-dYwGCk span`
- **Observações**: Dentro do item de chat

### Mensagem do Chat
- **Seletor Principal**: `.sc-eqYatC span`
- **Observações**: Dentro do item de chat

### Horário da Mensagem
- **Seletor Principal**: `.sc-kcLKEh span`
- **Observações**: Dentro do item de chat

### Indicador de Mensagem Nova
- **Seletor Principal**: `.sc-jwTyAe`
- **Seletor Alternativo 1**: `.sc-jwTyAe.evfDbZ`
- **Observações**: Ponto laranja

### Container do Chat
- **Seletor Principal**: `.sc-bRKDuR`

### Campo de Input de Mensagem
- **Seletor Principal**: `textarea#input-text-message`
- **Seletor Alternativo 1**: `[data-testid="chat-input"]`

### Botão de Envio (SVG Path 1)
- **Seletor Principal**: `path[d*="M2.04229758,14.0134155"]`
- **Observações**: Busca pelo SVG path

### Botão de Envio (SVG Path 2)
- **Seletor Principal**: `path[d*="L12.5770477,12.499828"]`
- **Observações**: Busca pelo SVG path

### Botão de Envio (SVG Path 3)
- **Seletor Principal**: `path[d*="L20.8707211,10.285034"]`
- **Observações**: Busca pelo SVG path

### Botão de Envio (Alternativo 1)
- **Seletor Principal**: `[data-testid="send-button"]`

### Botão de Envio (Alternativo 2)
- **Seletor Principal**: `button[type="submit"]`

### Botão Mais Opções
- **Seletor Principal**: `button[aria-label="Mais Opções"]`

### Opção Excluir conversa
- **Seletor Principal**: `li` (filtro texto)
- **Observações**: Texto "Excluir conversa"

### Botão Confirmar Exclusão
- **Seletor Principal**: `button.olx-core-button--danger`
- **Seletor Alternativo 1**: `button` (filtro texto)
- **Observações**: Texto "Excluir conversa"

### Botão Aceita oferta? (Principal)
- **Seletor Principal**: `button.olx-core-button` (filtro texto)
- **Observações**: Texto "aceita oferta?"

### Botão Aceita oferta? (Alternativo 1)
- **Seletor Principal**: `button` (filtro texto)
- **Observações**: Texto inclui "aceita oferta"

### Botão Aceita oferta? (Alternativo 2)
- **Seletor Principal**: `button[data-testid*="accept"]`

### Botão Aceita oferta? (Alternativo 3)
- **Seletor Principal**: `button[aria-label*="aceita"]`

### Botão Aceita oferta? (Alternativo 4)
- **Seletor Principal**: `button[aria-label*="Aceita"]`

### Botão Chat OLX
- **Seletor Principal**: `#price-box-button-chat`
- **Seletor Alternativo 1**: `button[action="chat"]`

### Mensagens Já Enviadas
- **Seletor Principal**: `.sc-jJkQYJ.sc-kOnlKp.krvZiw`

### Badge de Notificação
- **Seletor Principal**: `span[class*="badge"], [class*="notification"], [class*="count"]`

---

## 📄 Paginação

### Botão Próxima Página (Principal)
- **Seletor Principal**: `a.olx-core-button--link` (filtro texto)
- **Observações**: Texto "Próxima página"

### Botão Próxima Página (Alternativo 1)
- **Seletor Principal**: `.olx-core-button--link` (filtro texto)
- **Observações**: Texto "Próxima página"

### Botão Próxima Página (Número)
- **Seletor Principal**: `a.olx-core-button--link` (filtro número)
- **Observações**: Número da próxima página

### Botão Paginação
- **Seletor Principal**: `a.Pagination_pageButton__9hd5x`

---

## 📱 WhatsApp

### Botão de Ação WhatsApp
- **Seletor Principal**: `#action-button`
- **Observações**: Redirecionamento API

### Botão Enviar WhatsApp
- **Seletor Principal**: `[data-icon=send]`

### Mensagem Inválida WhatsApp
- **Seletor Principal**: `div.x12lqup9.x1o1kx08`

### Mensagens WhatsApp
- **Seletor Principal**: `span._ao3e.selectable-text.copyable-text`

---

## 🔧 Outros

### Container Principal
- **Seletor Principal**: `.container`

### Botão Visualização em Grade
- **Seletor Principal**: `[aria-label='Ativar visualização em grade']`

### Título Grande
- **Seletor Principal**: `span.olx-text.olx-text--title-large.olx-text--block`

---

## 📝 Notas Importantes

1. **Seletores CSS**: Use `driver.find_element(By.CSS_SELECTOR, 'seletor')` no Selenium
2. **Seletores XPath**: Use `driver.find_element(By.XPATH, 'xpath')` no Selenium
3. **BeautifulSoup**: Use `soup.select('seletor')` ou `soup.select_one('seletor')`
4. **Children**: Para acessar children[0], use `element.find_element(By.XPATH, './child::*[1]')` ou `element.find(True)` no BeautifulSoup
5. **Filtro texto**: Significa buscar elemento que contenha determinado texto
6. **Regex**: Alguns campos requerem regex para extrair dados específicos

---

## 🔄 Atualizações

Este arquivo foi criado em: 2025-12-05
Fonte: Seletores extraídos do código JavaScript oficial do OLX

**Importante**: Os seletores podem mudar se o OLX atualizar sua estrutura HTML. Sempre teste após atualizações do site.

