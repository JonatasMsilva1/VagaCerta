"""
Módulo de Serviço de Relatórios e Business Intelligence (F6 - BI).
Consolida indicadores estratégicos de ocupação de agenda, taxa geral de absenteísmo,
vagas recuperadas e ociosidade da rede de saúde.
"""

from typing import Dict, Any, List
from vagacerta.database import db
from vagacerta.models.enums import StatusAgendamento, StatusHorario


class RelatoriosService:
    """
    Gera relatórios analíticos para gestores e secretarias de saúde.
    """

    def __init__(self, database_manager=db):
        self.db = database_manager

    def relatorio_geral_absenteismo(self) -> Dict[str, Any]:
        """
        Calcula a taxa geral de absenteísmo da rede:
        Absenteísmo = Faltas / (Atendimentos Realizados + Faltas)
        """
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT status, COUNT(*) as total
                FROM agendamento
                GROUP BY status
                """
            )
            contagens = {row["status"]: row["total"] for row in cursor.fetchall()}

            agendados = contagens.get(StatusAgendamento.AGENDADO.value, 0)
            confirmados = contagens.get(StatusAgendamento.CONFIRMADO.value, 0)
            realizados = contagens.get(StatusAgendamento.REALIZADO.value, 0)
            faltas = contagens.get(StatusAgendamento.FALTA.value, 0)
            cancelados = contagens.get(StatusAgendamento.CANCELADO.value, 0)
            total_geral = agendados + confirmados + realizados + faltas + cancelados

            total_concluidos = realizados + faltas
            taxa_absenteismo = (
                round((faltas / total_concluidos) * 100, 2)
                if total_concluidos > 0
                else 0.0
            )

            # Contagem de vagas liberadas e horários livres atuais
            cursor.execute(
                "SELECT status, COUNT(*) as total FROM horario GROUP BY status"
            )
            horarios_status = {row["status"]: row["total"] for row in cursor.fetchall()}
            horarios_livres = horarios_status.get(StatusHorario.LIVRE.value, 0)
            horarios_reservados = horarios_status.get(StatusHorario.RESERVADO.value, 0)
            total_horarios = sum(horarios_status.values())

            taxa_ocupacao_grade = (
                round((horarios_reservados / total_horarios) * 100, 2)
                if total_horarios > 0
                else 0.0
            )

            return {
                "total_agendamentos": total_geral,
                "agendados_pendentes": agendados,
                "confirmados": confirmados,
                "realizados": realizados,
                "faltas": faltas,
                "cancelados_autoliberados": cancelados,
                "taxa_absenteismo_percentual": taxa_absenteismo,
                "total_horarios_grade": total_horarios,
                "horarios_disponiveis_livres": horarios_livres,
                "horarios_reservados": horarios_reservados,
                "taxa_ocupacao_grade_percentual": taxa_ocupacao_grade,
            }
        finally:
            conn.close()

    def relatorio_absenteismo_por_procedimento(self) -> List[Dict[str, Any]]:
        """Consolida faltas agrupadas por especialização do atendimento."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT tipo_agendamento,
                       COUNT(*) as total,
                       SUM(CASE WHEN status = 'FALTA' THEN 1 ELSE 0 END) as faltas,
                       SUM(CASE WHEN status = 'REALIZADO' THEN 1 ELSE 0 END) as realizados,
                       SUM(CASE WHEN status = 'CONFIRMADO' THEN 1 ELSE 0 END) as confirmados,
                       SUM(CASE WHEN status = 'CANCELADO' THEN 1 ELSE 0 END) as cancelados
                FROM agendamento
                GROUP BY tipo_agendamento
                """
            )
            linhas = []
            for row in cursor.fetchall():
                total_desfecho = row["realizados"] + row["faltas"]
                taxa = (
                    round((row["faltas"] / total_desfecho) * 100, 1)
                    if total_desfecho > 0
                    else 0.0
                )
                linhas.append(
                    {
                        "tipo_procedimento": row["tipo_agendamento"],
                        "total_geral": row["total"],
                        "realizados": row["realizados"],
                        "faltas": row["faltas"],
                        "confirmados": row["confirmados"],
                        "cancelados": row["cancelados"],
                        "taxa_absenteismo": taxa,
                    }
                )
            return linhas
        finally:
            conn.close()

    def relatorio_pacientes_criticos(self, limite_faltas: int = 2) -> List[Dict[str, Any]]:
        """Identifica pacientes com reincidência próxima ou acima do limite de bloqueio (RN03)."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT u.id, u.nome, u.cpf, u.telefone, p.cartao_sus, p.faltas_nao_justificadas
                FROM paciente p
                INNER JOIN usuario u ON p.usuario_id = u.id
                WHERE p.faltas_nao_justificadas >= ?
                ORDER BY p.faltas_nao_justificadas DESC
                """,
                (limite_faltas,),
            )
            return [
                {
                    "paciente_id": row["id"],
                    "nome": row["nome"],
                    "cpf": row["cpf"],
                    "telefone": row["telefone"],
                    "cartao_sus": row["cartao_sus"],
                    "faltas_nao_justificadas": row["faltas_nao_justificadas"],
                    "bloqueado": row["faltas_nao_justificadas"] >= 3,
                }
                for row in cursor.fetchall()
            ]
        finally:
            conn.close()
