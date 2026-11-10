"""
Módulo DAO para Gestão e Persistência de Agenda Diária e Horários.
Demonstração da persistência da relação de COMPOSIÇÃO 1:N com transações atômicas.
"""

from datetime import date
from typing import List, Optional
from vagacerta.database import db
from vagacerta.models.agenda import AgendaDiaria, Horario
from vagacerta.models.enums import StatusHorario


class AgendaDiariaDAO:
    """
    Data Access Object para Agendas Diárias e Horários associados.
    Persiste a Agenda e seus Horários em cascata na mesma transação.
    """

    def __init__(self, database_manager=db):
        self.db = database_manager

    def criar(self, agenda: AgendaDiaria) -> AgendaDiaria:
        """
        Cria a AgendaDiária e persiste todos os Horários que a compõem.
        Operação atômica em transação.
        """
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO agenda_diaria (unidade_id, profissional_id, data, turno_inicio, turno_fim, bloqueada)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    agenda.unidade_id,
                    agenda.profissional_id,
                    agenda.data.isoformat(),
                    agenda.turno_inicio.isoformat(),
                    agenda.turno_fim.isoformat(),
                    1 if agenda.bloqueada else 0,
                ),
            )
            agenda.id = cursor.lastrowid

            # Persistência da composição: Cada Horario é salvo referenciando a Agenda pai
            for h in agenda.horarios:
                cursor.execute(
                    """
                    INSERT INTO horario (agenda_id, hora_inicio, hora_fim, status)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        agenda.id,
                        h.hora_inicio.isoformat(),
                        h.hora_fim.isoformat(),
                        h.status.value,
                    ),
                )
                h.id = cursor.lastrowid
                h.agenda_id = agenda.id

            return agenda

    def buscar_por_id(self, agenda_id: int) -> Optional[AgendaDiaria]:
        """Busca agenda pelo ID e carrega todos os seus horários compostos."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, unidade_id, profissional_id, data, turno_inicio, turno_fim, bloqueada
                FROM agenda_diaria
                WHERE id = ?
                """,
                (agenda_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None

            agenda = AgendaDiaria(
                id=row["id"],
                unidade_id=row["unidade_id"],
                profissional_id=row["profissional_id"],
                data_agenda=row["data"],
                turno_inicio=row["turno_inicio"],
                turno_fim=row["turno_fim"],
                bloqueada=bool(row["bloqueada"]),
            )

            # Carrega horários associados (Composição)
            cursor.execute(
                """
                SELECT id, agenda_id, hora_inicio, hora_fim, status
                FROM horario
                WHERE agenda_id = ?
                ORDER BY hora_inicio ASC
                """,
                (agenda_id,),
            )
            for h_row in cursor.fetchall():
                agenda.adicionar_horario(
                    Horario(
                        id=h_row["id"],
                        agenda_id=h_row["agenda_id"],
                        hora_inicio=h_row["hora_inicio"],
                        hora_fim=h_row["hora_fim"],
                        status=h_row["status"],
                    )
                )

            return agenda
        finally:
            conn.close()

    def buscar_por_profissional_e_data(
        self, profissional_id: int, data_agenda: date
    ) -> Optional[AgendaDiaria]:
        """Busca a grade de determinado profissional em um dia específico."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id FROM agenda_diaria
                WHERE profissional_id = ? AND data = ?
                """,
                (profissional_id, data_agenda.isoformat()),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return self.buscar_por_id(row["id"])
        finally:
            conn.close()

    def listar_por_unidade(self, unidade_id: int) -> List[AgendaDiaria]:
        """Lista todas as agendas de uma UBS."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM agenda_diaria WHERE unidade_id = ? ORDER BY data DESC",
                (unidade_id,),
            )
            agenda_ids = [row["id"] for row in cursor.fetchall()]
        finally:
            conn.close()

        agendas = []
        for aid in agenda_ids:
            agenda = self.buscar_por_id(aid)
            if agenda:
                agendas.append(agenda)
        return agendas

    def atualizar_status_horario(self, horario_id: int, novo_status: StatusHorario) -> None:
        """RN01 - Atualiza atomicamente a disponibilidade do horário."""
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE horario SET status = ? WHERE id = ?",
                (novo_status.value, horario_id),
            )

    def buscar_horario_por_id(self, horario_id: int) -> Optional[Horario]:
        """Busca um horário individual pelo seu ID."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, agenda_id, hora_inicio, hora_fim, status FROM horario WHERE id = ?",
                (horario_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return Horario(
                id=row["id"],
                agenda_id=row["agenda_id"],
                hora_inicio=row["hora_inicio"],
                hora_fim=row["hora_fim"],
                status=row["status"],
            )
        finally:
            conn.close()

    def obter_data_do_horario(self, horario_id: int) -> Optional[date]:
        """Helper para recuperar a data da agenda a qual pertence o horário."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT a.data
                FROM horario h
                INNER JOIN agenda_diaria a ON h.agenda_id = a.id
                WHERE h.id = ?
                """,
                (horario_id,),
            )
            row = cursor.fetchone()
            return date.fromisoformat(row["data"]) if row else None
        finally:
            conn.close()

    def excluir(self, agenda_id: int) -> bool:
        """Exclui a agenda diária e todos os seus horários (ON DELETE CASCADE)."""
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM agenda_diaria WHERE id = ?", (agenda_id,))
            return cursor.rowcount > 0
