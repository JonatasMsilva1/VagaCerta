"""
Enumerações utilizadas pelo domínio do VagaCerta.
Garante consistência e tipagem forte em toda a aplicação.
"""

from enum import Enum


class PerfilAcesso(str, Enum):
    """Perfis de acesso de usuários no sistema."""
    PACIENTE = "PACIENTE"
    PROFISSIONAL = "PROFISSIONAL"
    GESTOR = "GESTOR"


class StatusHorario(str, Enum):
    """Status de disponibilidade do horário na grade diária."""
    LIVRE = "LIVRE"
    RESERVADO = "RESERVADO"
    BLOQUEADO = "BLOQUEADO"


class StatusAgendamento(str, Enum):
    """Ciclo de vida de um agendamento."""
    AGENDADO = "AGENDADO"
    CONFIRMADO = "CONFIRMADO"
    REALIZADO = "REALIZADO"
    FALTA = "FALTA"
    CANCELADO = "CANCELADO"


class TipoAgendamento(str, Enum):
    """Tipos de procedimentos com comportamentos polimórficos distintos."""
    CONSULTA = "CONSULTA"
    EXAME = "EXAME"
    VACINA = "VACINA"
