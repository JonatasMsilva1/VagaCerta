"""
Pacote DAO (Data Access Object) do VagaCerta.
Camada responsável pelo isolamento e operações de persistência em banco relacional.
"""

from vagacerta.dao.usuario_dao import UsuarioDAO
from vagacerta.dao.unidade_dao import UnidadeSaudeDAO
from vagacerta.dao.agenda_dao import AgendaDiariaDAO
from vagacerta.dao.agendamento_dao import AgendamentoDAO

__all__ = [
    "UsuarioDAO",
    "UnidadeSaudeDAO",
    "AgendaDiariaDAO",
    "AgendamentoDAO",
]
