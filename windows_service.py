"""
Servico do Windows para o Evabot.

Executa a automacao diariamente no horario configurado (padrao: 7:00).
Aguardando entre execucoes e responde ao sinal de parada do SCM.

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
from datetime import datetime, timedelta

import win32serviceutil
import win32service
import win32event

from main import main, sinalizar_parada


HORARIO_EXECUCAO = 7  # Executa diariamente as 07:00


def _proximo_horario(hora):
    agora = datetime.now()
    alvo = agora.replace(hour=hora, minute=0, second=0, microsecond=0)
    if alvo <= agora:
        alvo += timedelta(days=1)
    return alvo


class EvabotService(win32serviceutil.ServiceFramework):
    _svc_name_ = "Evabot"
    _svc_display_name_ = "Evabot - Automacao de Reenvio de Documentos"
    _svc_description_ = (
        "Automatiza o reenvio de documentos com status 'Em assinatura' "
        "no Senior X / HCM. Execucao diaria programada as 7:00."
    )

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        sinalizar_parada()
        win32event.SetEvent(self.hWaitStop)

    def _aguardar_proximo_horario(self):
        proximo = _proximo_horario(HORARIO_EXECUCAO)
        segundos = int((proximo - datetime.now()).total_seconds())
        while segundos > 0:
            intervalo = min(segundos, 30)
            if (
                win32event.WaitForSingleObject(self.hWaitStop, intervalo * 1000)
                == win32event.WAIT_OBJECT_0
            ):
                return False
            segundos = int((proximo - datetime.now()).total_seconds())
        return True

    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        while True:
            if (
                win32event.WaitForSingleObject(self.hWaitStop, 0)
                == win32event.WAIT_OBJECT_0
            ):
                break

            if not self._aguardar_proximo_horario():
                break

            thread = threading.Thread(target=main, daemon=True)
            thread.start()

            while thread.is_alive():
                if (
                    win32event.WaitForSingleObject(self.hWaitStop, 1000)
                    == win32event.WAIT_OBJECT_0
                ):
                    break
            if thread.is_alive():
                thread.join(timeout=30)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(
            "Uso: python windows_service.py install|start|stop|remove\n"
            "Exemplo: python windows_service.py install"
        )
    else:
        win32serviceutil.HandleCommandLine(EvabotService)
