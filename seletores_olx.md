# Seletores Oficiais do OLX - Referência

Este arquivo contém os seletores oficiais do OLX extraídos do código JavaScript do site, organizados por categoria.

## 📋 Dados do Anúncio

### Nome do Vendedor
- **Seletor Principal**: `.ad__sc-ypp2u2-12` (children[0])
- **Seletor Alternativo 1**: `div[data-testid="account-box"]`
- **Observações**: Primeiro filho do elemento, texto dividido por `\n`

### Modelo do Veículo
- **Seletor Principal**: `a.ad__sc-2h9gkk-3.lkkHCr` (extraído da URL)
- **Observações**: O modelo está na URL do link, após a marca. Padrão: `.../autos-e-pecas/carros-vans-e-utilitarios/MARCA/MODELO/...`. Exemplo: `https://www.olx.com.br/autos-e-pecas/carros-vans-e-utilitarios/ford/ecosport/...` → modelo: "ecosport"

### Versão do Veículo
- **Seletor Principal**: `h1`
- **Seletor Alternativo 1**: `.ad__sc-wuor06-0.hfcCRQ span.olx-color-neutral-120`
- **Observações**: Versão completa do veículo extraída do título H1 (ex: "Ford Se 1.6 16v Flex 5p Aut.")

### Ano do Veículo
- **Seletor Principal**: `.ad__sc-wuor06-0.hfcCRQ span.olx-color-neutral-120`
- **Observações**: Busca por texto "ANO"

### Preço do Veículo
- **Seletor Principal**: `span.typo-title-large`
- **Seletor Alternativo 1**: `h2.olx-text.olx-text--title-large.olx-text--block.ad__sc-1leoitd-0.bJHaGt`
- **Seletor Alternativo 2**: `h2.ad__sc-1leoitd-0`
- **Observações**: O seletor `span.typo-title-large` contém o preço formatado (ex: "R$ 37.000")

### Valor do Anúncio
- **Seletor Principal**: `.ad__sc-q5xder-1.hoJpM .olx-d-flex.olx-fd-column`
- **Observações**: Remove "R$ " do texto

### Preço FIPE (Container e Valor)
- **Container Principal**: `div.LkJa2kno`
- **Label**: `span[data-variant="overline"]` (dentro do container, contém "preço fipe" ou "PREÇO FIPE")
- **Valor**: `span[data-ds-component="DS-Text"].olx-text.olx-text--body-medium.olx-text--block.olx-text--bold` (dentro do container)
- **Observações**: Busca containers com classe `LkJa2kno`, identifica pelo label "FIPE" e extrai o preço do mesmo container

### Preço Médio OLX (Container e Valor)
- **Container Principal**: `div.LkJa2kno`
- **Label**: `span[data-variant="overline"]` (dentro do container, contém "Preço Médio OLX" ou "PREÇO MÉDIO OLX")
- **Valor**: `span[data-ds-component="DS-Text"].olx-text.olx-text--body-medium.olx-text--block.olx-text--bold` (dentro do container)
- **Observações**: Busca containers com classe `LkJa2kno`, identifica pelo label "MÉDIO OLX" e extrai o preço do mesmo container

### Preço Médio OLX (Label)
- **Seletor Principal**: `.LkJa2kno` (children[1])
- **Observações**: Busca texto "PREÇO MÉDIO OLX"

### Número de Telefone (Principal)
- **Seletor Principal**: `span.ad__sc-14mcmsd-7.hORwFH`
- **Seletor Alternativo 1**: `span.typo-body-large.font-light.ad__sc-14mcmsd-7`
- **Seletor Alternativo 2**: `span.typo-body-large.text-neutral-120`
- **Seletor Alternativo 3**: `.ad__sc-14mcmsd-3.jojxFh`
- **Observações**: Regex: `\(\d{2}\)\s*\d{4,5}-?\d{4}`. O telefone aparece no elemento com classes `ad__sc-14mcmsd-7 hORwFH` dentro de um container com ícone de telefone.

### Número de Telefone (Alternativo 4)
- **Seletor Principal**: `span[data-ds-component="DS-Text"]`
- **Observações**: Regex para telefone

### Número de Telefone (Alternativo 5)
- **Seletor Principal**: `.olx-text--caption`
- **Observações**: Regex para telefone

### Número de Telefone (Alternativo 6)
- **Seletor Principal**: `span`
- **Observações**: Filtra por regex telefone

### Quilometragem
- **Seletor Principal**: `span.ad__sc-hj0yqs-0.ekhFnR`
- **Observações**: Quilometragem do veículo em km (ex: "89000"). O elemento pode conter divs internos, extrair apenas o texto numérico principal.

### Bairro/Localização
- **Seletor Principal**: `span.typo-body-medium.font-semibold`
- **Observações**: Bairro ou localização do anúncio (ex: "Parque Residencial Villa dos Inglezes"). Pode haver múltiplos elementos com essa classe, filtrar por contexto (não ser link, não ser marca/ano).

### Cidade/Estado/CEP
- **Seletor Principal**: `span.typo-body-small.font-semibold.text-neutral-110`
- **Observações**: Localização completa (ex: "Sorocaba, SP, 18051864")

### Ano do Veículo (Atualizado)
- **Seletor Principal**: `.ad__sc-wuor06-0.hfcCRQ span.olx-color-neutral-120`
- **Seletor Alternativo 1**: `a.ad__sc-2h9gkk-3.lkkHCr` (filtro: texto numérico de 4 dígitos)
- **Observações**: Busca por texto "ANO" ou link com texto numérico de 4 dígitos (regex `^\d{4}$`)

### Marca do Veículo
- **Seletor Principal**: `a.ad__sc-2h9gkk-3.lkkHCr` (filtro: texto de marca)
- **Observações**: Marca do veículo (ex: "Volkswagen", "Fiat"). Diferenciar de ano verificando se o texto não é numérico de 4 dígitos.

### Preço Médio OLX (Valor) - Atualizado
- **Seletor Principal**: `span[data-ds-component="DS-Text"].olx-text.olx-text--body-medium.olx-text--block.olx-text--bold`
- **Seletor Alternativo 1**: `.LkJa2kno` (children[0])
- **Observações**: Preço médio do veículo no OLX. Mapeia valores, busca label "PREÇO MÉDIO OLX" ou usa o seletor específico.

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
Última atualização: 2025-12-06
Fonte: Seletores extraídos do código JavaScript oficial do OLX

**Mudanças recentes:**
- 2025-12-06: Atualizado seletor de preço para `span.typo-title-large` (seletor principal)
- 2025-12-06: Adicionados novos seletores:
  - Telefone: `span.typo-body-large.text-neutral-120` (seletor principal atualizado)
  - Quilometragem: `span.ad__sc-hj0yqs-0.ekhFnR`
  - Bairro: `span.typo-body-medium.font-semibold`
  - Cidade/Estado/CEP: `span.typo-body-small.font-semibold.text-neutral-110`
  - Ano do Veículo: `a.ad__sc-2h9gkk-3.lkkHCr` (seletor alternativo adicionado)
  - Marca do Veículo: `a.ad__sc-2h9gkk-3.lkkHCr` (novo campo)
  - Modelo do Veículo: `a.ad__sc-2h9gkk-3.lkkHCr` (extraído da URL do link)
  - Versão do Veículo: `h1` (separado do modelo, extraído do título)
  - Preço Médio OLX: `span[data-ds-component="DS-Text"].olx-text.olx-text--body-medium.olx-text--block.olx-text--bold` (seletor específico adicionado)

**Importante**: Os seletores podem mudar se o OLX atualizar sua estrutura HTML. Sempre teste após atualizações do site.


