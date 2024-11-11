# NFCE Scraper

O **NFCE Scraper** é uma aplicação Django desenvolvida para automatizar a leitura e extração de dados de Notas Fiscais Eletrônicas (NFC-e). A aplicação permite o cadastro de notas através do QR Code, chave de acesso ou de forma manual, além de possuir um dashboard financeiro para a visualização e análise dos gastos.

## Índice

- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Funcionalidades](#funcionalidades)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Uso](#uso)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Contribuição](#contribuição)
- [Licença](#licença)

## Pré-requisitos

Antes de começar, certifique-se de ter os seguintes programas instalados:

- [Python 3.x](https://www.python.org/downloads/)
- [Django](https://www.djangoproject.com/)
- [Selenium](https://pypi.org/project/selenium/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) para reconhecimento de texto nas imagens do CAPTCHA
- [OpenCV](https://opencv.org/) para o uso da câmera (para leitura de QR Codes)
- Um driver para o Selenium (por exemplo, [ChromeDriver](https://sites.google.com/a/chromium.org/chromedriver/) para o Google Chrome)

## Instalação

1. Clone este repositório para o seu ambiente local:

   ```bash
   git clone https://github.com/seu-usuario/nfce-scraper.git
   cd nfce-scraper
   ```
Crie um ambiente virtual e ative-o:

 ```bash
python3 -m venv venv
source venv/bin/activate 
```
Instale as dependências do projeto:

 ```bash
pip install -r requirements.txt
```
Instale o Tesseract OCR:

Linux: sudo apt-get install tesseract-ocr
macOS: brew install tesseract
Windows: Baixe o instalador do site oficial do Tesseract OCR e adicione-o ao seu PATH.
Configure o Django para usar o driver Selenium com o navegador de sua escolha (ex: ChromeDriver).

Configuração
Crie um arquivo .env na raiz do projeto para armazenar as variáveis de ambiente necessárias, incluindo as credenciais e configurações do banco de dados.

Defina o caminho do executável do Tesseract no arquivo .env:

env
Copiar código
TESSERACT_CMD=/path/to/tesseract  # Altere para o caminho correto do executável
Realize as migrações do banco de dados:

 ```bash
python manage.py migrate
```
Crie um superusuário para acessar a interface administrativa do Django:

 ```bash
python manage.py createsuperuser
```
Funcionalidades
Cadastro de Notas Fiscais:

Leitura de NFC-e através do QR Code.
Entrada manual da chave de acesso.
Cadastro manual de notas fiscais e itens.
Processamento de CAPTCHA:

Uso do Selenium e Tesseract OCR para reconhecimento e preenchimento de CAPTCHA automaticamente.
Dashboard Financeiro:

Visualização de dados financeiros com gráficos de gastos por mês e categoria.
Filtros para análise por mês, ano e categoria.
Meta de gasto mensal para alertar o usuário quando o limite for ultrapassado.
Sugestões de economia com base no histórico de compras.
## Estrutura do Projeto
```bash
nfce-scraper/
├── nfce/                  # Aplicação principal
│   ├── migrations/        # Migrações do Django
│   ├── templates/         # Templates HTML
│   ├── static/            # Arquivos estáticos (CSS, JS, etc.)
│   ├── forms.py           # Formulários Django para o sistema
│   ├── models.py          # Modelos de dados
│   ├── views.py           # Lógica de visualização
│   └── urls.py            # URLs da aplicação
├── scraping_nfe/          # Configurações principais do Django
├── manage.py              # Script de gerenciamento do Django
├── requirements.txt       # Arquivo com as dependências do Python
└── README.md              # Documentação do projeto
```
## Inicie o servidor Django:

 ```bash
python manage.py runserver
```
Acesse a aplicação no navegador:

Página inicial: <http://localhost:8000/>
Dashboard financeiro (rodando com Streamlit): <http://localhost:8501/>
Fluxo de Cadastro de Nota Fiscal
Acesse a página de cadastro de notas fiscais.
Escolha entre:
Escanear o QR Code com a câmera.
Inserir a chave de acesso manualmente.
Adicionar uma nota fiscal manualmente.
Após o cadastro, você será redirecionado para a página de conferência de itens.
Edite os itens conforme necessário e salve a nota fiscal.
Dashboard
O dashboard financeiro fornece gráficos de gastos mensais e de distribuição de categorias. Utilize os filtros de data e categoria para uma análise mais detalhada.

## Tecnologias Utilizadas
Backend: Django
Interface do Usuário: HTML, CSS, Bootstrap, Font Awesome
Automação e Web Scraping: Selenium, OpenCV, Tesseract OCR
Visualização de Dados: Streamlit, Plotly
Banco de Dados: Configuração padrão do Django (pode ser ajustado para SQLite, PostgreSQL, etc.)


