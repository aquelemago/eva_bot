"""
Servico do Windows para o Evabot.

Executa a automacao imediatamente ao iniciar e repete
diariamente no horario configurado. Responde ao sinal de parada do SCM.

Uso:
    python windows_service.py install
    python windows_service.py start
    python windows_service.py stop
    python windows_service.py remove
    python windows_service.py debug

Variaveis de ambiente:
    HORARIO_EXECUCAO   Horario da execucao diaria (formato HH ou HH:MM). Padrao: 7:00.
    Exemplos (PowerShell):
        $env:HORARIO_EXECUCAO = "14"; python windows_service.py debug
        $env:HORARIO_EXECUCAO = "8:30"; python windows_service.py debug

Requer pywin32 instalado.
Funciona apenas em Windows.
"""
import math
import os
import threading
import time
import sys
from datetime import datetime, timedelta
from pathlib import Path

_SCRIPT_DIR = Path(__file__).parent.resolve()
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from dotenv import load_dotenv
import win32serviceutil  # type: ignore
import win32service  # type: ignore
import win32event  # type: ignore

load_dotenv(_SCRIPT_DIR / "credenciais.env")

_horario_raw = os.getenv("HORARIO_EXECUCAO", "7:00")
if ":" in _horario_raw:
    HORARIO_EXECUCAO_HORA, HORARIO_EXECUCAO_MIN = int(_horario_raw.split(":")[0]), int(_horario_raw.split(":")[1])
else:
    HORARIO_EXECUCAO_HORA, HORARIO_EXECUCAO_MIN = int(_horario_raw), 0


class EvabotService(win32serviceutil.ServiceFramework):
    _svc_name_ = "Evabot"
    _svc_display_name_ = "Evabot - Automacao de Reenvio de Documentos"
    _svc_description_ = (
        "Automatiza o reenvio de documentos com status 'Em assinatura' "
        f"no Senior X / HCM. Execucao diaria as {HORARIO_EXECUCAO_HORA:02d}:{HORARIO_EXECUCAO_MIN:02d}."
    )

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self._running = True

    def SvcStop(self):
        from main import sinalizar_parada
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self._running = False
        sinalizar_parada()
        win32event.SetEvent(self.hWaitStop)

    def _parada_solicitada(self):
        if not self._running:
            return True
        if win32event.WaitForSingleObject(self.hWaitStop, 0) == win32event.WAIT_OBJECT_0:
            return True
        return False

    def _log_servico(self, msg):
        log_path = _SCRIPT_DIR / "logs" / "bot.log"
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
                f.flush()
        except Exception:
            pass

    def _executar_bot(self):
        try:
            from main import main, sinalizar_parada
        except Exception as e:
            self._log_servico(f"ERRO ao importar main: {e}")
            return

        thread = threading.Thread(target=main, daemon=True)
        thread.start()
        while thread.is_alive():
            if self._parada_solicitada():
                sinalizar_parada()
                break
            thread.join(timeout=2)
        if thread.is_alive():
            thread.join(timeout=30)

    def _aguardar_proximo_horario(self):
        agora = datetime.now()
        alvo = agora.replace(hour=HORARIO_EXECUCAO_HORA, minute=HORARIO_EXECUCAO_MIN, second=0, microsecond=0)
        if alvo <= agora:
            alvo += timedelta(days=1)
        while True:
            segundos = math.ceil((alvo - datetime.now()).total_seconds())
            if segundos <= 0:
                return True
            if self._parada_solicitada():
                return False
            time.sleep(min(segundos, 5))

    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING, waitHint=60000)
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        self._log_servico(f"Servico iniciado. Horario: {HORARIO_EXECUCAO_HORA:02d}:{HORARIO_EXECUCAO_MIN:02d}")
        try:
            self._executar_bot()
            while self._running:
                if not self._aguardar_proximo_horario():
                    break
                self._executar_bot()
        except Exception as e:
            self._log_servico(f"ERRO no SvcDoRun: {e}")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(
            "Uso: python windows_service.py install|start|stop|remove|debug\n"
            "Exemplo: python windows_service.py install"
        )
    else:
        win32serviceutil.HandleCommandLine(EvabotService)
