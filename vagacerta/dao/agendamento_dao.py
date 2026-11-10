"""
Módulo DAO para Gestão e Persistência de Agendamentos Polimórficos.
Mapeia a hierarquia Agendamento -> (ConsultaClinica, Exame, Vacinacao)
em tabelas relacionais separadas com chaves conjuntas (PF), garantindo
a RN01 (Exclusividade de Horário) e atomicidade transacional.
"""

from datetime import datetime, date
from typing import List, Optional, Tuple, Dict, Any
from vagacerta.database import db
from vagacerta.models.agendamento import (
    Agendamento,
    ConsultaClinica,
    Exame,
    Vacinacao,
)
from vagacerta.models.enums import StatusAgendamento, StatusHorario, TipoAgendamento


class AgendamentoDAO:
    """
    Data Access Object para Agendamentos e suas especializações.
    Garante integridade referencial, bloqueio atômico de horários e persistência polimórfica.
    """

    def __init__(self, database_manager=db):
        self.db = database_manager

    def criar(self, agendamento: Agendamento) -> Agendamento:
        """
        RN01 - Exclusividade de Horário:
        Reserva o horário e persiste o agendamento em transação atômica.
        A restrição UNIQUE(horario_id) no banco garante a integridade concorrente.
        """
        with self.db.transaction() as conn:
            cursor = conn.cursor()

            # 1. Verifica se o horário está realmente LIVRE
            cursor.execute("SELECT status FROM horario WHERE id = ?", (agendamento.horario_id,))
            h_row = cursor.fetchone()
            if not h_row:
                raise ValueError(f"Horário com ID {agendamento.horario_id} não existe.")
            if h_row["status"] != StatusHorario.LIVRE.value:
                raise ValueError(
                    f"Horário ID {agendamento.horario_id} indisponível (status atual: {h_row['status']})."
                )

            # 2. Insere na tabela base agendamento
            cursor.execute(
                """
                INSERT INTO agendamento (horario_id, paciente_id, tipo_agendamento, status, confirmado_em, data_criacao)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    agendamento.horario_id,
                    agendamento.paciente_id,
                    agendamento.tipo().value,
                    agendamento.status.value,
                    agendamento.confirmado_em.isoformat() if agendamento.confirmado_em else None,
                    agendamento.data_criacao.isoformat(),
                ),
            )
            agendamento.id = cursor.lastrowid

            # 3. Insere na tabela especializada correspondente (Herança Relacional - PF)
            if isinstance(agendamento, ConsultaClinica):
                cursor.execute(
                    """
                    INSERT INTO consulta_clinica (agendamento_id, motivo, retorno)
                    VALUES (?, ?, ?)
                    """,
                    (agendamento.id, agendamento.motivo, 1 if agendamento.retorno else 0),
                )
            elif isinstance(agendamento, Exame):
                cursor.execute(
                    """
                    INSERT INTO exame (agendamento_id, tipo_exame, orientacao_preparo)
                    VALUES (?, ?, ?)
                    """,
                    (agendamento.id, agendamento.tipo_exame, agendamento.orientacao_preparo),
                )
            elif isinstance(agendamento, Vacinacao):
                cursor.execute(
                    """
                    INSERT INTO vacinacao (agendamento_id, imunobiologico, dose)
                    VALUES (?, ?, ?)
                    """,
                    (agendamento.id, agendamento.imunobiologico, agendamento.dose),
                )
            else:
                raise TypeError(f"Tipo desconhecido de agendamento: {type(agendamento)}")

            # 4. Atualiza o status do horário para RESERVADO
            cursor.execute(
                "UPDATE horario SET status = ? WHERE id = ?",
                (StatusHorario.RESERVADO.value, agendamento.horario_id),
            )

            return agendamento

    def buscar_por_id(self, agendamento_id: int) -> Optional[Agendamento]:
        """
        Reconstrói polimorficamente o objeto concreto (ConsultaClinica, Exame, Vacinacao)
        a partir da tabela base e sua respectiva especialização.
        """
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, horario_id, paciente_id, tipo_agendamento, status, confirmado_em, data_criacao
                FROM agendamento
                WHERE id = ?
                """,
                (agendamento_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None

            tipo = TipoAgendamento(row["tipo_agendamento"])
            base_kwargs = {
                "id": row["id"],
                "horario_id": row["horario_id"],
                "paciente_id": row["paciente_id"],
                "status": row["status"],
                "confirmado_em": row["confirmado_em"],
                "data_criacao": row["data_criacao"],
            }

            if tipo == TipoAgendamento.CONSULTA:
                cursor.execute(
                    "SELECT motivo, retorno FROM consulta_clinica WHERE agendamento_id = ?",
                    (agendamento_id,),
                )
                esp_row = cursor.fetchone()
                return ConsultaClinica(
                    **base_kwargs,
                    motivo=esp_row["motivo"],
                    retorno=bool(esp_row["retorno"]),
                )

            elif tipo == TipoAgendamento.EXAME:
                cursor.execute(
                    "SELECT tipo_exame, orientacao_preparo FROM exame WHERE agendamento_id = ?",
                    (agendamento_id,),
                )
                esp_row = cursor.fetchone()
                return Exame(
                    **base_kwargs,
                    tipo_exame=esp_row["tipo_exame"],
                    orientacao_preparo=esp_row["orientacao_preparo"],
                )

            elif tipo == TipoAgendamento.VACINA:
                cursor.execute(
                    "SELECT imunobiologico, dose FROM vacinacao WHERE agendamento_id = ?",
                    (agendamento_id,),
                )
                esp_row = cursor.fetchone()
                return Vacinacao(
                    **base_kwargs,
                    imunobiologico=esp_row["imunobiologico"],
                    dose=esp_row["dose"],
                )

            return None
        finally:
            conn.close()

    def buscar_por_horario_id(self, horario_id: int) -> Optional[Agendamento]:
        """Busca o agendamento associado a um determinado horário."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM agendamento WHERE horario_id = ?", (horario_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self.buscar_por_id(row["id"])
        finally:
            conn.close()

    def listar_por_paciente(self, paciente_id: int) -> List[Agendamento]:
        """Lista histórico completo de agendamentos de um paciente."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM agendamento WHERE paciente_id = ? ORDER BY id DESC",
                (paciente_id,),
            )
            ids = [row["id"] for row in cursor.fetchall()]
        finally:
            conn.close()

        lista = []
        for aid in ids:
            obj = self.buscar_por_id(aid)
            if obj:
                lista.append(obj)
        return lista

    def listar_todos(
        self, status_filtro: Optional[StatusAgendamento] = None
    ) -> List[Agendamento]:
        """Lista todos os agendamentos cadastrados, com filtro opcional por status."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            if status_filtro:
                cursor.execute(
                    "SELECT id FROM agendamento WHERE status = ? ORDER BY id DESC",
                    (status_filtro.value,),
                )
            else:
                cursor.execute("SELECT id FROM agendamento ORDER BY id DESC")
            ids = [row["id"] for row in cursor.fetchall()]
        finally:
            conn.close()

        lista = []
        for aid in ids:
            obj = self.buscar_por_id(aid)
            if obj:
                lista.append(obj)
        return lista

    def atualizar_status(
        self,
        agendamento_id: int,
        novo_status: StatusAgendamento,
        confirmado_em: Optional[datetime] = None,
    ) -> None:
        """Atualiza status e registro de confirmação."""
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE agendamento
                SET status = ?, confirmado_em = COALESCE(?, confirmado_em)
                WHERE id = ?
                """,
                (
                    novo_status.value,
                    confirmado_em.isoformat() if confirmado_em else None,
                    agendamento_id,
                ),
            )

    def cancelar_e_liberar_vaga(self, agendamento_id: int) -> None:
        """
        RN01 - Cancelamento e Liberação Imediata:
        Altera status do agendamento para CANCELADO e libera o horário correspondente.
        """
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT horario_id FROM agendamento WHERE id = ?", (agendamento_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Agendamento {agendamento_id} não encontrado.")

            horario_id = row["horario_id"]

            cursor.execute(
                "UPDATE agendamento SET status = ? WHERE id = ?",
                (StatusAgendamento.CANCELADO.value, agendamento_id),
            )
            cursor.execute(
                "UPDATE horario SET status = ? WHERE id = ?",
                (StatusHorario.LIVRE.value, horario_id),
            )

    def excluir(self, agendamento_id: int) -> bool:
        """
        Exclui permanentemente o registro de agendamento e libera o horário correspondente.
        """
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT horario_id FROM agendamento WHERE id = ?", (agendamento_id,))
            row = cursor.fetchone()
            if not row:
                return False

            horario_id = row["horario_id"]
            cursor.execute("DELETE FROM agendamento WHERE id = ?", (agendamento_id,))
            cursor.execute(
                "UPDATE horario SET status = ? WHERE id = ?",
                (StatusHorario.LIVRE.value, horario_id),
            )
            return True

    def obter_detalhes_completos(self, agendamento_id: int) -> Optional[Dict[str, Any]]:
        """
        Retorna visão detalhada com joins entre Agendamento, Horário, Agenda, UBS e Profissional.
        Útil para emissão de comprovantes e visualização de BI.
        """
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT a.id AS agendamento_id, a.tipo_agendamento, a.status, a.confirmado_em, a.data_criacao,
                       h.id AS horario_id, h.hora_inicio, h.hora_fim,
                       ag.data AS data_atendimento,
                       u_pac.nome AS nome_paciente, u_pac.cpf AS cpf_paciente, pac.cartao_sus, pac.faltas_nao_justificadas,
                       u_prof.nome AS nome_profissional, prof.especialidade, prof.registro_conselho,
                       ubs.nome AS nome_ubs, ubs.endereco AS endereco_ubs, ubs.telefone AS telefone_ubs
                FROM agendamento a
                INNER JOIN horario h ON a.horario_id = h.id
                INNER JOIN agenda_diaria ag ON h.agenda_id = ag.id
                INNER JOIN paciente pac ON a.paciente_id = pac.usuario_id
                INNER JOIN usuario u_pac ON pac.usuario_id = u_pac.id
                INNER JOIN profissional_saude prof ON ag.profissional_id = prof.usuario_id
                INNER JOIN usuario u_prof ON prof.usuario_id = u_prof.id
                INNER JOIN unidade_saude ubs ON ag.unidade_id = ubs.id
                WHERE a.id = ?
                """,
                (agendamento_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return dict(row)
        finally:
            conn.close()

    # =========================================================================
    # GESTÃO DE FALTAS E JUSTIFICATIVAS (RN03)
    # =========================================================================
    def registrar_falta_paciente(
        self, agendamento_id: int, data_falta: Optional[datetime] = None
    ) -> None:
        """
        Registra a ausência do paciente no agendamento e incrementa
        o contador de faltas não justificadas na tabela paciente (RN03).
        """
        dt_falta = data_falta or datetime.now()
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT paciente_id, horario_id FROM agendamento WHERE id = ?",
                (agendamento_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError("Agendamento não encontrado.")

            paciente_id = row["paciente_id"]

            cursor.execute(
                "UPDATE agendamento SET status = ? WHERE id = ?",
                (StatusAgendamento.FALTA.value, agendamento_id),
            )
            cursor.execute(
                """
                INSERT INTO registro_falta (paciente_id, agendamento_id, data_falta, justificada)
                VALUES (?, ?, ?, 0)
                """,
                (paciente_id, agendamento_id, dt_falta.isoformat()),
            )
            cursor.execute(
                """
                UPDATE paciente
                SET faltas_nao_justificadas = faltas_nao_justificadas + 1
                WHERE usuario_id = ?
                """,
                (paciente_id,),
            )

    def justificar_falta(
        self, registro_falta_id: int, motivo: str, gestor_id: int
    ) -> None:
        """
        Abona uma falta registrada (atestado médico / acolhimento presencial).
        Decrementa o contador de faltas não justificadas do paciente.
        """
        agora = datetime.now()
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT paciente_id, justificada FROM registro_falta WHERE id = ?",
                (registro_falta_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Registro de falta {registro_falta_id} não encontrado.")
            if row["justificada"]:
                raise ValueError("Esta falta já foi justificada anteriormente.")

            paciente_id = row["paciente_id"]

            cursor.execute(
                """
                UPDATE registro_falta
                SET justificada = 1, motivo_justificativa = ?, justificado_em = ?, justificado_por = ?
                WHERE id = ?
                """,
                (motivo, agora.isoformat(), gestor_id, registro_falta_id),
            )
            cursor.execute(
                """
                UPDATE paciente
                SET faltas_nao_justificadas = CASE
                    WHEN faltas_nao_justificadas > 0 THEN faltas_nao_justificadas - 1
                    ELSE 0
                END
                WHERE usuario_id = ?
                """,
                (paciente_id,),
            )

    def listar_faltas_paciente(self, paciente_id: int) -> List[Dict[str, Any]]:
        """Lista todas as faltas e justificativas registradas para um paciente."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT rf.id, rf.agendamento_id, rf.data_falta, rf.justificada,
                       rf.motivo_justificativa, rf.justificado_em, u.nome AS gestor_nome
                FROM registro_falta rf
                LEFT JOIN usuario u ON rf.justificado_por = u.id
                WHERE rf.paciente_id = ?
                ORDER BY rf.data_falta DESC
                """,
                (paciente_id,),
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
