"""
Servico do Windows para o Evabot.

Executa a automacao imediatamente ao iniciar e repete
diariamente as 07:00. Responde ao sinal de parada do SCM.

Uso:
    python windows_service.py install
    python windows_service.py start
    python windows_service.py stop
    python windows_service.py remove
    python windows_service.py debug

Requer pywin32 instalado.
Funciona apenas em Windows.
"""
import threading
import time
import sys
from datetime import datetime, timedelta

import win32serviceutil
import win32service
import win32event

HORARIO_EXECUCAO = 7


class EvabotService(win32serviceutil.ServiceFramework):
    _svc_name_ = "Evabot"
    _svc_display_name_ = "Evabot - Automacao de Reenvio de Documentos"
    _svc_description_ = (
        "Automatiza o reenvio de documentos com status 'Em assinatura' "
        "no Senior X / HCM. Execucao diaria as 7:00."
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

    def _executar_bot(self):
        from main import main, sinalizar_parada
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
        alvo = agora.replace(hour=HORARIO_EXECUCAO, minute=0, second=0, microsecond=0)
        if alvo <= agora:
            alvo += timedelta(days=1)
        while True:
            segundos = int((alvo - datetime.now()).total_seconds())
            if segundos <= 0:
                return True
            if self._parada_solicitada():
                return False
            time.sleep(min(segundos, 5))

    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING, waitHint=60000)
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        self._executar_bot()
        while self._running:
            if not self._aguardar_proximo_horario():
                break
            self._executar_bot()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(
            "Uso: python windows_service.py install|start|stop|remove|debug\n"
            "Exemplo: python windows_service.py install"
        )
    else:
        win32serviceutil.HandleCommandLine(EvabotService)
