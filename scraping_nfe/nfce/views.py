import urllib.parse
import time
from django.shortcuts import render, redirect
from django.http import HttpResponse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from io import BytesIO
import cv2
from pyzbar.pyzbar import decode

pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

def escanear_qr_code_com_camera():
    cap = cv2.VideoCapture(0)  # Abre a câmera

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        decoded_objects = decode(frame)
        for obj in decoded_objects:
            qr_code_url = obj.data.decode('utf-8')
            cap.release()
            cv2.destroyAllWindows()
            return qr_code_url

        cv2.imshow('Escaneando QR Code - Pressione "q" para sair', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return None

def index(request):
    if request.method == 'POST':
        # Checa se o usuário quer escanear o QR code
        if 'escanear_qr_code' in request.POST:
            qr_code_url = escanear_qr_code_com_camera()
            if qr_code_url:
                qr_code_url_encoded = urllib.parse.quote(qr_code_url, safe='')
                return redirect('process_captcha', qr_code_url=qr_code_url_encoded)
            else:
                return HttpResponse('QR Code não encontrado ou leitura falhou.')
        
        # Caso o usuário insira a chave de acesso manualmente
        chave_acesso = request.POST.get('chave_acesso')
        if chave_acesso:
            qr_code_url = f"http://nfce.set.rn.gov.br/portalDFE/NFCe/mDadosNFCe.aspx?p={chave_acesso}"
            qr_code_url_encoded = urllib.parse.quote(qr_code_url, safe='')
            return redirect('process_captcha', qr_code_url=qr_code_url_encoded)

    return render(request, 'nfce/index.html')

def process_captcha(request, qr_code_url):
    # Decodifica a URL
    qr_code_url = urllib.parse.unquote(qr_code_url)

    # Inicializa o driver do Selenium para acessar a página
    driver = webdriver.Chrome()

    while True:
        try:
            driver.get(qr_code_url)

            # Espera até que o CAPTCHA esteja presente
            captcha_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'img_captcha'))
            )

            # Captura o CAPTCHA, resolve e continua o processo
            captcha_location = captcha_element.location
            captcha_size = captcha_element.size
            png = driver.get_screenshot_as_png()

            im = Image.open(BytesIO(png))
            left = captcha_location['x']
            top = captcha_location['y']
            right = left + captcha_size['width']
            bottom = top + captcha_size['height']
            captcha_im = im.crop((left, top, right, bottom))

            captcha_im = captcha_im.convert('L')  # Converte para escala de cinza
            captcha_im = captcha_im.filter(ImageFilter.MedianFilter())
            enhancer = ImageEnhance.Contrast(captcha_im)
            captcha_im = enhancer.enhance(2.0)
            captcha_im = captcha_im.filter(ImageFilter.SHARPEN)

            captcha_texto = pytesseract.image_to_string(captcha_im, config='--psm 6 -c tessedit_char_whitelist=0123456789')

            # Preenche o CAPTCHA no campo de texto e prossegue
            campo_captcha = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'txt_cod_antirobo'))
            )
            campo_captcha.send_keys(captcha_texto.strip())

            botao_ver_danfe = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'btnVerDanfe'))
            )
            botao_ver_danfe.click()

            # Verifica se a página da nota fiscal foi carregada corretamente
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, 'divConteudoDanfe'))
            )

            # Extrai as informações da nota fiscal
            context = extract_nota_info(driver)
            break  # Sai do loop quando o CAPTCHA for resolvido

        except Exception as e:
            # Aguarda um pouco antes de tentar novamente
            print(f"Erro ao tentar resolver o CAPTCHA: {e}. Tentando novamente...")
            time.sleep(5)  # Pausa de 5 segundos antes de tentar novamente

    driver.quit()
    return render(request, 'nfce/nota_fiscal.html', context)

def extract_nota_info(driver):
    numero_serie = driver.find_element(By.ID, 'lblNumeroSerie').text
    razao_social = driver.find_element(By.ID, 'lblRazaoSocialEmitente').text
    cnpj_emitente = driver.find_element(By.ID, 'lblCPFCNPJEmitente').text
    inscricao_estadual = driver.find_element(By.ID, 'lblInscricaoEstadualEmitente').text
    descricao_produto = driver.find_element(By.ID, 'tbItensList_lblTbItensDescricao_0').text
    valor_total_produtos = driver.find_element(By.ID, 'lblValorTotal').text
    forma_pagamento = driver.find_element(By.ID, 'lblFormaPagamento').text
    chave_acesso = driver.find_element(By.ID, 'lblChave').text

    return {
        'numero_serie': numero_serie,
        'razao_social': razao_social,
        'cnpj_emitente': cnpj_emitente,
        'inscricao_estadual': inscricao_estadual,
        'descricao_produto': descricao_produto,
        'valor_total_produtos': valor_total_produtos,
        'forma_pagamento': forma_pagamento,
        'chave_acesso': chave_acesso
    }
