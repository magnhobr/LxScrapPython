# Scraper OLX - Extração de Dados de Anúncios

Script Python CLI que extrai informações de anúncios do OLX sem abrir navegador.

## 📋 Dados Extraídos

- **Nome do vendedor**
- **Modelo do veículo**
- **Valor do anúncio**
- **Preço FIPE** (opcional - exibe "Não disponível" se não encontrado)

## 🔧 Pré-requisitos e Instalação

### Passo 1: Instalar Python 3

1. Baixe Python 3.11 ou superior de [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Durante a instalação, **marque a opção "Add Python to PATH"**
3. Verifique a instalação abrindo o terminal/PowerShell e digitando:
   ```bash
   python --version
   ```
   ou
   ```bash
   python3 --version
   ```

### Passo 2: Instalar Dependências

1. Abra o terminal/PowerShell na pasta do projeto
2. Execute o comando:
   ```bash
   pip install -r requirements.txt
   ```

   Ou instale manualmente:
   ```bash
   pip install requests beautifulsoup4 lxml selenium webdriver-manager
   ```

### Passo 3: Google Chrome (Obrigatório)

O script usa o Google Chrome em modo headless (sem abrir janela) para renderizar JavaScript.
- Certifique-se de que o Google Chrome está instalado no seu computador
- O `webdriver-manager` baixará automaticamente o ChromeDriver compatível
- Não é necessário baixar o ChromeDriver manualmente

## 🚀 Como Usar

### Uso Básico

```bash
python main.py "URL_DO_ANUNCIO"
```

### Exemplo

```bash
python main.py "https://sp.olx.com.br/regiao-de-sorocaba/autos-e-pecas/carros-vans-e-utilitarios/aluguel-de-veiculos-p-app-1457220451"
```

### No Windows PowerShell

```powershell
python main.py "URL_DO_ANUNCIO"
```

## 📝 Exemplo de Saída

```
🔍 Buscando dados do anúncio: https://sp.olx.com.br/...
⏳ Aguarde...

============================================================
📋 DADOS DO ANÚNCIO
============================================================

👤 Nome do Vendedor: João Silva
🚗 Modelo do Veículo: Honda Civic 2020
💰 Valor do Anúncio: R$ 85.000,00
📊 Preço FIPE: R$ 90.000,00
============================================================
```

## 📊 Sistema de Logs

O projeto possui um sistema completo de logging que registra todas as operações e erros:

- **Localização**: Os logs são salvos na pasta `logs/`
- **Formato**: Um arquivo por dia com nome `olx_scraper_YYYYMMDD.log`
- **Conteúdo**: Registra todas as requisições HTTP, extrações de dados, avisos e erros
- **Console**: Os logs também são exibidos no console durante a execução

### Exemplo de log

```
2024-01-15 14:30:25 - INFO - Sistema de logging inicializado
2024-01-15 14:30:25 - INFO - Arquivo de log: logs/olx_scraper_20240115.log
2024-01-15 14:30:25 - INFO - Iniciando processamento do anúncio: https://...
2024-01-15 14:30:26 - INFO - Requisição bem-sucedida. Status: 200
2024-01-15 14:30:26 - INFO - Extração concluída. 3/4 campos extraídos com sucesso.
```

## ⚠️ Observações Importantes

- **Selenium como Método Principal**: O script usa Selenium com Chrome headless para renderizar JavaScript e extrair dados dinâmicos
- **Fallback Automático**: Se o Selenium não estiver disponível ou falhar, o script tenta usar requests + BeautifulSoup
- **ChromeDriver Automático**: O `webdriver-manager` baixa e gerencia o ChromeDriver automaticamente - não é necessário instalação manual
- **Modo Headless**: O Chrome roda em modo headless (sem abrir janela visível) para melhor performance
- **Preço FIPE**: Nem todos os anúncios exibem o preço FIPE. Se não estiver disponível, será exibido "Não disponível"
- **Estrutura HTML**: Os seletores são otimizados para a estrutura atual do OLX e podem precisar de ajustes se o site mudar
- **Logs**: Todos os erros são registrados automaticamente no arquivo de log para facilitar o debug

## 🛠️ Tecnologias Utilizadas

- **Selenium** - Automação de navegador (método principal) para renderizar JavaScript
- **webdriver-manager** - Gerenciamento automático do ChromeDriver
- **BeautifulSoup4** - Parsing e extração de dados HTML
- **lxml** - Parser HTML rápido
- **requests** - Requisições HTTP (método fallback)

## ❓ Solução de Problemas

### Erro: "URL inválida ou não é do OLX"
- Certifique-se de que a URL começa com `https://www.olx.com.br` ou `https://sp.olx.com.br`

### Erro: "Alguns dados essenciais não foram encontrados"
- Verifique se o Google Chrome está instalado
- Certifique-se de que o Selenium está instalado: `pip install selenium webdriver-manager`
- O script já usa Selenium automaticamente - verifique os logs para mais detalhes
- Pode ser que a estrutura do site tenha mudado - verifique o arquivo de log

### Erro ao instalar dependências
- Certifique-se de que o Python está instalado corretamente
- Tente usar `pip3` em vez de `pip` em alguns sistemas
- No Windows, pode ser necessário usar `python -m pip install -r requirements.txt`

### Erro: "Selenium não está disponível"
- Instale o Selenium: `pip install selenium webdriver-manager`
- O script funcionará, mas apenas com método fallback (pode não extrair dados dinâmicos)

### Erro: "ChromeDriver não encontrado"
- O `webdriver-manager` deve baixar automaticamente
- Verifique sua conexão com a internet
- Certifique-se de que o Google Chrome está instalado

### Verificar logs de erro
- Todos os erros são registrados automaticamente na pasta `logs/`
- Verifique o arquivo de log mais recente para detalhes sobre erros específicos
- O formato do arquivo é: `olx_scraper_YYYYMMDD.log`

## 📄 Licença

Este projeto é de uso livre para fins educacionais e pessoais.

