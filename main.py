from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import pytesseract
from io import BytesIO

# Caminho para o Tesseract no seu sistema (pode variar conforme a instalação)
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

# Inicia o webdriver (assumindo que o chromedriver está no PATH)
driver = webdriver.Chrome()

# Acessa a página desejada
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

# Usar OCR para extrair o texto do CAPTCHA
captcha_texto = pytesseract.image_to_string(captcha_im, config='--psm 7')
print(f"Texto do CAPTCHA: {captcha_texto}")

# Espera até que o campo de texto do CAPTCHA esteja presente e localiza o campo
campo_captcha = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.NAME, 'txt_cod_antirobo'))
)
campo_captcha.send_keys(captcha_texto.strip())  # Remove possíveis espaços em branco

# Localiza e clica no botão "Ver DANFE"
botao_ver_danfe = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.NAME, 'btnVerDanfe'))
)
botao_ver_danfe.click()

# Espera as informações da DANFE serem carregadas e as imprime
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, 'informacoesDanfe'))  # Ajuste conforme a estrutura da página
)

# Exemplo para capturar e exibir as informações desejadas
danfe_info = driver.find_element(By.ID, 'informacoesDanfe').text
print(f"Informações da DANFE: {danfe_info}")

# Fechar o driver após o processamento
driver.quit()
