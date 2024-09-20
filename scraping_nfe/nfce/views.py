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

pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

def index(request):
    if request.method == 'POST':
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

    success = False
    while not success:
        try:
            driver.get(qr_code_url)

            # Espera até que o CAPTCHA esteja presente
            captcha_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'img_captcha'))
            )

            # Captura e resolve o CAPTCHA
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

            # Preenche o CAPTCHA e prossegue
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

            # Se a página da nota fiscal foi carregada, parar o loop
            success = True

            # Extrai as informações da nota fiscal
            nota_fiscal_data = extract_nota_info(driver)
            
            # Salva a Nota Fiscal imediatamente
            nota_fiscal = salvar_nota_fiscal_e_itens(nota_fiscal_data, nota_fiscal_data.pop('itens'))

            # Verifica se a nota fiscal foi salva corretamente
            if nota_fiscal is None or nota_fiscal.id is None:
                return HttpResponse("Erro ao salvar a nota fiscal. Tente novamente.")

            # Fecha o navegador
            driver.quit()

            # Salva o ID da nota fiscal na sessão
            request.session['nota_fiscal_id'] = nota_fiscal.id

            # Redireciona para a página de conferência dos itens
            return redirect('conferir_itens')

        except Exception as e:
            print(f"Erro ao tentar resolver o CAPTCHA: {e}")
            time.sleep(5)  # Tenta novamente após 5 segundos

    # Caso o loop falhe e saia sem sucesso, garante que o driver seja fechado
    driver.quit()
    return HttpResponse("Erro ao processar o CAPTCHA. Tente novamente.")


def conferir_itens(request):
    # Obtém o ID da nota fiscal salvo na sessão
    nota_fiscal_id = request.session.get('nota_fiscal_id', None)

    if nota_fiscal_id is None:
        return HttpResponse("Erro: Nenhum dado de nota fiscal disponível.")

    # Obtém a nota fiscal a partir do ID
    nota_fiscal = NotaFiscal.objects.get(id=nota_fiscal_id)

    if request.method == 'POST':
        # Editar um item específico
        if 'editar_item' in request.POST:
            item_id = request.POST.get('item_id')
            item = get_object_or_404(Item, id=item_id)

            # Atualizar os campos do item com os valores enviados
            item.descricao = request.POST.get('descricao')
            item.quantidade = request.POST.get('quantidade').replace(',', '.')
            item.unidade = request.POST.get('unidade')
            item.valor_unid = request.POST.get('valor_unid').replace(',', '.')
            item.desconto = request.POST.get('desconto').replace(',', '.')
            item.valor_total = request.POST.get('valor_total').replace(',', '.')

            # Salvar as mudanças no banco
            item.save()

            # Redireciona para a mesma página para evitar reenvio do formulário
            return redirect('conferir_itens')

        # Excluir um item específico
        elif 'excluir_item' in request.POST:
            item_id = request.POST.get('item_id')
            item = get_object_or_404(Item, id=item_id)
            item.delete()

            # Redireciona para a mesma página para evitar reenvio do formulário
            return redirect('conferir_itens')

        # Salvar a nota fiscal e os itens no banco de dados
        elif 'salvar_nota_fiscal' in request.POST:
            # Salva os itens, caso ainda não estejam no banco
            if not nota_fiscal.itens.exists():  # Verifica se os itens já existem
                for item_data in nota_fiscal_data['itens']:
                    quantidade = float(item_data['quantidade'].replace(',', '.'))
                    valor_unid = float(item_data['valor_unid'].replace(',', '.'))
                    desconto = float(item_data['desconto'].replace(',', '.'))
                    valor_total = float(item_data['valor_total'].replace(',', '.'))

                    Item.objects.create(
                        nota_fiscal=nota_fiscal,
                        descricao=item_data['descricao'],
                        quantidade=quantidade,
                        unidade=item_data['unidade'],
                        valor_unid=valor_unid,
                        desconto=desconto,
                        valor_total=valor_total
                    )

            # Redirecionar para a página de edição de itens com o ID correto
            return redirect('editar_itens', nota_fiscal_id=nota_fiscal.id)

    # Exibe a página de conferência
    return render(request, 'nfce/conferir_itens.html', {
        'nota_fiscal': nota_fiscal,
        'itens': nota_fiscal.itens.all(),
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


def salvar_nota_fiscal_e_itens(nota_fiscal_data, itens_data):
    # Função auxiliar para converter valores com vírgula em valores decimais corretos
    def converter_valor_decimal(valor):
        try:
            if isinstance(valor, str):
                valor = valor.replace(',', '.').strip()  # Converte vírgula em ponto e remove espaços
            return float(valor)  # Converte para float para garantir que seja numérico
        except ValueError:
            print(f"Erro ao converter valor: {valor}")
            return None  # Retorna None se a conversão falhar

    # Converte os valores numéricos da nota fiscal (somente os campos numéricos)
    nota_fiscal_data['valor_total_produtos'] = converter_valor_decimal(nota_fiscal_data['valor_total_produtos'])

    # Cria a instância da NotaFiscal
    try:
        nota_fiscal = NotaFiscal.objects.create(
            numero_serie=nota_fiscal_data['numero_serie'],
            razao_social=nota_fiscal_data['razao_social'],
            cnpj_emitente=nota_fiscal_data['cnpj_emitente'],
            inscricao_estadual=nota_fiscal_data['inscricao_estadual'],
            data_emissao=nota_fiscal_data['data_emissao'],
            data_autorizacao=nota_fiscal_data['data_autorizacao'],
            valor_total_produtos=nota_fiscal_data['valor_total_produtos'],
            forma_pagamento=nota_fiscal_data['forma_pagamento'],
            chave_acesso=nota_fiscal_data['chave_acesso'],
        )
        print(f"Nota Fiscal salva com ID: {nota_fiscal.id}")
    except Exception as e:
        print(f"Erro ao salvar a nota fiscal: {e}")
        return None  # Retorna None se a criação falhar

    # Verifica se a instância foi criada e se possui um ID válido
    if not nota_fiscal.id:
        print("Erro: ID da nota fiscal não gerado corretamente.")
        return None

    # Itera sobre os itens e converte apenas os campos numéricos antes de salvar
    for item_data in itens_data:
        # Converte valores numéricos e valida antes de salvar
        quantidade = converter_valor_decimal(item_data['quantidade'])
        valor_unid = converter_valor_decimal(item_data['valor_unid'])
        desconto = converter_valor_decimal(item_data['desconto'])
        valor_total = converter_valor_decimal(item_data['valor_total'])

        # Verifica se todos os valores numéricos são válidos antes de salvar
        if quantidade is not None and valor_unid is not None and valor_total is not None:
            try:
                Item.objects.create(
                    nota_fiscal=nota_fiscal,
                    descricao=item_data['descricao'],  # Campo de texto, não precisa de conversão
                    quantidade=quantidade,  # Numérico
                    unidade=item_data['unidade'],  # Campo de texto, não precisa de conversão
                    valor_unid=valor_unid,  # Numérico
                    desconto=desconto if desconto is not None else 0,  # Numérico, valor padrão 0 se None
                    valor_total=valor_total,  # Numérico
                )
                print(f"Item salvo: {item_data['descricao']}")
            except Exception as e:
                print(f"Erro ao salvar o item: {item_data}. Erro: {e}")
        else:
            print(f"Erro ao salvar o item: {item_data}. Quantidade, valor unitário ou valor total inválidos.")

    # Retorna a instância de NotaFiscal
    return nota_fiscal







def listar_notas_fiscais(request):
    notas_fiscais = NotaFiscal.objects.all()
    return render(request, 'nfce/nota_fiscal.html', {'notas_fiscais': notas_fiscais})

def editar_itens(request, nota_fiscal_id):
    nota_fiscal = get_object_or_404(NotaFiscal, id=nota_fiscal_id)
    itens = nota_fiscal.itens.all()

    if request.method == 'POST':
        if 'adicionar_item' in request.POST:
            form = ItemForm(request.POST)
            if form.is_valid():
                item = form.save(commit=False)
                item.nota_fiscal = nota_fiscal
                item.save()
                return redirect('editar_itens', nota_fiscal_id=nota_fiscal_id)

        elif 'editar_item' in request.POST:
            item_id = request.POST.get('item_id')
            item = get_object_or_404(Item, id=item_id)
            form = ItemForm(request.POST, instance=item)
            if form.is_valid():
                form.save()
                return redirect('editar_itens', nota_fiscal_id=nota_fiscal_id)

        elif 'excluir_item' in request.POST:
            item_id = request.POST.get('item_id')
            item = get_object_or_404(Item, id=item_id)
            item.delete()
            return redirect('editar_itens', nota_fiscal_id=nota_fiscal_id)

        elif 'salvar_nota_fiscal' in request.POST:
            return redirect('index')

    form = ItemForm()
    return render(request, 'nfce/editar_itens.html', {
        'nota_fiscal': nota_fiscal,
        'itens': itens,
        'form': form  # O formulário será vazio, mas você pode customizá-lo para pré-preencher itens.
    })


def nota_fiscal_view(request, nota_fiscal_id):
    # Obtém a nota fiscal pelo ID passado como argumento
    nota_fiscal = get_object_or_404(NotaFiscal, id=nota_fiscal_id)
    
    # Passa a nota fiscal e seus itens para o template
    return render(request, 'nfce/nota_fiscal.html', {
        'nota_fiscal': nota_fiscal,
        'itens': nota_fiscal.itens.all(),  # Assume que 'itens' é um relacionamento ManyToMany ou ForeignKey no modelo
    })