"""
Módulo de Serviço para Controle de Absenteísmo e Acolhimento Presencial (RN03).
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from vagacerta.dao.agendamento_dao import AgendamentoDAO
from vagacerta.dao.usuario_dao import UsuarioDAO
from vagacerta.config import LIMITE_FALTAS_BLOQUEIO


class AbsenteismoService:
    """
    Controla o ciclo de faltas, aplicação de bloqueio por reincidência
    e justificativas autorizadas por gestores no setor de acolhimento.
    """

    def __init__(
        self,
        agendamento_dao: Optional[AgendamentoDAO] = None,
        usuario_dao: Optional[UsuarioDAO] = None,
    ):
        self.agendamento_dao = agendamento_dao or AgendamentoDAO()
        self.usuario_dao = usuario_dao or UsuarioDAO()

    def registrar_falta(
        self, agendamento_id: int, data_falta: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Registra a falta do paciente a uma consulta marcada.
        Aplica a restrição da RN03 caso atinja o limite de faltas.
        """
        agendamento = self.agendamento_dao.buscar_por_id(agendamento_id)
        if not agendamento:
            raise ValueError(f"Agendamento {agendamento_id} não encontrado.")

        self.agendamento_dao.registrar_falta_paciente(agendamento_id, data_falta)
        paciente = self.usuario_dao.buscar_paciente_por_id(agendamento.paciente_id)

        bloqueado = paciente.esta_bloqueado()
        return {
            "agendamento_id": agendamento_id,
            "paciente_id": paciente.id,
            "paciente_nome": paciente.nome,
            "total_faltas_nao_justificadas": paciente.faltas_nao_justificadas,
            "status_bloqueio_online": bloqueado,
            "aviso": (
                "BLOQUEIO ATIVADO (RN03): Paciente atingiu o limite de faltas. "
                "Agendamento remoto suspenso até comparecimento ao acolhimento presencial."
                if bloqueado
                else f"Falta registrada com sucesso. Total acumulado: {paciente.faltas_nao_justificadas}/{LIMITE_FALTAS_BLOQUEIO}."
            ),
        }

    def acolher_e_justificar_falta(
        self, registro_falta_id: int, motivo_justificativa: str, gestor_id: int
    ) -> Dict[str, Any]:
        """
        Abona uma falta através do atendimento presencial no setor de acolhimento.
        Reabilita o agendamento remoto se o total de faltas ficar abaixo do teto.
        """
        gestor = self.usuario_dao.buscar_gestor_por_id(gestor_id)
        if not gestor:
            raise PermissionError("Apenas gestores da unidade possuem permissão para abonar faltas.")

        self.agendamento_dao.justificar_falta(registro_falta_id, motivo_justificativa, gestor_id)

        return {
            "registro_falta_id": registro_falta_id,
            "gestor_responsavel": gestor.nome,
            "motivo_justificativa": motivo_justificativa,
            "sucesso": True,
            "mensagem": "Falta abonada com sucesso no acolhimento da UBS.",
        }

    def obter_extrato_paciente(self, paciente_id: int) -> Dict[str, Any]:
        """Retorna histórico completo de assiduidade de um paciente."""
        paciente = self.usuario_dao.buscar_paciente_por_id(paciente_id)
        if not paciente:
            raise ValueError(f"Paciente {paciente_id} não encontrado.")

        faltas = self.agendamento_dao.listar_faltas_paciente(paciente_id)
        pode_agendar, motivo_bloqueio = paciente.pode_agendar_online()

        return {
            "paciente_id": paciente.id,
            "nome": paciente.nome,
            "cartao_sus": paciente.cartao_sus,
            "faltas_nao_justificadas": paciente.faltas_nao_justificadas,
            "pode_agendar_online": pode_agendar,
            "motivo_status": motivo_bloqueio,
            "historico_faltas": faltas,
        }
