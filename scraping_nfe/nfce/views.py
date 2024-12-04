import urllib.parse
import time
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from io import BytesIO
from .models import NotaFiscal, Item
from .forms import ItemForm
from django.urls import reverse
import cv2
from pyzbar.pyzbar import decode
import uuid
from .forms import NotaFiscalForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import logout
from django.contrib import messages
import numpy as np
import os

pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

@login_required
def index(request):
    if request.method == 'POST':
        # Caso o usuário insira a chave de acesso manualmente
        chave_acesso = request.POST.get('chave_acesso')
        if chave_acesso:
            # Verifica se a nota fiscal já existe
            nota_existente = NotaFiscal.objects.filter(chave_acesso=chave_acesso).first()
            if nota_existente:
                messages.warning(request, 'Esta nota fiscal já está cadastrada no sistema.')
                return redirect('index')

            # Se não existe, continua com o processamento
            qr_code_url = f"http://nfce.set.rn.gov.br/portalDFE/NFCe/mDadosNFCe.aspx?p={chave_acesso}"
            qr_code_url_encoded = urllib.parse.quote(qr_code_url, safe='')
            return redirect('process_captcha', qr_code_url=qr_code_url_encoded)

        # Caso o usuário queira escanear o QR code
        if 'escanear_qr_code' in request.POST:
            cap = None
            try:
                # Configurar variáveis de ambiente para X11
                os.environ.pop('QT_QPA_PLATFORM', None)  # Remove configuração do Qt
                os.environ['DISPLAY'] = ':0'  # Força uso do X11
                
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    raise Exception("Não foi possível acessar a câmera")
                
                detector = cv2.QRCodeDetector()
                window_name = 'QRCode Scanner (Pressione Q para sair)'
                cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
                cv2.resizeWindow(window_name, 800, 600)

                while True:
                    ret, img = cap.read()
                    if not ret:
                        raise Exception("Erro ao ler frame da câmera")

                    data, bbox, _ = detector.detectAndDecode(img)
                    
                    if data:
                        # Extrai a chave de acesso da URL do QR code
                        parsed_url = urllib.parse.urlparse(data)
                        query_params = urllib.parse.parse_qs(parsed_url.query)
                        chave_acesso = query_params.get('p', [None])[0]

                        if chave_acesso:
                            # Verifica se a nota fiscal já existe
                            nota_existente = NotaFiscal.objects.filter(chave_acesso=chave_acesso).first()
                            if nota_existente:
                                if cap is not None:
                                    cap.release()
                                cv2.destroyAllWindows()
                                request.session['mensagem_nota_duplicada'] = True
                                return redirect('index')

                            # Se não existe, continua com o processamento
                            qr_code_url = f"http://nfce.set.rn.gov.br/portalDFE/NFCe/mDadosNFCe.aspx?p={chave_acesso}"
                            qr_code_url_encoded = urllib.parse.quote(qr_code_url, safe='')
                            return redirect('process_captcha', qr_code_url=qr_code_url_encoded)

                    cv2.imshow(window_name, img)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        break

            except Exception as e:
                messages.error(request, f'Erro ao escanear QR Code: {str(e)}')
            finally:
                # Garante que a câmera seja fechada mesmo se houver erro
                if cap is not None:
                    cap.release()
                cv2.destroyAllWindows()
                return redirect('index')

    if request.session.pop('mensagem_nota_duplicada', False):
        messages.warning(request, 'Esta nota fiscal já está cadastrada no sistema.')
    return render(request, 'nfce/index.html')

@login_required
def process_qr_code(request):
    if request.method == 'POST' and request.FILES.get('qr_code'):
        try:
            # Lê a imagem do QR code
            image_file = request.FILES['qr_code']
            image = cv2.imdecode(np.frombuffer(image_file.read(), np.uint8), cv2.IMREAD_COLOR)

            # Decodifica o QR code
            detector = cv2.QRCodeDetector()
            data, bbox, _ = detector.detectAndDecode(image)

            if data:
                # Extrai a chave de acesso da URL do QR code
                parsed_url = urllib.parse.urlparse(data)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                chave_acesso = query_params.get('p', [None])[0]

                if chave_acesso:
                    # Verifica se a nota fiscal já existe
                    nota_existente = NotaFiscal.objects.filter(chave_acesso=chave_acesso).first()
                    if nota_existente:
                        messages.warning(request, 'Esta nota fiscal já está cadastrada no sistema!')
                        return redirect('index')

                    # Se não existe, continua com o processamento
                    qr_code_url_encoded = urllib.parse.quote(data, safe='')
                    return redirect('process_captcha', qr_code_url=qr_code_url_encoded)
                else:
                    messages.error(request, 'QR Code inválido: chave de acesso não encontrada.')
                    return redirect('index')
            else:
                messages.error(request, 'Não foi possível ler o QR Code. Por favor, tente novamente.')
                return redirect('index')

        except Exception as e:
            messages.error(request, f'Erro ao processar o QR Code: {str(e)}')
            return redirect('index')

    messages.error(request, 'Método não permitido ou nenhum arquivo enviado.')
    return redirect('index')

def dashboard_view(request):
    # Redireciona o usuário para o dashboard do Streamlit que está rodando no localhost
    return redirect('http://localhost:8501/')

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

def process_captcha(request, qr_code_url):
    qr_code_url = urllib.parse.unquote(qr_code_url)
    driver = webdriver.Chrome()

    success = False
    while not success:
        try:
            driver.get(qr_code_url)
            captcha_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'img_captcha'))
            )

            captcha_location = captcha_element.location
            captcha_size = captcha_element.size
            png = driver.get_screenshot_as_png()

            im = Image.open(BytesIO(png))
            captcha_im = im.crop((captcha_location['x'], captcha_location['y'],
                                  captcha_location['x'] + captcha_size['width'],
                                  captcha_location['y'] + captcha_size['height']))

            captcha_im = captcha_im.convert('L')
            captcha_im = captcha_im.filter(ImageFilter.MedianFilter())
            enhancer = ImageEnhance.Contrast(captcha_im)
            captcha_im = enhancer.enhance(2.0).filter(ImageFilter.SHARPEN)

            captcha_texto = pytesseract.image_to_string(captcha_im, config='--psm 6 -c tessedit_char_whitelist=0123456789')

            campo_captcha = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'txt_cod_antirobo'))
            )
            campo_captcha.send_keys(captcha_texto.strip())

            botao_ver_danfe = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'btnVerDanfe'))
            )
            botao_ver_danfe.click()

            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, 'divConteudoDanfe'))
            )
            success = True

            # Extrai os dados da nota fiscal
            nota_fiscal_data = extract_nota_info(driver)
            driver.quit()

            # Gerar identificador temporário para a nota fiscal
            temp_id = str(uuid.uuid4())
            nota_fiscal_data['temp_id'] = temp_id
            

            # Armazena os dados da nota fiscal na sessão (sem salvar no banco)
            request.session['nota_fiscal_data'] = nota_fiscal_data
            request.session['temp_id'] = temp_id
            # Redireciona para a página de conferência dos itens
            return redirect('conferir_itens')

        except Exception as e:
            print(f"Erro ao tentar resolver o CAPTCHA: {e}")
            time.sleep(5)

    driver.quit()
    return HttpResponse("Erro ao processar o CAPTCHA. Tente novamente.")

@login_required
def conferir_itens(request):
    # Obtém os dados da nota fiscal salvos na sessão (sem ID do banco)
    nota_fiscal_data = request.session.get('nota_fiscal_data', None)

    if nota_fiscal_data is None:
        return HttpResponse("Erro: Nenhum dado de nota fiscal disponível.")

    if request.method == 'POST':
        # Função auxiliar para substituir a vírgula por ponto em valores numéricos e retornar None se o valor for inválido
        def ajustar_valor(valor):
            try:
                if valor is None or valor == '':
                    return 0.0  # Valor padrão 0.0
                # Tenta converter o valor para float após substituir a vírgula por ponto
                return float(valor.replace(',', '.'))
            except ValueError:
                # Caso ocorra um erro de conversão, retorna 0.0 como valor padrão
                return 0.0
        categoria = request.POST.get('categoria', 'outros')  # Define 'outros' como padrão se não for fornecido
        nota_fiscal_data['categoria'] = categoria
        # Atualiza os itens com os dados do formulário
        itens_data = []
        for i in range(len(nota_fiscal_data['itens'])):
            itens_data.append({
                'descricao': request.POST.get(f'item_descricao_{i}'),
                'quantidade': ajustar_valor(request.POST.get(f'item_quantidade_{i}')),
                'unidade': request.POST.get(f'item_unidade_{i}'),
                'valor_unid': ajustar_valor(request.POST.get(f'item_valor_unid_{i}')),
                'desconto': ajustar_valor(request.POST.get(f'item_desconto_{i}')),
                'valor_total': ajustar_valor(request.POST.get(f'item_valor_total_{i}')),
            })
        nota_fiscal_data['itens'] = itens_data

        # Tenta salvar a nota fiscal e os itens no banco de dados
        nota_fiscal = salvar_nota_fiscal_e_itens(nota_fiscal_data, itens_data)
        
        if nota_fiscal is None:
            # Se retornou None, significa que a nota fiscal já existe
            messages.warning(request, 'Esta nota fiscal já está cadastrada no sistema.')
        else:
            messages.success(request, 'Nota fiscal salva com sucesso!')

        # Redirecionar para a página de listagem de notas fiscais após salvar
        return redirect('/')

    # Exibe a página de conferência
    return render(request, 'nfce/conferir_itens.html', {
        'nota_fiscal': nota_fiscal_data,
        'itens': nota_fiscal_data['itens'],
    })


def extract_nota_info(driver):
    # Captura as informações da nota fiscal
    numero_serie = driver.find_element(By.ID, 'lblNumeroSerie').text
    razao_social = driver.find_element(By.ID, 'lblRazaoSocialEmitente').text
    cnpj_emitente = driver.find_element(By.ID, 'lblCPFCNPJEmitente').text
    inscricao_estadual = driver.find_element(By.ID, 'lblInscricaoEstadualEmitente').text

    # Captura as datas de emissão e autorização
    data_emissao = driver.find_element(By.ID, 'lblDataEmissao').text
    data_autorizacao = driver.find_element(By.ID, 'lblDataAutorizacaoDenegacao').text

    # Captura os itens da tabela (todos os itens)
    itens = []
    rows = driver.find_elements(By.XPATH, '//table[@id="tbItensList"]/tbody/tr')
    for row in rows:
        try:
            # Verifica e extrai corretamente cada coluna do item
            descricao = row.find_element(By.XPATH, './/td[3]').text
            quantidade = row.find_element(By.XPATH, './/td[4]').text
            unidade = row.find_element(By.XPATH, './/td[5]').text
            valor_unid = row.find_element(By.XPATH, './/td[6]').text
            desconto = row.find_element(By.XPATH, './/td[7]').text
            valor_total = row.find_element(By.XPATH, './/td[8]').text

            # Remove qualquer espaço em branco ou formatação incorreta
            itens.append({
                'descricao': descricao.strip(),
                'quantidade': quantidade.strip(),
                'unidade': unidade.strip(),
                'valor_unid': valor_unid.strip(),
                'desconto': desconto.strip(),
                'valor_total': valor_total.strip()
            })
        except Exception as e:
            print(f"Erro ao extrair o item: {e}. Linha com problema: {row.text}")

    # Captura o valor total, forma de pagamento e chave de acesso
    valor_total_produtos = driver.find_element(By.ID, 'lblValorTotal').text.strip()
    forma_pagamento = driver.find_element(By.ID, 'lblFormaPagamento').text.strip()
    chave_acesso = driver.find_element(By.ID, 'lblChave').text.strip()

    return {
        'numero_serie': numero_serie.strip(),
        'razao_social': razao_social.strip(),
        'cnpj_emitente': cnpj_emitente.strip(),
        'inscricao_estadual': inscricao_estadual.strip(),
        'data_emissao': data_emissao.strip(),
        'data_autorizacao': data_autorizacao.strip(),
        'itens': itens,
        'valor_total_produtos': valor_total_produtos,
        'forma_pagamento': forma_pagamento,
        'chave_acesso': chave_acesso
    }

def adicionar_nota_fiscal(request):
    if request.method == 'POST':
        descricao = request.POST.get('descricao')
        categoria = request.POST.get('categoria')
        valor_total = request.POST.get('valor_total')
        data_emissao = request.POST.get('data_emissao')

        # Salvar a nova nota fiscal
        try:
            nota_fiscal = NotaFiscal.objects.create(
                categoria=categoria,
                numero_serie='Manual',
                razao_social='Nota Manual',
                cnpj_emitente='N/A',
                inscricao_estadual='N/A',
                data_emissao=data_emissao,
                valor_total_produtos=valor_total,
                forma_pagamento='Manual',
                chave_acesso='Manual',
            )
            
            # Criar um item associado à nota fiscal
            Item.objects.create(
                nota_fiscal=nota_fiscal,
                descricao=descricao,
                quantidade=1,
                unidade='UN',
                valor_unid=valor_total,
                desconto=0.0,
                valor_total=valor_total,
            )

            return redirect('index')
        except Exception as e:
            return HttpResponse(f"Erro ao adicionar nota fiscal manual: {e}")

    return HttpResponse("Método não permitido", status=405)


def salvar_nota_fiscal_e_itens(nota_fiscal_data, itens_data):
    # Função auxiliar para converter valores com vírgula em valores decimais e garantir que não sejam nulos
    def converter_valor_decimal(valor):
        try:
            if valor is None or valor == '':
                return 0.0  # Retorna 0.0 se o valor for None ou vazio
            if isinstance(valor, str):
                valor = valor.replace(',', '.').strip()  # Converte vírgula em ponto e remove espaços
            return float(valor)  # Converte para float para garantir que seja numérico
        except ValueError:
            print(f"Erro ao converter valor: {valor}")
            return 0.0  # Retorna 0.0 se a conversão falhar

    # Converte os valores numéricos da nota fiscal (somente os campos numéricos)
    nota_fiscal_data['valor_total_produtos'] = converter_valor_decimal(nota_fiscal_data['valor_total_produtos'])

    try:
        # Verifica se já existe uma nota fiscal com a mesma chave de acesso
        chave_acesso = nota_fiscal_data.get('chave_acesso')
        if NotaFiscal.objects.filter(chave_acesso=chave_acesso).exists():
            print(f"Nota fiscal com chave de acesso {chave_acesso} já existe no sistema.")
            return None

        # Verifica se a categoria está presente no nota_fiscal_data
        categoria = nota_fiscal_data.get('categoria', None)
        
        # Caso a categoria não tenha sido passada, define um valor padrão
        if not categoria:
            print("Categoria não fornecida, utilizando valor padrão 'Outros'")
            categoria = 'Outros'

        # Salva a nota fiscal no banco
        nota_fiscal = NotaFiscal.objects.create(
            categoria=categoria,
            numero_serie=nota_fiscal_data['numero_serie'],
            razao_social=nota_fiscal_data['razao_social'],
            cnpj_emitente=nota_fiscal_data['cnpj_emitente'],
            inscricao_estadual=nota_fiscal_data['inscricao_estadual'],
            data_emissao=nota_fiscal_data['data_emissao'],
            data_autorizacao=nota_fiscal_data['data_autorizacao'],
            valor_total_produtos=nota_fiscal_data['valor_total_produtos'],
            forma_pagamento=nota_fiscal_data['forma_pagamento'],
            chave_acesso=chave_acesso,
        )
        print(f"Nota Fiscal salva com ID: {nota_fiscal.id} e categoria: {categoria}")
    except Exception as e:
        print(f"Erro ao salvar a nota fiscal: {e}")
        return None

    # Itera sobre os itens e salva no banco
    for item_data in itens_data:
        descricao = item_data.get('descricao', '').strip() or 'Sem descrição'
        quantidade = converter_valor_decimal(item_data.get('quantidade'))
        unidade = item_data.get('unidade', '').strip() or 'UN'
        valor_unid = converter_valor_decimal(item_data.get('valor_unid'))
        desconto = converter_valor_decimal(item_data.get('desconto'))
        valor_total = converter_valor_decimal(item_data.get('valor_total'))

        # Verifica se todos os campos são válidos
        if descricao and unidade:
            try:
                Item.objects.create(
                    nota_fiscal=nota_fiscal,
                    descricao=descricao,
                    quantidade=quantidade,
                    unidade=unidade,
                    valor_unid=valor_unid,
                    desconto=desconto,
                    valor_total=valor_total,
                )
                print(f"Item salvo: {descricao}")
            except Exception as e:
                print(f"Erro ao salvar o item: {item_data}. Erro: {e}")
        else:
            print(f"Ignorando item inválido ou incompleto: {item_data}")

    return nota_fiscal




def listar_notas_fiscais(request):
    notas_fiscais = NotaFiscal.objects.all()
    return render(request, 'index', {'notas_fiscais': notas_fiscais})

def editar_itens(request, nota_fiscal_id):
    # Obtém a nota fiscal pelo ID
    nota_fiscal = get_object_or_404(NotaFiscal, id=nota_fiscal_id)
    itens = nota_fiscal.itens.all()

    if request.method == 'POST':
        if 'editar_item' in request.POST:
            # Editar um item específico
            item_id = request.POST.get('item_id')
            item = get_object_or_404(Item, id=item_id)
            form = ItemForm(request.POST, instance=item)
            if form.is_valid():
                form.save()
                return redirect('editar_itens', nota_fiscal_id=nota_fiscal_id)

        elif 'excluir_item' in request.POST:
            # Excluir um item específico
            item_id = request.POST.get('item_id')
            item = get_object_or_404(Item, id=item_id)
            item.delete()
            return redirect('editar_itens', nota_fiscal_id=nota_fiscal_id)

        elif 'salvar_nota_fiscal' in request.POST:
            # Confirmar o salvamento e redirecionar para a listagem de notas
            return redirect('index')

    form = ItemForm()  # Formulário vazio apenas para exibir no template, mas não será utilizado para adicionar novos itens
    return render(request, 'nfce/editar_itens.html', {
        'nota_fiscal': nota_fiscal,
        'itens': itens,
        'form': form
    })

@login_required
def consultar_nfce(request):
    if request.method == 'POST':
        # Caso o usuário insira a chave de acesso manualmente
        chave_acesso = request.POST.get('chave_acesso', '').strip()
        if chave_acesso:
            # Verifica se a nota fiscal já existe
            nota_existente = NotaFiscal.objects.filter(chave_acesso=chave_acesso).first()
            if nota_existente:
                messages.warning(request, 'Esta nota fiscal já está cadastrada no sistema.')
                return redirect('index')

            # Se não existe, continua com o processamento
            qr_code_url = f"http://nfce.set.rn.gov.br/portalDFE/NFCe/mDadosNFCe.aspx?p={chave_acesso}"
            qr_code_url_encoded = urllib.parse.quote(qr_code_url, safe='')
            return redirect('process_captcha', qr_code_url=qr_code_url_encoded)

    return render(request, 'nfce/index.html')

def nota_fiscal_view(request, nota_fiscal_id):
    # Obtém a nota fiscal pelo ID passado como argumento
    nota_fiscal = get_object_or_404(NotaFiscal, id=nota_fiscal_id)
    
    # Passa a nota fiscal e seus itens para o template
    return render(request, 'nfce/nota_fiscal.html', {
        'nota_fiscal': nota_fiscal,
        'itens': nota_fiscal.itens.all(),  # Assume que 'itens' é um relacionamento ManyToMany ou ForeignKey no modelo
    })
def inicio_view(request):
    return render(request, 'nfce/inicio.html') 
def cadastro_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # Redireciona o usuário para a página de login após o cadastro
    else:
        form = UserCreationForm()
    
    return render(request, 'nfce/cadastro.html', {'form': form})

@login_required
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    return render(request, 'nfce/logout.html')