"""
Módulo de Agendamentos e Especializações de Atendimento.
Demonstração dos Pilares POO: HERANÇA e POLIMORFISMO.

==============================================================================
HIERARQUIA POLIMÓRFICA:
  Agendamento (Classe Base Abstrata)
    ├── ConsultaClinica (Janela: 24h, Duração: 20min, Preparo: Não)
    ├── Exame           (Janela: 48h, Duração: 30min, Preparo: Sim - RN02)
    └── Vacinacao       (Janela: 0h [Isenta], Duração: 5min, Preparo: Não)
==============================================================================
"""

from abc import ABC, abstractmethod
from datetime import datetime, date, time, timedelta
from typing import Optional
from vagacerta.models.enums import StatusAgendamento, TipoAgendamento
from vagacerta.config import (
    JANELA_CONFIRMACAO_CONSULTA_HORAS,
    JANELA_CONFIRMACAO_EXAME_HORAS,
    JANELA_CONFIRMACAO_VACINA_HORAS,
    DURACAO_CONSULTA_MINUTOS,
    DURACAO_EXAME_MINUTOS,
    DURACAO_VACINA_MINUTOS,
)


class Agendamento(ABC):
    """
    Classe base abstrata para todos os agendamentos na rede pública.
    Controla o ciclo de vida da reserva e define os métodos polimórficos obrigatórios.
    """

    def __init__(
        self,
        id: Optional[int],
        horario_id: int,
        paciente_id: int,
        status: StatusAgendamento | str = StatusAgendamento.AGENDADO,
        confirmado_em: Optional[datetime | str] = None,
        data_criacao: Optional[datetime | str] = None,
    ):
        self.id = id
        self.horario_id = horario_id
        self.paciente_id = paciente_id
        self.status = (
            StatusAgendamento(status) if isinstance(status, str) else status
        )
        self.confirmado_em = (
            datetime.fromisoformat(confirmado_em)
            if isinstance(confirmado_em, str)
            else confirmado_em
        )
        self.data_criacao = (
            datetime.fromisoformat(data_criacao)
            if isinstance(data_criacao, str)
            else (data_criacao or datetime.now())
        )

    # -------------------------------------------------------------------------
    # MÉTODOS ABSTRATOS (POLIMORFISMO OBRIGATÓRIO)
    # -------------------------------------------------------------------------
    @abstractmethod
    def tipo(self) -> TipoAgendamento:
        """Identificador do tipo do agendamento."""
        pass

    @abstractmethod
    def janela_confirmacao_horas(self) -> int:
        """
        RN02 - Janela Diferenciada de Confirmação Prévia.
        Define quantas horas antes do atendimento a confirmação torna-se obrigatória.
        """
        pass

    @abstractmethod
    def duracao_minutos(self) -> int:
        """
        RN04 - Duração padrão do procedimento para geração da grade horária.
        """
        pass

    @abstractmethod
    def exige_preparo(self) -> bool:
        """Indica se o paciente necessita de orientações prévias (jejum, medicação)."""
        pass

    @abstractmethod
    def gerar_instrucoes_atendimento(self) -> str:
        """Gera roteiro e orientações polimórficas direcionadas ao cidadão."""
        pass

    # -------------------------------------------------------------------------
    # MÉTODOS CONCRETOS DE CICLO DE VIDA E REGRAS DE NEGÓCIO
    # -------------------------------------------------------------------------
    def confirmar(self, data_hora: Optional[datetime] = None) -> None:
        """Registra a confirmação ativa pelo paciente dentro do prazo."""
        if self.status != StatusAgendamento.AGENDADO:
            raise ValueError(f"Não é possível confirmar agendamento com status '{self.status.value}'.")
        self.status = StatusAgendamento.CONFIRMADO
        self.confirmado_em = data_hora or datetime.now()

    def cancelar(self) -> None:
        """Cancela agendamento, permitindo que a vaga seja liberada imediatamente."""
        if self.status in (StatusAgendamento.REALIZADO, StatusAgendamento.CANCELADO):
            raise ValueError(f"Agendamento já finalizado com status '{self.status.value}'.")
        self.status = StatusAgendamento.CANCELADO

    def registrar_falta(self) -> None:
        """Marca o agendamento como falta do paciente (absenteísmo)."""
        self.status = StatusAgendamento.FALTA

    def marcar_realizado(self) -> None:
        """Registra atendimento concluído pelo profissional de saúde."""
        self.status = StatusAgendamento.REALIZADO

    def deve_ser_autoliberado(
        self,
        data_atendimento: date,
        hora_atendimento: time,
        agora: Optional[datetime] = None,
    ) -> bool:
        """
        RN02 - Regra de Descarte e Autoliberação:
        Se a confirmação é obrigatória (janela > 0) e o paciente NÃO confirmou
        antes da janela estipulada, a vaga caduca e deve ser liberada automaticamente.
        """
        # Se já estiver confirmado, realizado ou cancelado, não descarta
        if self.status != StatusAgendamento.AGENDADO:
            return False

        janela_horas = self.janela_confirmacao_horas()
        if janela_horas <= 0:
            # Procedimentos isentos de confirmação (ex: Vacinação) nunca são autoliberados
            return False

        momento_atendimento = datetime.combine(data_atendimento, hora_atendimento)
        limite_confirmacao = momento_atendimento - timedelta(hours=janela_horas)
        momento_atual = agora or datetime.now()

        # Se já passamos do prazo limite sem confirmação, ativa autoliberação
        return momento_atual >= limite_confirmacao

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} id={self.id} tipo={self.tipo().value} "
            f"paciente_id={self.paciente_id} horario_id={self.horario_id} status={self.status.value}>"
        )


class ConsultaClinica(Agendamento):
    """
    Especialização para consultas médicas gerais ou especializadas.
    - Janela de confirmação: 24h
    - Duração padrão: 20 min
    """

    def __init__(
        self,
        id: Optional[int],
        horario_id: int,
        paciente_id: int,
        motivo: str,
        retorno: bool = False,
        status: StatusAgendamento | str = StatusAgendamento.AGENDADO,
        confirmado_em: Optional[datetime | str] = None,
        data_criacao: Optional[datetime | str] = None,
    ):
        super().__init__(id, horario_id, paciente_id, status, confirmado_em, data_criacao)
        self.motivo = motivo.strip()
        self.retorno = bool(retorno)

    def tipo(self) -> TipoAgendamento:
        return TipoAgendamento.CONSULTA

    def janela_confirmacao_horas(self) -> int:
        return JANELA_CONFIRMACAO_CONSULTA_HORAS

    def duracao_minutos(self) -> int:
        return DURACAO_CONSULTA_MINUTOS

    def exige_preparo(self) -> bool:
        return False

    def gerar_instrucoes_atendimento(self) -> str:
        tipo_str = "Consulta de Retorno" if self.retorno else "Primeira Consulta"
        return (
            f"[{tipo_str}] Compareça com 15 minutos de antecedência munido de documento com foto, "
            f"Cartão do SUS e exames anteriores pertinentes. Motivo informado: '{self.motivo}'. "
            f"Confirmação obrigatória até 24h antes para não perder a vaga."
        )


class Exame(Agendamento):
    """
    Especialização para exames diagnósticos e laboratoriais.
    - Janela de confirmação: 48h (devido à logística de reagentes e preparo prévio)
    - Duração padrão: 30 min
    - Exige preparo: Sim
    """

    def __init__(
        self,
        id: Optional[int],
        horario_id: int,
        paciente_id: int,
        tipo_exame: str,
        orientacao_preparo: str,
        status: StatusAgendamento | str = StatusAgendamento.AGENDADO,
        confirmado_em: Optional[datetime | str] = None,
        data_criacao: Optional[datetime | str] = None,
    ):
        super().__init__(id, horario_id, paciente_id, status, confirmado_em, data_criacao)
        self.tipo_exame = tipo_exame.strip()
        self.orientacao_preparo = orientacao_preparo.strip()

    def tipo(self) -> TipoAgendamento:
        return TipoAgendamento.EXAME

    def janela_confirmacao_horas(self) -> int:
        return JANELA_CONFIRMACAO_EXAME_HORAS

    def duracao_minutos(self) -> int:
        return DURACAO_EXAME_MINUTOS

    def exige_preparo(self) -> bool:
        return True

    def gerar_instrucoes_atendimento(self) -> str:
        return (
            f"[Exame: {self.tipo_exame}] ATENÇÃO AO PREPARO OBRIGATÓRIO: {self.orientacao_preparo}. "
            f"Devido à complexidade do procedimento e insumos, confirme sua presença com pelo menos 48h de antecedência. "
            f"Caso contrário, a vaga será autoliberada."
        )


class Vacinacao(Agendamento):
    """
    Especialização para imunização e vacinação básica do calendário de saúde.
    - Janela de confirmação: 0h (isenta de confirmação prévia - regra de descarte não se aplica)
    - Duração padrão: 5 min
    - Exige preparo: Não
    """

    def __init__(
        self,
        id: Optional[int],
        horario_id: int,
        paciente_id: int,
        imunobiologico: str,
        dose: str,
        status: StatusAgendamento | str = StatusAgendamento.AGENDADO,
        confirmado_em: Optional[datetime | str] = None,
        data_criacao: Optional[datetime | str] = None,
    ):
        super().__init__(id, horario_id, paciente_id, status, confirmado_em, data_criacao)
        self.imunobiologico = imunobiologico.strip()
        self.dose = dose.strip()

    def tipo(self) -> TipoAgendamento:
        return TipoAgendamento.VACINA

    def janela_confirmacao_horas(self) -> int:
        return JANELA_CONFIRMACAO_VACINA_HORAS

    def duracao_minutos(self) -> int:
        return DURACAO_VACINA_MINUTOS

    def exige_preparo(self) -> bool:
        return False

    def gerar_instrucoes_atendimento(self) -> str:
        return (
            f"[Imunização: {self.imunobiologico} - {self.dose}] "
            f"Apresente a caderneta de vacinação física ou digital e documento de identidade. "
            f"Atendimento rápido na sala de vacina (5 min). Isento de confirmação prévia."
        )
