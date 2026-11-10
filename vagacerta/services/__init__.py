"""
Pacote de Serviços do VagaCerta.
Orquestra as regras de negócio, motor de autoliberação, absenteísmo e relatórios analíticos.
"""

from vagacerta.services.agendamento_service import AgendamentoService
from vagacerta.services.absenteismo_service import AbsenteismoService
from vagacerta.services.relatorios_service import RelatoriosService

__all__ = [
    "AgendamentoService",
    "AbsenteismoService",
    "RelatoriosService",
]
