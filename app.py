from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from io import BytesIO
import time

# Caminho para o Tesseract no seu sistema
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

# Função para processar o CAPTCHA e tentar acessar a página da DANFE
def resolver_captcha():
    # Loop até conseguir resolver o CAPTCHA e avançar
    captcha_resolvido = False
    while not captcha_resolvido:
        try:
            # Acessa novamente a página desejada
            driver.get('http://nfce.set.rn.gov.br/portalDFE/NFCe/mDadosNFCe.aspx?p=24240930967492000150651260005065011186908554%7C2%7C1%7C1%7CA47C80821009C87703023BD2DB82B743C46FC7E9')

            # Espera até que o CAPTCHA esteja presente
            captcha_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'img_captcha'))
            )

            # Localiza o elemento CAPTCHA na tela
            captcha_location = captcha_element.location
            captcha_size = captcha_element.size
            png = driver.get_screenshot_as_png()  # Captura a tela inteira

            # Abre a imagem e faz o crop para capturar somente a área do CAPTCHA
            im = Image.open(BytesIO(png))
            left = captcha_location['x']
            top = captcha_location['y']
            right = left + captcha_size['width']
            bottom = top + captcha_size['height']
            captcha_im = im.crop((left, top, right, bottom))

            # Pré-processamento da imagem para melhorar o OCR
            captcha_im = captcha_im.convert('L')  # Converte para escala de cinza
            captcha_im = captcha_im.filter(ImageFilter.MedianFilter())  # Reduz ruídos leves
            enhancer = ImageEnhance.Contrast(captcha_im)
            captcha_im = enhancer.enhance(2.0)  # Aumenta o contraste
            captcha_im = captcha_im.filter(ImageFilter.SHARPEN)  # Aplica nitidez

            # Usar OCR para extrair o texto do CAPTCHA (somente números)
            captcha_texto = pytesseract.image_to_string(captcha_im, config='--psm 6 -c tessedit_char_whitelist=0123456789')
            print(f"Texto do CAPTCHA: {captcha_texto}")

            # Verifica se o texto capturado tem os 6 dígitos esperados
            if len(captcha_texto.strip()) == 6:
                # Enviar o CAPTCHA resolvido
                campo_captcha = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, 'txt_cod_antirobo'))
                )
                campo_captcha.send_keys(captcha_texto.strip())

                # Aguardar um pouco antes de clicar no botão
                time.sleep(3)  # Pausa para garantir que o CAPTCHA foi digitado

                # Clica no botão "Ver DANFE"
                botao_ver_danfe = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, 'btnVerDanfe'))
                )
                botao_ver_danfe.click()

                # Verifica se avançou para a página da nota fiscal (DANFE)
                try:
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.ID, 'divConteudoDanfe'))
                    )
                    print("CAPTCHA resolvido com sucesso! Acessando a página da DANFE.")
                    captcha_resolvido = True  # Finaliza o loop quando o CAPTCHA for resolvido
                except:
                    print("Falha ao carregar a página da DANFE, recarregando a página...")
            else:
                print("CAPTCHA incompleto, recarregando a página...")

        except Exception as e:
            print(f"Erro: {e}. Recarregando a página e tentando novamente...")

        # Recarrega a página se a tentativa falhar
        time.sleep(5)  # Pausa de 5 segundos antes de tentar novamente

# Função para capturar os dados da nota fiscal
def extrair_informacoes_nota():
    try:
        # Espera a página da nota fiscal carregar e localiza os elementos de interesse
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, 'divConteudoDanfe'))
        )

        # Captura o número e série
        numero_serie = driver.find_element(By.ID, 'lblNumeroSerie').text
        print(f"Número e Série: {numero_serie}")

        # Captura a razão social e CNPJ
        razao_social = driver.find_element(By.ID, 'lblRazaoSocialEmitente').text
        cnpj_emitente = driver.find_element(By.ID, 'lblCPFCNPJEmitente').text
        inscricao_estadual = driver.find_element(By.ID, 'lblInscricaoEstadualEmitente').text
        data_emissao = driver.find_element(By.ID, 'lblDataEmissao').text
        print(f"Razão Social: {razao_social}")
        print(f"CNPJ: {cnpj_emitente}")
        print(f"Inscrição Estadual: {inscricao_estadual}")
        print(f"Data: {data_emissao}")

        # Captura a descrição do produto
        descricao_produto = driver.find_element(By.ID, 'tbItensList_lblTbItensDescricao_0').text
        print(f"Descrição do Produto: {descricao_produto}")

        # Captura o valor total do produto
        valor_total_produtos = driver.find_element(By.ID, 'lblValorTotal').text
        print(f"Valor Total dos Produtos: {valor_total_produtos}")

        # Captura a forma de pagamento
        forma_pagamento = driver.find_element(By.ID, 'lblFormaPagamento').text
        print(f"Forma de Pagamento: {forma_pagamento}")

        # Captura a chave de acesso
        chave_acesso = driver.find_element(By.ID, 'lblChave').text
        print(f"Chave de Acesso: {chave_acesso}")

    except Exception as e:
        print(f"Erro ao extrair informações da nota: {e}")

# Inicia o webdriver (assumindo que o chromedriver está no PATH)
driver = webdriver.Chrome()

# Chama a função para resolver o CAPTCHA
resolver_captcha()

# Chama a função para extrair as informações da nota fiscal
extrair_informacoes_nota()

# Fechar o driver após o processamento
driver.quit()
