"""
Pacote de Modelos de Domínio do VagaCerta.
Exporta as classes fundamentais de entidades, abstrações e enumerações.
"""

from vagacerta.models.enums import (
    PerfilAcesso,
    StatusHorario,
    StatusAgendamento,
    TipoAgendamento,
)
from vagacerta.models.usuario import (
    Usuario,
    Paciente,
    ProfissionalSaude,
    GestorUnidade,
)
from vagacerta.models.unidade import UnidadeSaude
from vagacerta.models.agenda import Horario, AgendaDiaria
from vagacerta.models.agendamento import (
    Agendamento,
    ConsultaClinica,
    Exame,
    Vacinacao,
)

__all__ = [
    "PerfilAcesso",
    "StatusHorario",
    "StatusAgendamento",
    "TipoAgendamento",
    "Usuario",
    "Paciente",
    "ProfissionalSaude",
    "GestorUnidade",
    "UnidadeSaude",
    "Horario",
    "AgendaDiaria",
    "Agendamento",
    "ConsultaClinica",
    "Exame",
    "Vacinacao",
]
