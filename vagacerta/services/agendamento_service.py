"""
Módulo de Serviço de Agendamentos e Motor de Autoliberação.
Orquestra as regras de negócio RN01, RN02 e RN04.
"""

from datetime import datetime, date, time
from typing import List, Optional, Dict, Any, Tuple
from vagacerta.dao.agendamento_dao import AgendamentoDAO
from vagacerta.dao.agenda_dao import AgendaDiariaDAO
from vagacerta.dao.usuario_dao import UsuarioDAO
from vagacerta.models.agendamento import Agendamento, ConsultaClinica, Exame, Vacinacao
from vagacerta.models.enums import StatusAgendamento, StatusHorario, TipoAgendamento


class AgendamentoService:
    """
    Camada de serviço responsável pelo fluxo de marcação, confirmação,
    cancelamento e pela rotina automatizada de autoliberação de horários (RN02).
    """

    def __init__(
        self,
        agendamento_dao: Optional[AgendamentoDAO] = None,
        agenda_dao: Optional[AgendaDiariaDAO] = None,
        usuario_dao: Optional[UsuarioDAO] = None,
    ):
        self.agendamento_dao = agendamento_dao or AgendamentoDAO()
        self.agenda_dao = agenda_dao or AgendaDiariaDAO()
        self.usuario_dao = usuario_dao or UsuarioDAO()

    def agendar_consulta(
        self,
        paciente_id: int,
        horario_id: int,
        motivo: str,
        retorno: bool = False,
    ) -> ConsultaClinica:
        """
        Realiza agendamento de consulta médica, validando a elegibilidade do paciente (RN03)
        e a disponibilidade atômica do horário (RN01).
        """
        self._validar_elegibilidade_paciente(paciente_id)
        consulta = ConsultaClinica(
            id=None,
            horario_id=horario_id,
            paciente_id=paciente_id,
            motivo=motivo,
            retorno=retorno,
        )
        return self.agendamento_dao.criar(consulta)

    def agendar_exame(
        self,
        paciente_id: int,
        horario_id: int,
        tipo_exame: str,
        orientacao_preparo: str,
    ) -> Exame:
        """Realiza agendamento de exame com preparo obrigatório (RN02)."""
        self._validar_elegibilidade_paciente(paciente_id)
        exame = Exame(
            id=None,
            horario_id=horario_id,
            paciente_id=paciente_id,
            tipo_exame=tipo_exame,
            orientacao_preparo=orientacao_preparo,
        )
        return self.agendamento_dao.criar(exame)

    def agendar_vacinacao(
        self,
        paciente_id: int,
        horario_id: int,
        imunobiologico: str,
        dose: str,
    ) -> Vacinacao:
        """Realiza agendamento de imunização (isenta de confirmação prévia - RN02)."""
        self._validar_elegibilidade_paciente(paciente_id)
        vacina = Vacinacao(
            id=None,
            horario_id=horario_id,
            paciente_id=paciente_id,
            imunobiologico=imunobiologico,
            dose=dose,
        )
        return self.agendamento_dao.criar(vacina)

    def confirmar_presenca(
        self, agendamento_id: int, momento_confirmacao: Optional[datetime] = None
    ) -> Agendamento:
        """
        Registra confirmação prévia obrigatória pelo paciente.
        Garante que a vaga não seja autoliberada pela regra de descarte (RN02).
        """
        agendamento = self.agendamento_dao.buscar_por_id(agendamento_id)
        if not agendamento:
            raise ValueError(f"Agendamento ID {agendamento_id} não encontrado.")

        agendamento.confirmar(momento_confirmacao)
        self.agendamento_dao.atualizar_status(
            agendamento.id, agendamento.status, agendamento.confirmado_em
        )
        return agendamento

    def cancelar_agendamento(self, agendamento_id: int) -> None:
        """
        RN01 - Libera imediatamente a vaga na grade e altera status para CANCELADO.
        """
        self.agendamento_dao.cancelar_e_liberar_vaga(agendamento_id)

    def executar_motor_autoliberacao(
        self, momento_referencia: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        RN02 - Motor de Autoliberação e Combate ao Absenteísmo:
        Varre agendamentos com status AGENDADO (não confirmados).
        Utiliza polimorfismo (janela_confirmacao_horas) para identificar vagas que
        estouraram o prazo limite sem confirmação.
        Libera o horário imediatamente na grade pública para reoferta à fila.
        """
        agora = momento_referencia or datetime.now()
        agendamentos_pendentes = self.agendamento_dao.listar_todos(
            status_filtro=StatusAgendamento.AGENDADO
        )
        vagas_recuperadas = []

        for ag in agendamentos_pendentes:
            detalhes = self.agendamento_dao.obter_detalhes_completos(ag.id)
            if not detalhes:
                continue

            data_atendimento = date.fromisoformat(detalhes["data_atendimento"])
            hora_inicio = time.fromisoformat(detalhes["hora_inicio"])

            # Verificação polimórfica da regra de descarte
            if ag.deve_ser_autoliberado(data_atendimento, hora_inicio, agora):
                # Executa a liberação imediata do horário (RN01 / RN02)
                self.agendamento_dao.cancelar_e_liberar_vaga(ag.id)

                vagas_recuperadas.append(
                    {
                        "agendamento_id": ag.id,
                        "tipo": ag.tipo().value,
                        "paciente": detalhes["nome_paciente"],
                        "profissional": detalhes["nome_profissional"],
                        "data": data_atendimento.isoformat(),
                        "horario": hora_inicio.strftime("%H:%M"),
                        "janela_exigida_horas": ag.janela_confirmacao_horas(),
                        "motivo_liberacao": (
                            f"Ausência de confirmação na janela de {ag.janela_confirmacao_horas()}h. "
                            f"Vaga liberada automaticamente para a fila pública."
                        ),
                    }
                )

        return vagas_recuperadas

    def _validar_elegibilidade_paciente(self, paciente_id: int) -> None:
        """RN03 - Validação de restrição por reincidência de faltas."""
        paciente = self.usuario_dao.buscar_paciente_por_id(paciente_id)
        if not paciente:
            raise ValueError(f"Paciente com ID {paciente_id} não cadastrado no sistema.")

        pode, motivo = paciente.pode_agendar_online()
        if not pode:
            raise PermissionError(motivo)
