#/
import os
import sys
import time
import threading
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException, InvalidSessionIdException


_SCRIPT_DIR = Path(__file__).parent.resolve()

load_dotenv(_SCRIPT_DIR / "credenciais.env")

ARQUIVO_PROCESSADOS = _SCRIPT_DIR / "emails_processados.txt"
ARQUIVO_LOG = _SCRIPT_DIR / "logs" / "bot.log"
MODO_TESTE = os.getenv("MODO_TESTE", os.getenv("TEST_MODE", "")).strip().lower() in {"1", "true", "sim", "yes"}

_stop_event = threading.Event()


def sinalizar_parada():
    """Sinaliza para o bot interromper a execucao de forma graciosa."""
    _stop_event.set()


def parada_sinalizada():
    """Retorna True se a parada foi solicitada."""
    return _stop_event.is_set()


class TeeOutput:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, mensagem):
        if not mensagem:
            return
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        partes = mensagem.split("\n")
        for i, parte in enumerate(partes):
            if parte:
                for stream in self.streams:
                    try:
                        stream.write(f"[{timestamp}] {parte}")
                    except Exception:
                        pass
            if i < len(partes) - 1:
                for stream in self.streams:
                    try:
                        stream.write("\n")
                        stream.flush()
                    except Exception:
                        pass

    def flush(self):
        for stream in self.streams:
            stream.flush()


def configurar_log():
    ARQUIVO_LOG.parent.mkdir(parents=True, exist_ok=True)

    if ARQUIVO_LOG.exists():
        idade = datetime.now() - datetime.fromtimestamp(ARQUIVO_LOG.stat().st_mtime)
        if idade.days >= 7:
            arquivo_velho = ARQUIVO_LOG.with_suffix(f".{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
            ARQUIVO_LOG.rename(arquivo_velho)
            print(f"Log antigo movido para {arquivo_velho.name}")

    arquivo_log = open(ARQUIVO_LOG, "a", encoding="utf-8")
    stdout_original = sys.stdout
    stderr_original = sys.stderr

    sep = "=" * 70
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cabecalho = f"{sep}\n  Execucao iniciada em {agora}\n{sep}\n"
    arquivo_log.write(cabecalho)
    arquivo_log.flush()
    print(cabecalho, end="")

    sys.stdout = TeeOutput(stdout_original, arquivo_log)
    sys.stderr = TeeOutput(stderr_original, arquivo_log)
    return arquivo_log, stdout_original, stderr_original


def reiniciar_emails_processados():
    if ARQUIVO_PROCESSADOS.exists():
        ARQUIVO_PROCESSADOS.unlink()
    ARQUIVO_PROCESSADOS.touch()
    print(f"Arquivo {ARQUIVO_PROCESSADOS} recriado vazio.")


def verificar_sessao_selenium(driver):
    """Verifica se a sessao Selenium ainda esta ativa."""
    try:
        _ = driver.title
        return True
    except (WebDriverException, InvalidSessionIdException, ConnectionRefusedError, OSError):
        return False


def criar_driver_chrome():
    """Cria uma nova instancia do Chrome WebDriver com configuracoes estaveis."""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--keep-alive-timeout=300")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-features=TranslateUI,Translate")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    chrome_options.add_argument("--disable-hang-monitor")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-domain-reliability")
    chrome_options.add_argument("--disable-component-update")
    chrome_options.add_argument("--disable-breakpad")
    chrome_options.add_argument("--metrics-recording-only")
    chrome_options.add_argument("--disable-sync")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(60)
    driver.implicitly_wait(10)
    return driver


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
        except Exception as erro:
            print(f"Falhou {nome}: {erro}")

    return False


def clicar_aba_em_assinatura(driver, timeout=30):
    seletores = [
        ("link da aba", By.XPATH, "//li[@role='presentation'][.//span[contains(normalize-space(), 'Em assinatura')]]//a[@role='tab']"),
        ("qualquer tab", By.XPATH, "//*[@role='tab' and contains(normalize-space(), 'Em assinatura')]"),
        ("span da aba", By.XPATH, "//span[contains(normalize-space(), 'Em assinatura')]"),
    ]

    fim = time.time() + timeout
    while time.time() < fim:
        for descricao, by, seletor in seletores:
            elementos = driver.find_elements(by, seletor)
            if elementos:
                print(f"Seletor aba '{descricao}' encontrou {len(elementos)} elemento(s).")
            for elemento in elementos:
                try:
                    if elemento.is_displayed() and clicar_elemento(driver, elemento, f"aba Em assinatura ({descricao})"):
                        time.sleep(5)
                        return True
                except Exception as erro:
                    print(f"Falhou ao clicar aba com '{descricao}': {erro}")
        time.sleep(1)

    print("Nao foi possivel clicar na aba 'Em assinatura' dentro do timeout.")
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
        ("ui-tabview-header", By.XPATH, "//a[contains(@class, 'ui-tabview-header') and .//span[normalize-space()='Documentos enviados']]"),
        ("role tab", By.XPATH, "//a[@role='tab' and .//span[normalize-space()='Documentos enviados']]"),
        ("span direto", By.XPATH, "//span[normalize-space()='Documentos enviados']"),
        ("li header", By.XPATH, "//li[contains(@class, 'ui-tabview-header') and .//span[normalize-space()='Documentos enviados']]"),
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
                    print(f"Falha ao tentar aba Documentos enviados com '{descricao}': {erro}")
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

            const painelDocumentos = document.querySelector(
                'div[role="tabpanel"]:not(.ui-helper-hidden), ' +
                '.ui-tabview-panel:not(.ui-helper-hidden)'
            );
            const tabelaDocumentos = painelDocumentos
                ? painelDocumentos.querySelector('p-table, .ui-table, table')
                : null;
            const linhas = tabelaDocumentos
                ? Array.from(tabelaDocumentos.querySelectorAll('tbody.ui-table-tbody > tr, tbody > tr'))
                : Array.from(document.querySelectorAll('p-table tbody.ui-table-tbody > tr, table tbody > tr'));

            return linhas
                .map((linha, indice) => {
                    const celulas = Array.from(linha.querySelectorAll(":scope > td"));
                    const status = Array.from(linha.querySelectorAll("s-badge span"))
                        .map((span) => (span.innerText || span.textContent || '').trim())
                        .find(Boolean) || '';
                    const botao = linha.querySelector("button[stieredmenu]");
                    const textoBotao = botao
                        ? normalizar(botao.innerText || botao.textContent)
                        : '';
                    return {
                        indice,
                        titulo: (celulas[0]?.innerText || '').trim(),
                        status,
                        statusNormalizado: normalizar(status),
                        botao,
                        temBotao: Boolean(botao) && textoBotao === 'acoes',
                        botaoTexto: textoBotao,
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
        status_encontrados = sorted({
            documento.get("status") or "Sem status"
            for documento in documentos
        })

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

        if documentos and not pendentes:
            status_log = ", ".join(status_encontrados)
            status_normalizados = [
                documento.get("statusNormalizado")
                for documento in documentos
                if documento.get("statusNormalizado")
            ]
            todos_expirados = all(
                status == "expirado"
                for status in status_normalizados
            )
            if status_normalizados and todos_expirados:
                print("[SKIP] Usuario ignorado: todos os documentos encontrados estao Expirados.")
                return "skip_expirado"

            print(
                "[SKIP] Nenhum documento em assinatura encontrado para este usuario. "
                f"Status encontrados: {status_log}."
            )
            return "skip_sem_documento_acionavel"

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
                        return "processar"
            except Exception as erro:
                print(f"Falha ao tentar Acoes do documento em assinatura: {erro}")
        time.sleep(2)

    print("[SKIP] Nenhum documento em assinatura encontrado para este usuario dentro do timeout.")
    return "skip_sem_documento_acionavel"


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
    status_documentos = clicar_acoes_documentos(driver)
    if status_documentos != "processar":
        return status_documentos

    clicar_item_menu(driver, "Reenviar")
    confirmar_reenviar(driver)
    time.sleep(8)
    return "processado"


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
            for tentativa in range(5):
                if not verificar_sessao_selenium(driver):
                    raise WebDriverException("Sessao Selenium encerrada. Browser pode ter travado.")
                try:
                    wait.until(EC.element_to_be_clickable((by, seletor))).click()
                    break
                except Exception as e:
                    if tentativa < 4:
                        tempo_espera = 8 + (tentativa * 2)
                        print(f"Tentativa {tentativa+1} falhou para '{nome}': {e}. Retentando em {tempo_espera}s...")
                        time.sleep(tempo_espera)
                        driver.switch_to.default_content()
                    else:
                        raise
            time.sleep(5)

        print("Aguardando carregamento da aplicacao Pre-admissoes...")
        time.sleep(15)
        fechar_popup_se_existir(driver, "button.close-popup", timeout=10, nome="Popup de pre-admissoes")

    if not switch_to_internal_frame(driver):
        raise Exception("Nao foi possivel encontrar o iframe interno.")

    fechar_popup_se_existir(driver, "button.close-popup", timeout=5, nome="Popup pos-aba tipo 1")
    fechar_popup_se_existir(driver, ".ui-dialog-titlebar-close", timeout=2, nome="Popup pos-aba tipo 2")
    fechar_popup_se_existir(driver, "div.close-modal", timeout=2, nome="Popup pos-aba tipo 3")

    if not clicar_aba_em_assinatura(driver):
        print("Nao foi possivel clicar na aba 'Em assinatura'. Verifique se o nome da aba mudou.")

    fechar_popup_se_existir(driver, "button.close-popup", timeout=5, nome="Popup pos-aba tipo 1")
    fechar_popup_se_existir(driver, ".ui-dialog-titlebar-close", timeout=2, nome="Popup pos-aba tipo 2")
    fechar_popup_se_existir(driver, "div.close-modal", timeout=2, nome="Popup pos-aba tipo 3")
    selecionar_100_registros(driver)

    if not aguardar_lista_em_assinatura(driver):
        print("Lista da aba 'Em assinatura' nao carregou dentro do timeout.")


def main():
    try:
        with open(ARQUIVO_LOG, "a", encoding="utf-8") as _diag:
            _diag.write(f"[{datetime.now().strftime('%H:%M:%S')}] main() iniciada\n")
            _diag.flush()
    except Exception:
        pass

    arquivo_log, stdout_original, stderr_original = configurar_log()
    driver = None

    try:
        reiniciar_emails_processados()

        driver = criar_driver_chrome()
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
        print(f"Emails ja registrados como processados: {len(emails_processados)}")

        while True:
            if parada_sinalizada():
                print("Parada solicitada. Encerrando execucao...")
                break

            if not verificar_sessao_selenium(driver):
                print("Sessao Selenium perdida. Tentando reconectar...")
                try:
                    driver.quit()
                except Exception:
                    pass
                driver = criar_driver_chrome()
                wait = WebDriverWait(driver, 20)
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
                navegar_ate_em_assinatura(driver, wait, primeira_vez=True)
                continue

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
            resultado_processamento = processar_usuario_em_assinatura(driver, usuario_atual, modo_teste=MODO_TESTE)

            if resultado_processamento in {"processado", "skip_expirado", "skip_sem_documento_acionavel"}:
                email_normalizado = usuario_atual.get("email").strip().lower()
                emails_processados.add(email_normalizado)
                if resultado_processamento == "processado" and not MODO_TESTE:
                    registrar_email_processado(email_normalizado)
                tentativas_sem_avanco = 0
                if resultado_processamento == "skip_expirado":
                    print("Usuario ignorado nesta execucao por possuir somente documentos expirados.")
                elif resultado_processamento == "skip_sem_documento_acionavel":
                    print("Usuario ignorado nesta execucao por nao possuir documento em assinatura acionavel.")
                else:
                    total_processados += 1
                    print("Reenvio concluido.")
            else:
                tentativas_sem_avanco += 1
                print(f"Tentativa sem avanco {tentativas_sem_avanco}/3.")
                if tentativas_sem_avanco >= 3:
                    print("Encerrando para evitar loop sem progresso.")
                    break

            print("Atualizando a pagina e voltando para 'Em assinatura'...")
            if verificar_sessao_selenium(driver):
                driver.refresh()
                time.sleep(10)
                navegar_ate_em_assinatura(driver, wait, primeira_vez=False)
            else:
                print("Sessao perdida apos processamento. Reiniciando browser...")
                break

        print(f"\nTarefa finalizada! Total processado: {total_processados}")

    except BaseException as erro:
        import traceback
        trace = traceback.format_exc()
        try:
            with open(ARQUIVO_LOG, "a", encoding="utf-8") as f:
                f.write(f"\n  ERRO: {erro}\n{trace}\n")
                f.flush()
        except Exception:
            pass
    finally:
        if driver:
            driver.quit()
        sep = "=" * 70
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rodape = f"\n{sep}\n  Execucao finalizada em {agora}\n{sep}\n"
        arquivo_log.write(rodape)
        arquivo_log.flush()
        sys.stdout = stdout_original
        sys.stderr = stderr_original
        arquivo_log.close()


if __name__ == "__main__":
    main()
