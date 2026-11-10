"""
Módulo DAO para Gestão e Persistência de Unidades de Saúde (UBS).
Operações CRUD completas com validação de CNES e tratamento de erros.
"""

from typing import List, Optional
from vagacerta.database import db
from vagacerta.models.unidade import UnidadeSaude


class UnidadeSaudeDAO:
    """Data Access Object para Unidades Básicas de Saúde."""

    def __init__(self, database_manager=db):
        self.db = database_manager

    def criar(self, unidade: UnidadeSaude) -> UnidadeSaude:
        """Cria uma nova UBS no banco de dados."""
        unidade.validar()
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO unidade_saude (nome, cnes, endereco, telefone)
                VALUES (?, ?, ?, ?)
                """,
                (unidade.nome, unidade.cnes, unidade.endereco, unidade.telefone),
            )
            unidade.id = cursor.lastrowid
            return unidade

    def buscar_por_id(self, unidade_id: int) -> Optional[UnidadeSaude]:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, nome, cnes, endereco, telefone FROM unidade_saude WHERE id = ?",
                (unidade_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return UnidadeSaude(
                id=row["id"],
                nome=row["nome"],
                cnes=row["cnes"],
                endereco=row["endereco"],
                telefone=row["telefone"],
            )
        finally:
            conn.close()

    def buscar_por_cnes(self, cnes: str) -> Optional[UnidadeSaude]:
        cnes_clean = "".join(filter(str.isdigit, cnes))
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, nome, cnes, endereco, telefone FROM unidade_saude WHERE cnes = ?",
                (cnes_clean,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return UnidadeSaude(
                id=row["id"],
                nome=row["nome"],
                cnes=row["cnes"],
                endereco=row["endereco"],
                telefone=row["telefone"],
            )
        finally:
            conn.close()

    def listar_todas(self) -> List[UnidadeSaude]:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome, cnes, endereco, telefone FROM unidade_saude ORDER BY nome ASC")
            return [
                UnidadeSaude(
                    id=row["id"],
                    nome=row["nome"],
                    cnes=row["cnes"],
                    endereco=row["endereco"],
                    telefone=row["telefone"],
                )
                for row in cursor.fetchall()
            ]
        finally:
            conn.close()

    def atualizar(self, unidade: UnidadeSaude) -> None:
        if not unidade.id:
            raise ValueError("Unidade de Saúde sem ID para atualização.")
        unidade.validar()
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE unidade_saude
                SET nome = ?, cnes = ?, endereco = ?, telefone = ?
                WHERE id = ?
                """,
                (unidade.nome, unidade.cnes, unidade.endereco, unidade.telefone, unidade.id),
            )

    def excluir(self, unidade_id: int) -> bool:
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM unidade_saude WHERE id = ?", (unidade_id,))
            return cursor.rowcount > 0
