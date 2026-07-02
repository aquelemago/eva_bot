"""
Servico do Windows para o Evabot.

Controla exclusivamente o ciclo de vida da automacao:
inicializacao, execucao e encerramento.

Uso:
    python windows_service.py install
    python windows_service.py start
    python windows_service.py stop
    python windows_service.py remove

Requer pywin32 instalado.
Funciona apenas em Windows.
"""
import threading
import sys

import win32serviceutil
import win32service
import win32event

from main import main, sinalizar_parada


class EvabotService(win32serviceutil.ServiceFramework):
    _svc_name_ = "Evabot"
    _svc_display_name_ = "Evabot - Automacao de Reenvio de Documentos"
    _svc_description_ = (
        "Automatiza o reenvio de documentos com status 'Em assinatura' "
        "no Senior X / HCM."
    )

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self._thread = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        sinalizar_parada()
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        self._thread = threading.Thread(target=main, daemon=True)
        self._thread.start()

        while True:
            if (
                win32event.WaitForSingleObject(self.hWaitStop, 5000)
                == win32event.WAIT_OBJECT_0
            ):
                break
            if not self._thread.is_alive():
                break

        if self._thread.is_alive():
            sinalizar_parada()
            self._thread.join(timeout=30)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.argv.extend(["install", "--start", "auto"])
    win32serviceutil.HandleCommandLine(EvabotService)
