import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains


load_dotenv("credenciais.env")

ARQUIVO_PROCESSADOS = Path("emails_processados.txt")
ARQUIVO_LOG = Path("logs") / "bot.log"
MODO_TESTE = os.getenv("MODO_TESTE", os.getenv("TEST_MODE", "")).strip().lower() in {"1", "true", "sim", "yes"}


class TeeOutput:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, mensagem):
        for stream in self.streams:
            stream.write(mensagem)
            stream.flush()

    def flush(self):
        for stream in self.streams:
            stream.flush()


def configurar_log():
    ARQUIVO_LOG.parent.mkdir(parents=True, exist_ok=True)
    log_estava_vazio = not ARQUIVO_LOG.exists() or ARQUIVO_LOG.stat().st_size == 0
    arquivo_log = open(ARQUIVO_LOG, "a", encoding="utf-8")
    stdout_original = sys.stdout
    stderr_original = sys.stderr

    if log_estava_vazio:
        arquivo_log.write("Log iniciado.\n")
        arquivo_log.flush()

    sys.stdout = TeeOutput(stdout_original, arquivo_log)
    sys.stderr = TeeOutput(stderr_original, arquivo_log)
    return arquivo_log, stdout_original, stderr_original


def reiniciar_emails_processados():
    if ARQUIVO_PROCESSADOS.exists():
        ARQUIVO_PROCESSADOS.unlink()
    ARQUIVO_PROCESSADOS.touch()
    print(f"Arquivo {ARQUIVO_PROCESSADOS} recriado vazio.")


def carregar_emails_processados():
    if not ARQUIVO_PROCESSADOS.exists():
        return set()

    with open(ARQUIVO_PROCESSADOS, "r", encoding="utf-8") as arquivo:
        return {
            linha.strip().lower()
            for linha in arquivo
            if linha.strip() and not linha.strip().startswith("#")
        }


def registrar_email_processado(email):
    if not email:
        return

    with open(ARQUIVO_PROCESSADOS, "a", encoding="utf-8") as arquivo:
        arquivo.write(f"{email.strip().lower()}\n")


def switch_to_internal_frame(driver, retries=5):
    """Entra no iframe que contem a tela de pre-admissoes."""
    for tentativa in range(retries):
        print(f"Tentativa {tentativa + 1} de encontrar o iframe interno...")

        try:
            if driver.find_elements(By.XPATH, "//*[contains(normalize-space(), 'Em assinatura')]"):
                print("Ja esta no contexto correto.")
                return True
        except Exception:
            pass

        driver.switch_to.default_content()
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"Encontrados {len(iframes)} iframes na pagina.")

        for indice in range(len(iframes)):
            try:
                driver.switch_to.default_content()
                driver.switch_to.frame(indice)
                if driver.find_elements(By.XPATH, "//*[contains(normalize-space(), 'Em assinatura')]"):
                    print(f"Iframe {indice} identificado como o frame de conteudo.")
                    return True
            except Exception:
                continue

        print("Iframe nao encontrado ainda. Aguardando 5 segundos...")
        time.sleep(5)

    return False


def fechar_popup_se_existir(driver, seletor, timeout=3, nome="Popup"):
    try:
        botao = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, seletor))
        )
        botao.click()
        print(f"{nome} fechado.")
        time.sleep(2)
        return True
    except Exception:
        return False


def clicar_elemento(driver, elemento, descricao, verificacao=None):
    """Tenta clicar em um elemento usando metodos complementares."""
    tentativas = [
        ("coordenada", lambda: ActionChains(driver).move_to_element(elemento).pause(0.2).click().perform()),
        ("click direto", lambda: elemento.click()),
        ("JavaScript click", lambda: driver.execute_script("arguments[0].click();", elemento)),
        (
            "eventos de mouse",
            lambda: driver.execute_script(
                """
                const el = arguments[0];
                const rect = el.getBoundingClientRect();
                const opts = {
                    bubbles: true,
                    cancelable: true,
                    view: window,
                    clientX: rect.left + rect.width / 2,
                    clientY: rect.top + rect.height / 2
                };
                ['mouseover', 'mousedown', 'mouseup', 'click'].forEach((type) => {
                    el.dispatchEvent(new MouseEvent(type, opts));
                });
                """,
                elemento,
            ),
        ),
        ("ENTER", lambda: elemento.send_keys(Keys.ENTER)),
    ]

    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento)
        time.sleep(1)
    except Exception:
        pass

    for nome, acao in tentativas:
        try:
            print(f"Tentando {descricao} com {nome}...")
            acao()
            time.sleep(2)
            if verificacao is None or verificacao():
                return True
            print(f"{nome} executado, mas a verificacao esperada ainda nao apareceu.")
        except Exception as erro:
            print(f"Falhou {nome}: {erro}")

    return False


def clicar_aba_em_assinatura(driver):
    seletores = [
        ("link da aba", By.XPATH, "//li[@role='presentation'][.//span[contains(normalize-space(), 'Em assinatura')]]//a[@role='tab']"),
        ("span da aba", By.XPATH, "//span[contains(normalize-space(), 'Em assinatura')]"),
        ("qualquer tab", By.XPATH, "//*[@role='tab' and contains(normalize-space(), 'Em assinatura')]"),
    ]

    for descricao, by, seletor in seletores:
        elementos = driver.find_elements(by, seletor)
        print(f"Seletor aba '{descricao}' encontrou {len(elementos)} elemento(s).")
        for elemento in elementos:
            try:
                if elemento.is_displayed() and clicar_elemento(driver, elemento, f"aba Em assinatura ({descricao})"):
                    time.sleep(5)
                    return True
            except Exception as erro:
                print(f"Falhou ao clicar aba com '{descricao}': {erro}")

    return False


def aguardar_lista_em_assinatura(driver, timeout=60):
    print("Aguardando lista da aba 'Em assinatura' carregar...")
    fim = time.time() + timeout

    while time.time() < fim:
        usuarios = obter_usuarios_acoes_lista(driver, imprimir=False)
        if usuarios:
            obter_usuarios_acoes_lista(driver, imprimir=True)
            return True

        sinais = driver.find_elements(By.CSS_SELECTOR, "div[id^='pre-admission-list.component'], s-employee-data, .person-secondary-info")
        if sinais:
            obter_usuarios_acoes_lista(driver, imprimir=True)
            return True

        time.sleep(3)

    obter_usuarios_acoes_lista(driver, imprimir=True)
    return False


def menu_visivel(driver, texto):
    itens = driver.find_elements(
        By.XPATH,
        f"//span[contains(@class, 'ui-menuitem-text') and normalize-space()='{texto}']",
    )
    return any(item.is_displayed() for item in itens)


def clicar_item_menu(driver, texto, timeout=60):
    print(f"Aguardando item '{texto}' aparecer...")
    xpath = (
        "//a[contains(@class, 'ui-menuitem-link') and "
        f".//span[contains(@class, 'ui-menuitem-text') and normalize-space()='{texto}']]"
    )
    item = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
    if clicar_elemento(driver, item, f"item {texto}"):
        print(f"Item '{texto}' clicado.")
        return True
    raise Exception(f"Nao foi possivel clicar no item '{texto}'.")


def clicar_ver_detalhes(driver, timeout=60):
    print("Aguardando botao 'Ver detalhes' aparecer...")
    seletores = [
        ("texto", By.XPATH, "//button[.//span[contains(@class, 's-button-text') and normalize-space()='Ver detalhes']]"),
        ("classe secondary", By.XPATH, "//button[contains(@class, 's-button-priority-secondary') and .//span[normalize-space()='Ver detalhes']]"),
    ]

    fim = time.time() + timeout
    while time.time() < fim:
        for descricao, by, seletor in seletores:
            for botao in driver.find_elements(by, seletor):
                try:
                    if not botao.is_displayed() or not botao.is_enabled():
                        continue
                    estado = driver.execute_script(
                        """
                        const rect = arguments[0].getBoundingClientRect();
                        return {
                            width: rect.width,
                            height: rect.height,
                            disabled: arguments[0].disabled,
                            ariaDisabled: arguments[0].getAttribute('aria-disabled'),
                            classes: arguments[0].className || ''
                        };
                        """,
                        botao,
                    )
                    if (
                        estado["width"] <= 0
                        or estado["height"] <= 0
                        or estado["disabled"]
                        or estado["ariaDisabled"] == "true"
                        or "ui-state-disabled" in estado["classes"]
                    ):
                        continue
                    if clicar_elemento(driver, botao, f"botao Ver detalhes ({descricao})"):
                        print("Botao 'Ver detalhes' clicado.")
                        return True
                except Exception as erro:
                    print(f"Falha ao tentar Ver detalhes com '{descricao}': {erro}")
        time.sleep(2)

    raise Exception("Nao foi possivel clicar no botao 'Ver detalhes'.")


def clicar_documentos_enviados(driver, timeout=60):
    print("Aguardando aba 'Documentos enviados' aparecer...")
    seletores = [
        ("role tab", By.XPATH, "//a[@role='tab' and .//span[contains(@class, 'ui-tabview-title') and normalize-space()='Documentos enviados']]"),
        ("span da aba", By.XPATH, "//span[contains(@class, 'ui-tabview-title') and normalize-space()='Documentos enviados']"),
    ]

    fim = time.time() + timeout
    while time.time() < fim:
        for descricao, by, seletor in seletores:
            for aba in driver.find_elements(by, seletor):
                try:
                    if aba.is_displayed() and aba.is_enabled():
                        if clicar_elemento(driver, aba, f"aba Documentos enviados ({descricao})"):
                            print("Aba 'Documentos enviados' clicada.")
                            return True
                except Exception as erro:
                    print(f"Falha ao tentar Documentos enviados com '{descricao}': {erro}")
        time.sleep(2)

    raise Exception("Nao foi possivel clicar na aba 'Documentos enviados'.")


def selecionar_100_registros(driver, timeout=30):
    print("Selecionando 100 registros por pagina...")
    fim = time.time() + timeout

    while time.time() < fim:
        gatilhos = driver.find_elements(
            By.CSS_SELECTOR,
            "p-paginator p-dropdown .ui-dropdown-trigger, p-paginator .ui-dropdown-trigger",
        )
        print(f"Dropdown de registros encontrou {len(gatilhos)} gatilho(s).")
        for gatilho in gatilhos:
            try:
                if not gatilho.is_displayed() or not gatilho.is_enabled():
                    continue
                if not clicar_elemento(driver, gatilho, "dropdown registros por pagina"):
                    continue

                opcao_100 = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            "//li[@role='option' and (@aria-label='100' or .//span[normalize-space()='100'])]",
                        )
                    )
                )
                if clicar_elemento(driver, opcao_100, "opcao 100 registros"):
                    print("Opcao '100' selecionada.")
                    time.sleep(5)
                    return True
            except Exception as erro:
                print(f"Falha ao selecionar 100 registros: {erro}")

        time.sleep(2)

    print("Nao foi possivel selecionar 100 registros dentro do timeout.")
    return False


def clicar_acoes_documentos(driver, timeout=60):
    print("Aguardando botao 'Acoes' do documento com status 'Em assinatura' aparecer...")

    fim = time.time() + timeout
    while time.time() < fim:
        documentos = driver.execute_script(
            """
            const normalizar = (texto) => (texto || '')
                .normalize('NFD')
                .replace(/[\\u0300-\\u036f]/g, '')
                .trim()
                .toLowerCase();

            return Array.from(document.querySelectorAll("p-treetable tbody.ui-treetable-tbody > tr"))
                .map((linha, indice) => {
                    const celulas = Array.from(linha.querySelectorAll(":scope > td"));
                    const status = Array.from(linha.querySelectorAll("s-badge span"))
                        .map((span) => (span.innerText || span.textContent || '').trim())
                        .find(Boolean) || '';
                    const botao = linha.querySelector("button[id^='btn-actions-pre-admission-documents'][stieredmenu]");
                    return {
                        indice,
                        titulo: (celulas[0]?.innerText || '').trim(),
                        status,
                        statusNormalizado: normalizar(status),
                        botao,
                        temBotao: Boolean(botao),
                    };
                })
                .filter((documento) => documento.status || documento.temBotao);
            """
        )
        pendentes = [
            documento
            for documento in documentos
            if documento["statusNormalizado"] == "em assinatura" and documento["temBotao"]
        ]

        print(f"Documentos encontrados: {len(documentos)}")
        for documento in documentos:
            print(
                "Documento: "
                f"indice={documento.get('indice')}, "
                f"titulo='{documento.get('titulo')}', "
                f"status='{documento.get('status')}', "
                f"tem_botao_acoes={documento.get('temBotao')}"
            )
        print(f"Documentos com status 'Em assinatura' e botao Acoes: {len(pendentes)}")

        for documento in pendentes:
            try:
                botao = documento["botao"]
                print(
                    "Documento selecionado para reenviar: "
                    f"indice={documento.get('indice')}, "
                    f"status='{documento.get('status')}', "
                    f"titulo='{documento.get('titulo')}', "
                    f"botao_id='{botao.get_attribute('id')}'"
                )
                if botao.is_displayed() and botao.is_enabled():
                    if clicar_elemento(driver, botao, "botao Acoes do documento Em assinatura"):
                        print("Botao 'Acoes' do documento em assinatura clicado.")
                        return True
            except Exception as erro:
                print(f"Falha ao tentar Acoes do documento em assinatura: {erro}")
        time.sleep(2)

    raise Exception("Nao foi possivel clicar no botao 'Acoes' de documento com status 'Em assinatura'.")


def confirmar_reenviar(driver, timeout=60):
    print("Aguardando confirmacao 'Reenviar' aparecer...")
    seletores = [
        ("confirmdialog accept", By.CSS_SELECTOR, "button.ui-confirmdialog-acceptbutton"),
        ("botao confirmar reenviar", By.XPATH, "//button[contains(@class, 'ui-confirmdialog-acceptbutton') and .//span[normalize-space()='Reenviar']]"),
        ("texto Reenviar", By.XPATH, "//button[.//span[contains(@class, 'ui-button-text') and normalize-space()='Reenviar']]"),
    ]

    fim = time.time() + timeout
    while time.time() < fim:
        for descricao, by, seletor in seletores:
            for botao in driver.find_elements(by, seletor):
                try:
                    texto = botao.text.strip()
                    if "Reenviar" not in texto:
                        continue
                    if botao.is_displayed() and botao.is_enabled():
                        if clicar_elemento(driver, botao, f"confirmacao Reenviar ({descricao})"):
                            print("Confirmacao 'Reenviar' clicada.")
                            return True
                except Exception as erro:
                    print(f"Falha ao tentar confirmacao Reenviar com '{descricao}': {erro}")
        time.sleep(2)

    raise Exception("Nao foi possivel confirmar 'Reenviar'.")


def obter_usuarios_acoes_lista(driver, imprimir=True):
    resultado = driver.execute_script(
        """
        const normalizar = (texto) => (texto || '')
            .normalize('NFD')
            .replace(/[\\u0300-\\u036f]/g, '')
            .trim()
            .toLowerCase();

        const listas = Array.from(document.querySelectorAll("div[id^='pre-admission-list.component']"))
            .filter((elemento) => elemento.querySelector("p-table.sds-list"));

        const lista = listas
            .map((elemento) => {
                const linhas = Array.from(elemento.querySelectorAll(".ui-table-unfrozen-view .ui-table-scrollable-body tbody.ui-table-tbody > tr"))
                    .filter((linha) => linha.querySelector("s-employee-data"));
                const botoes = Array.from(elemento.querySelectorAll("button[stieredmenu]"))
                    .filter((botao) => normalizar(botao.innerText || botao.textContent) === 'acoes');
                return { elemento, linhas, botoes, total: Math.max(linhas.length, botoes.length) };
            })
            .sort((a, b) => b.total - a.total)[0];

        if (!lista) {
            return { usuarios: [], botoes: [] };
        }

        const botaoAcoesVisivel = (botao) => {
            const rect = botao.getBoundingClientRect();
            return normalizar(botao.innerText || botao.textContent) === 'acoes'
                && rect.width > 0
                && rect.height > 0
                && !botao.disabled
                && botao.getAttribute('aria-disabled') !== 'true';
        };

        const todosBotoesAcoes = Array.from(lista.elemento.querySelectorAll("button[stieredmenu]"))
            .filter(botaoAcoesVisivel);

        const obterBotaoAcoesDaLinha = (linha) => {
            const botaoNaLinha = Array.from(linha.querySelectorAll("button[stieredmenu]"))
                .find(botaoAcoesVisivel);
            if (botaoNaLinha) {
                return botaoNaLinha;
            }

            const rectLinha = linha.getBoundingClientRect();
            return todosBotoesAcoes.find((botao) => {
                const rectBotao = botao.getBoundingClientRect();
                const centroBotao = rectBotao.top + rectBotao.height / 2;
                return centroBotao >= rectLinha.top - 3 && centroBotao <= rectLinha.bottom + 3;
            }) || null;
        };

        const usuarios = lista.linhas.map((linha, indice) => {
            const usuario = linha.querySelector("s-employee-data");
            const nome = (usuario.querySelector("[data-testid^='pre-admission-list-employee-name-']")?.innerText || '').trim();
            const infos = Array.from(usuario.querySelectorAll(".person-secondary-info span")).map((span) => (span.innerText || span.textContent || '').trim());
            const email = infos.find((texto) => texto.includes('@')) || '';
            const botao = obterBotaoAcoesDaLinha(linha);
            return {
                indice,
                nome,
                email,
                temBotaoAcoes: !!botao,
                botaoId: botao ? (botao.id || '') : '',
                botaoTexto: botao ? ((botao.innerText || botao.textContent || '').trim()) : ''
            };
        }).filter((usuario) => usuario.email || usuario.nome);

        const botoes = todosBotoesAcoes.map((botao) => {
            return {
                id: botao.id || '',
                texto: (botao.innerText || botao.textContent || '').trim()
            };
        });

        return { usuarios, botoes };
        """
    )

    usuarios = resultado.get("usuarios", [])
    botoes = resultado.get("botoes", [])

    if imprimir:
        print(f"Total de usuarios pela classe 'person-secondary-info': {len(usuarios)}")
        print(f"Total de botoes 'Acoes' na tela atual: {len(botoes)}")
        for indice, usuario in enumerate(usuarios, start=1):
            print(
                f"  Usuario {indice}: indice={usuario.get('indice')}, "
                f"nome='{usuario.get('nome')}', email='{usuario.get('email')}', "
                f"id_botao='{usuario.get('botaoId')}', texto_botao='{usuario.get('botaoTexto')}', "
                f"temBotaoAcoes={usuario.get('temBotaoAcoes')}"
            )

    return usuarios


def clicar_acoes_usuario(driver, usuario):
    email = (usuario.get("email") or "").strip().lower()
    nome = (usuario.get("nome") or "").strip()
    indice = usuario.get("indice")
    print(f"Procurando botao 'Acoes' do usuario: {nome} <{email}>...")
    botao = driver.execute_script(
        """
        const alvo = arguments[0];
        const normalizar = (texto) => (texto || '')
            .normalize('NFD')
            .replace(/[\\u0300-\\u036f]/g, '')
            .trim()
            .toLowerCase();

        const listas = Array.from(document.querySelectorAll("div[id^='pre-admission-list.component']"))
            .filter((elemento) => elemento.querySelector("p-table.sds-list"));
        const lista = listas
            .map((elemento) => {
                const linhas = Array.from(elemento.querySelectorAll(".ui-table-unfrozen-view .ui-table-scrollable-body tbody.ui-table-tbody > tr"))
                    .filter((linha) => linha.querySelector("s-employee-data"));
                const botoes = Array.from(elemento.querySelectorAll("button[stieredmenu]"))
                    .filter((botao) => normalizar(botao.innerText || botao.textContent) === 'acoes');
                return { elemento, total: Math.max(linhas.length, botoes.length) };
            })
            .sort((a, b) => b.total - a.total)[0];

        if (!lista) {
            return null;
        }

        const linhas = Array.from(lista.elemento.querySelectorAll(".ui-table-unfrozen-view .ui-table-scrollable-body tbody.ui-table-tbody > tr"))
            .filter((linha) => linha.querySelector("s-employee-data"));
        const botaoAcoesVisivel = (botao) => {
            const rect = botao.getBoundingClientRect();
            return normalizar(botao.innerText || botao.textContent) === 'acoes'
                && rect.width > 0
                && rect.height > 0
                && !botao.disabled
                && botao.getAttribute('aria-disabled') !== 'true';
        };

        const todosBotoesAcoes = Array.from(lista.elemento.querySelectorAll("button[stieredmenu]"))
            .filter(botaoAcoesVisivel);

        const linhaEncontrada = linhas
            .map((linha, indice) => {
                const dadosUsuario = linha.querySelector("s-employee-data");
                const nome = (dadosUsuario.querySelector("[data-testid^='pre-admission-list-employee-name-']")?.innerText || '').trim();
                const infos = Array.from(dadosUsuario.querySelectorAll(".person-secondary-info span"))
                    .map((span) => (span.innerText || span.textContent || '').trim());
                const email = infos.find((texto) => texto.includes('@')) || '';
                return { linha, indice, nome, email };
            })
            .find((item) => {
                if (alvo.email && item.email && normalizar(item.email) === normalizar(alvo.email)) {
                    return true;
                }
                if (alvo.nome && item.nome && normalizar(item.nome) === normalizar(alvo.nome)) {
                    return true;
                }
                return Number.isInteger(alvo.indice) && item.indice === alvo.indice;
            });

        if (!linhaEncontrada) {
            return null;
        }

        const botaoNaLinha = Array.from(linhaEncontrada.linha.querySelectorAll("button[stieredmenu]"))
            .find(botaoAcoesVisivel);
        if (botaoNaLinha) {
            return botaoNaLinha;
        }

        const rectLinha = linhaEncontrada.linha.getBoundingClientRect();
        return todosBotoesAcoes.find((botao) => {
            const rectBotao = botao.getBoundingClientRect();
            const centroBotao = rectBotao.top + rectBotao.height / 2;
            return centroBotao >= rectLinha.top - 3 && centroBotao <= rectLinha.bottom + 3;
        }) || null;
        """,
        {"email": email, "nome": nome, "indice": indice},
    )
    if not botao:
        print(f"Nao encontrei botao Acoes para o usuario {nome} <{email}>.")
        return False

    print(
        "Candidato Acoes por usuario: "
        f"id='{botao.get_attribute('id')}', "
        f"class='{botao.get_attribute('class')}', "
        f"texto='{botao.text.strip().replace(chr(10), ' ')}'"
    )
    return clicar_elemento(driver, botao, f"botao Acoes do usuario {nome or indice}", lambda: menu_visivel(driver, "Detalhar"))


def processar_usuario_em_assinatura(driver, usuario, modo_teste=False):
    indice = usuario.get("indice")
    print(f"Processando usuario indice {indice}: {usuario.get('nome')} <{usuario.get('email')}>")

    if not clicar_acoes_usuario(driver, usuario):
        return False

    clicar_item_menu(driver, "Detalhar")
    clicar_ver_detalhes(driver)
    clicar_documentos_enviados(driver)
    time.sleep(3)
    clicar_acoes_documentos(driver)

    if modo_teste:
        if menu_visivel(driver, "Reenviar"):
            print("MODO TESTE: item 'Reenviar' apareceu. Nao vou clicar nem confirmar o reenvio.")
        else:
            print("MODO TESTE: botao Acoes do documento abriu, mas o item 'Reenviar' nao ficou visivel.")
        try:
            driver.switch_to.active_element.send_keys(Keys.ESCAPE)
        except Exception:
            pass
        time.sleep(2)
        return True

    clicar_item_menu(driver, "Reenviar")
    confirmar_reenviar(driver)
    time.sleep(8)
    return True


def navegar_ate_em_assinatura(driver, wait, primeira_vez=False):
    if primeira_vez:
        print("Iniciando navegacao nos menus...")
        menus = [
            ("Gestao de Pessoas | HCM", By.XPATH, "//*[starts-with(@id, 'menu-item-') and contains(normalize-space(), 'HCM')]"),
            ("Admissao Digital", By.ID, "apps-menu-item-9"),
            ("Pre-admissoes", By.ID, "apps-menu-item-3"),
        ]

        driver.switch_to.default_content()
        for nome, by, seletor in menus:
            print(f"Abrindo: {nome}")
            wait.until(EC.element_to_be_clickable((by, seletor))).click()
            time.sleep(3)

        print("Aguardando carregamento da aplicacao Pre-admissoes...")
        time.sleep(10)
        fechar_popup_se_existir(driver, "button.close-popup", timeout=10, nome="Popup de pre-admissoes")

    if not switch_to_internal_frame(driver):
        raise Exception("Nao foi possivel encontrar o iframe interno.")

    fechar_popup_se_existir(driver, "button.close-popup", timeout=5, nome="Popup pos-aba tipo 1")
    fechar_popup_se_existir(driver, ".ui-dialog-titlebar-close", timeout=2, nome="Popup pos-aba tipo 2")
    fechar_popup_se_existir(driver, "div.close-modal", timeout=2, nome="Popup pos-aba tipo 3")

    if not clicar_aba_em_assinatura(driver):
        print("Clique direto na aba falhou. Tentando fallback por teclado...")
        actions = ActionChains(driver)
        for _ in range(15):
            actions.send_keys(Keys.TAB)
        actions.send_keys(Keys.ENTER)
        actions.perform()
        time.sleep(5)

    fechar_popup_se_existir(driver, "button.close-popup", timeout=5, nome="Popup pos-aba tipo 1")
    fechar_popup_se_existir(driver, ".ui-dialog-titlebar-close", timeout=2, nome="Popup pos-aba tipo 2")
    fechar_popup_se_existir(driver, "div.close-modal", timeout=2, nome="Popup pos-aba tipo 3")
    selecionar_100_registros(driver)

    if not aguardar_lista_em_assinatura(driver):
        print("Lista da aba 'Em assinatura' nao carregou dentro do timeout.")


def main():
    arquivo_log, stdout_original, stderr_original = configurar_log()
    driver = None

    try:
        reiniciar_emails_processados()

        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--incognito")

        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 20)

        url = os.getenv("URL")
        usuario = os.getenv("USUARIO")
        senha = os.getenv("SENHA")
        if not all([url, usuario, senha]):
            print("Erro: Verifique as credenciais no arquivo credenciais.env")
            return

        print(f"Acessando: {url}")
        driver.get(url)
        time.sleep(2)

        wait.until(EC.element_to_be_clickable((By.ID, "username-input-field"))).send_keys(usuario)
        time.sleep(1)
        wait.until(EC.element_to_be_clickable((By.ID, "nextBtn"))).click()
        time.sleep(2)
        wait.until(EC.element_to_be_clickable((By.ID, "password-input-field"))).send_keys(senha)
        time.sleep(1)
        wait.until(EC.element_to_be_clickable((By.ID, "loginbtn"))).click()
        time.sleep(5)

        fechar_popup_se_existir(driver, "a.ui-dialog-titlebar-close", timeout=5, nome="Dialogo inicial")
        fechar_popup_se_existir(driver, "em.fas.fa-times", timeout=3, nome="Popup icone X")

        navegar_ate_em_assinatura(driver, wait, primeira_vez=True)

        total_processados = 0
        emails_processados = carregar_emails_processados()
        tentativas_sem_avanco = 0
        if MODO_TESTE:
            print("MODO TESTE ATIVO: o fluxo sera validado sem clicar em 'Reenviar'.")
        print(f"Emails ja registrados como processados: {len(emails_processados)}")

        while True:
            switch_to_internal_frame(driver)
            usuarios = obter_usuarios_acoes_lista(driver)
            usuarios_pendentes = [
                usuario
                for usuario in usuarios
                if usuario.get("email")
                and usuario.get("email").strip().lower() not in emails_processados
                and usuario.get("temBotaoAcoes")
            ]

            if not usuarios:
                print("Nenhum usuario encontrado na aba 'Em assinatura'.")
                break

            if not usuarios_pendentes:
                print("Nenhum usuario pendente nesta tela.")
                break

            usuario_atual = usuarios_pendentes[0]
            print(f"\n--- Ciclo {total_processados + 1}: {len(usuarios_pendentes)} usuario(s) pendente(s) nesta tela ---")
            processou = processar_usuario_em_assinatura(driver, usuario_atual, modo_teste=MODO_TESTE)

            if processou:
                email_normalizado = usuario_atual.get("email").strip().lower()
                emails_processados.add(email_normalizado)
                if not MODO_TESTE:
                    registrar_email_processado(email_normalizado)
                total_processados += 1
                tentativas_sem_avanco = 0
                if MODO_TESTE:
                    print("Teste do usuario concluido sem reenviar.")
                else:
                    print("Reenvio concluido.")
            else:
                tentativas_sem_avanco += 1
                print(f"Tentativa sem avanco {tentativas_sem_avanco}/3.")
                if tentativas_sem_avanco >= 3:
                    print("Encerrando para evitar loop sem progresso.")
                    break

            print("Atualizando a pagina e voltando para 'Em assinatura'...")
            driver.refresh()
            time.sleep(10)
            navegar_ate_em_assinatura(driver, wait, primeira_vez=False)

        print(f"\nTarefa finalizada! Total processado: {total_processados}")

    except Exception as erro:
        print(f"Erro Critico: {erro}")
    finally:
        if driver:
            driver.quit()
        sys.stdout = stdout_original
        sys.stderr = stderr_original
        arquivo_log.close()


if __name__ == "__main__":
    main()
