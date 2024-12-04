# Consulta SEFAZ - Automatização de Consulta de Notas Fiscais

O **Consulta SEFAZ** é uma aplicação Python desenvolvida para automatizar a consulta e extração de dados de Notas Fiscais Eletrônicas no portal da SEFAZ. A aplicação utiliza técnicas avançadas de web scraping e processamento de imagem para automatizar o preenchimento de CAPTCHA, tornando o processo de consulta mais eficiente.

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
- [Selenium](https://pypi.org/project/selenium/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) para reconhecimento de texto nas imagens do CAPTCHA
- [OpenCV](https://opencv.org/) para processamento de imagens
- Um driver para o Selenium (por exemplo, [ChromeDriver](https://sites.google.com/a/chromium.org/chromedriver/) para o Google Chrome)

## Instalação

1. Clone este repositório para o seu ambiente local:
   ```bash
   git clone [URL do repositório]
   cd consulta_sefaz
   ```

2. Crie um ambiente virtual e ative-o:
   ```bash
   python -m venv myenv
   source myenv/bin/activate  # No Windows use: myenv\Scripts\activate
   ```

3. Instale as dependências do projeto:
   ```bash
   pip install -r requirements.txt
   ```

4. Instale o Tesseract OCR:
   * Linux: `sudo apt-get install tesseract-ocr`
   * macOS: `brew install tesseract`
   * Windows: Baixe o instalador do site oficial do Tesseract OCR e adicione-o ao seu PATH

5. Configure o Selenium com o navegador de sua escolha (ex: ChromeDriver)

## Configuração

1. Certifique-se de que o Tesseract OCR está corretamente instalado e acessível no PATH do sistema

2. Verifique se o ChromeDriver (ou outro driver de navegador) está instalado e configurado corretamente

3. O projeto já vem com as configurações padrão necessárias para funcionar na maioria dos ambientes

## Funcionalidades

### Consulta Automatizada:
- Preenchimento automático de formulários no portal SEFAZ
- Processamento e resolução automática de CAPTCHA
- Extração de dados das notas fiscais consultadas

### Processamento de CAPTCHA:
- Captura automática da imagem do CAPTCHA
- Pré-processamento da imagem usando OpenCV
- Reconhecimento de texto usando Tesseract OCR
- Alta taxa de sucesso no reconhecimento

### Automação Web:
- Navegação automática pelo portal da SEFAZ
- Preenchimento inteligente de formulários
- Tratamento de erros e tentativas automáticas de reconexão

## Estrutura do Projeto

```
consulta_sefaz/
├── app.py              # Aplicação principal com a lógica de automação
├── ler_captcha.py      # Módulo de processamento de CAPTCHA
├── main.py             # Script principal de execução
├── requirements.txt    # Dependências do projeto
├── scraping_nfe/      # Módulos de web scraping
└── README.MD          # Documentação do projeto
```

## Uso

1. Ative o ambiente virtual:
   ```bash
   source myenv/bin/activate  # No Windows use: myenv\Scripts\activate
   ```

2. Execute o script principal:
   ```bash
   python main.py
   ```

3. Siga as instruções na interface para:
   - Inserir os dados da nota fiscal que deseja consultar
   - Acompanhar o processo de automação
   - Visualizar os resultados da consulta

4. O sistema irá:
   - Acessar automaticamente o portal da SEFAZ
   - Resolver o CAPTCHA apresentado
   - Preencher os dados necessários
   - Extrair as informações da nota fiscal

## Tecnologias Utilizadas

- **Python**: Linguagem principal do projeto
- **Selenium**: Framework para automação web
- **OpenCV**: Biblioteca para processamento de imagens
- **Tesseract OCR**: Engine para reconhecimento ótico de caracteres
- **Outras bibliotecas**: Conforme listadas no requirements.txt

## Contribuição

Contribuições são bem-vindas! Para contribuir:

1. Faça um fork do repositório
2. Crie uma branch para sua feature:
   ```bash
   git checkout -b feature/nova-feature
   ```
3. Faça commit das suas mudanças:
   ```bash
   git commit -m 'Adiciona nova feature'
   ```
4. Faça push para a branch:
   ```bash
   git push origin feature/nova-feature
   ```
5. Abra um Pull Request

### Diretrizes para Contribuição
- Mantenha o código limpo e bem documentado
- Adicione testes para novas funcionalidades
- Atualize a documentação quando necessário
- Siga as boas práticas de Python (PEP 8)

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---
Desenvolvido com ❤️ para automatizar consultas na SEFAZ