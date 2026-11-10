"""
Módulo de Grade de Atendimento e Horários.
Demonstração do Pilar POO: COMPOSIÇÃO com ciclo de vida acoplado.

==============================================================================
JUSTIFICATIVA TÉCNICA E CONCEITUAL: POR QUE COMPOSIÇÃO E NÃO HERANÇA?
==============================================================================
1. Relação Semântica 'Tem-um' (Has-a) vs. 'É-um' (Is-a):
   - Um Horário NÃO É uma AgendaDiária. Um Horário É PARTE DE uma AgendaDiária.
   - Herança aqui violaria o Princípio de Substituição de Liskov (LSP), pois um
     Horário individual não pode substituir uma AgendaDiária completa.

2. Ciclo de Vida Acoplado (Composição Estrita):
   - Um Horário não possui sentido ou existência isolada sem uma AgendaDiária
     que define sua data, turno, unidade e profissional responsável.
   - Quando uma AgendaDiária é gerada, ela instancia e administra seus próprios
     horários; se uma agenda for excluída, todos os seus horários são excluídos
     em cascata (ON DELETE CASCADE no banco relacional).

3. Encapsulamento da Regra RN04:
   - A geração dinâmica dos horários é controlada pela AgendaDiaria, que itera
     o turno do profissional dividindo-o conforme a duração do procedimento.
==============================================================================
"""

from datetime import date, time, datetime, timedelta
from typing import List, Optional
from vagacerta.models.enums import StatusHorario


class Horario:
    """
    Representa uma fatia de tempo discreta dentro do turno de um profissional.
    É o componente contido dentro da composição de AgendaDiaria.
    """

    def __init__(
        self,
        id: Optional[int],
        agenda_id: int,
        hora_inicio: time | str,
        hora_fim: time | str,
        status: StatusHorario | str = StatusHorario.LIVRE,
    ):
        self.id = id
        self.agenda_id = agenda_id
        self.hora_inicio = (
            time.fromisoformat(hora_inicio)
            if isinstance(hora_inicio, str)
            else hora_inicio
        )
        self.hora_fim = (
            time.fromisoformat(hora_fim)
            if isinstance(hora_fim, str)
            else hora_fim
        )
        self.status = (
            StatusHorario(status) if isinstance(status, str) else status
        )

    def esta_livre(self) -> bool:
        """Indica se o horário pode receber nova reserva."""
        return self.status == StatusHorario.LIVRE

    def reservar(self) -> None:
        """RN01 - Ao ser reservado, sai da grade disponível."""
        if not self.esta_livre():
            raise ValueError(f"Horário ID {self.id} já se encontra {self.status.value}.")
        self.status = StatusHorario.RESERVADO

    def liberar(self) -> None:
        """RN01 - Ao ser cancelado ou liberado por descarte, retorna imediatamente."""
        self.status = StatusHorario.LIVRE

    def bloquear(self) -> None:
        """Bloqueia horário por motivos operacionais ou indisponibilidade."""
        self.status = StatusHorario.BLOQUEADO

    def duracao_minutos(self) -> int:
        """Calcula duração do horário em minutos."""
        dt_ini = datetime.combine(date.today(), self.hora_inicio)
        dt_fim = datetime.combine(date.today(), self.hora_fim)
        return int((dt_fim - dt_ini).total_seconds() / 60)

    def __repr__(self) -> str:
        return f"<Horario id={self.id} {self.hora_inicio.strftime('%H:%M')}-{self.hora_fim.strftime('%H:%M')} [{self.status.value}]>"


class AgendaDiaria:
    """
    Compositor: Contém e gerencia a coleção de Horarios para um profissional em determinada data.
    Implementa a parametrização dinâmica de grade (RN04).
    """

    def __init__(
        self,
        id: Optional[int],
        unidade_id: int,
        profissional_id: int,
        data_agenda: date | str,
        turno_inicio: time | str,
        turno_fim: time | str,
        bloqueada: bool = False,
        horarios: Optional[List[Horario]] = None,
    ):
        self.id = id
        self.unidade_id = unidade_id
        self.profissional_id = profissional_id
        self.data = (
            date.fromisoformat(data_agenda)
            if isinstance(data_agenda, str)
            else data_agenda
        )
        self.turno_inicio = (
            time.fromisoformat(turno_inicio)
            if isinstance(turno_inicio, str)
            else turno_inicio
        )
        self.turno_fim = (
            time.fromisoformat(turno_fim)
            if isinstance(turno_fim, str)
            else turno_fim
        )
        self.bloqueada = bloqueada

        # COMPOSIÇÃO: A AgendaDiaria possui uma lista de Horarios
        self.horarios: List[Horario] = horarios if horarios is not None else []

    def adicionar_horario(self, horario: Horario) -> None:
        """Insere um novo horário na composição da agenda."""
        self.horarios.append(horario)

    def gerar_horarios(self, duracao_minutos: int) -> List[Horario]:
        """
        RN04 - Geração Dinâmica da Grade:
        Parametriza os horários diários a partir do turno do profissional
        e da duração padrão exigida para o tipo de atendimento.
        """
        if duracao_minutos <= 0:
            raise ValueError("Duração do atendimento deve ser positiva.")

        self.horarios = []
        dt_atual = datetime.combine(self.data, self.turno_inicio)
        dt_fim = datetime.combine(self.data, self.turno_fim)
        passo = timedelta(minutes=duracao_minutos)

        while dt_atual + passo <= dt_fim:
            hora_ini = dt_atual.time()
            hora_fim = (dt_atual + passo).time()
            novo_horario = Horario(
                id=None,
                agenda_id=self.id or 0,
                hora_inicio=hora_ini,
                hora_fim=hora_fim,
                status=StatusHorario.LIVRE,
            )
            self.horarios.append(novo_horario)
            dt_atual += passo

        return self.horarios

    def horarios_livres(self) -> List[Horario]:
        """Filtra horários disponíveis para agendamento."""
        return [h for h in self.horarios if h.esta_livre()]

    def total_horarios(self) -> int:
        return len(self.horarios)

    def taxa_ocupacao(self) -> float:
        """Calcula o percentual de ocupação da grade diária."""
        if not self.horarios:
            return 0.0
        ocupados = sum(1 for h in self.horarios if h.status == StatusHorario.RESERVADO)
        return round((ocupados / len(self.horarios)) * 100, 1)

    def __repr__(self) -> str:
        return (
            f"<AgendaDiaria id={self.id} prof_id={self.profissional_id} "
            f"data={self.data} total_horarios={len(self.horarios)} ocupacao={self.taxa_ocupacao()}%>"
        )
