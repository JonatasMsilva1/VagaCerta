"""
Módulo DAO para Gestão e Persistência de Usuários (Paciente, Profissional, Gestor).
Implementa operações CRUD completas com mapeamento para tabelas separadas (Herança Relacional).
"""

import sqlite3
from typing import List, Optional
from vagacerta.database import db
from vagacerta.models.usuario import Paciente, ProfissionalSaude, GestorUnidade, Usuario
from vagacerta.models.enums import PerfilAcesso


class UsuarioDAO:
    """
    Data Access Object para operações CRUD na hierarquia de Usuários.
    Garante integridade referencial nas transações entre a tabela pai `usuario`
    e as tabelas especializadas (`paciente`, `profissional_saude`, `gestor_unidade`).
    """

    def __init__(self, database_manager=db):
        self.db = database_manager

    # =========================================================================
    # CRUD - PACIENTE
    # =========================================================================
    def criar_paciente(self, paciente: Paciente) -> Paciente:
        """Cria um novo paciente persistindo nas tabelas usuario e paciente."""
        paciente.validar()
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO usuario (nome, cpf, email, senha_hash, telefone, perfil, ativo)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    paciente.nome,
                    paciente.cpf,
                    paciente.email,
                    paciente.senha_hash,
                    paciente.telefone,
                    PerfilAcesso.PACIENTE.value,
                    1 if paciente.ativo else 0,
                ),
            )
            usuario_id = cursor.lastrowid
            paciente.id = usuario_id

            cursor.execute(
                """
                INSERT INTO paciente (usuario_id, cartao_sus, data_nascimento, faltas_nao_justificadas)
                VALUES (?, ?, ?, ?)
                """,
                (
                    usuario_id,
                    paciente.cartao_sus,
                    paciente.data_nascimento.isoformat(),
                    paciente.faltas_nao_justificadas,
                ),
            )
            return paciente

    def buscar_paciente_por_id(self, paciente_id: int) -> Optional[Paciente]:
        """Busca paciente por ID com junção relacional."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT u.id, u.nome, u.cpf, u.email, u.senha_hash, u.telefone, u.ativo,
                       p.cartao_sus, p.data_nascimento, p.faltas_nao_justificadas
                FROM usuario u
                INNER JOIN paciente p ON u.id = p.usuario_id
                WHERE u.id = ?
                """,
                (paciente_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return Paciente(
                id=row["id"],
                nome=row["nome"],
                cpf=row["cpf"],
                email=row["email"],
                senha_hash=row["senha_hash"],
                telefone=row["telefone"],
                cartao_sus=row["cartao_sus"],
                data_nascimento=row["data_nascimento"],
                faltas_nao_justificadas=row["faltas_nao_justificadas"],
                ativo=bool(row["ativo"]),
            )
        finally:
            conn.close()

    def buscar_paciente_por_cpf(self, cpf: str) -> Optional[Paciente]:
        """Busca paciente por CPF normalizado."""
        cpf_clean = "".join(filter(str.isdigit, cpf))
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT u.id, u.nome, u.cpf, u.email, u.senha_hash, u.telefone, u.ativo,
                       p.cartao_sus, p.data_nascimento, p.faltas_nao_justificadas
                FROM usuario u
                INNER JOIN paciente p ON u.id = p.usuario_id
                WHERE u.cpf = ?
                """,
                (cpf_clean,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return Paciente(
                id=row["id"],
                nome=row["nome"],
                cpf=row["cpf"],
                email=row["email"],
                senha_hash=row["senha_hash"],
                telefone=row["telefone"],
                cartao_sus=row["cartao_sus"],
                data_nascimento=row["data_nascimento"],
                faltas_nao_justificadas=row["faltas_nao_justificadas"],
                ativo=bool(row["ativo"]),
            )
        finally:
            conn.close()

    def listar_pacientes(self) -> List[Paciente]:
        """Retorna todos os pacientes cadastrados."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT u.id, u.nome, u.cpf, u.email, u.senha_hash, u.telefone, u.ativo,
                       p.cartao_sus, p.data_nascimento, p.faltas_nao_justificadas
                FROM usuario u
                INNER JOIN paciente p ON u.id = p.usuario_id
                ORDER BY u.nome ASC
                """
            )
            lista = []
            for row in cursor.fetchall():
                lista.append(
                    Paciente(
                        id=row["id"],
                        nome=row["nome"],
                        cpf=row["cpf"],
                        email=row["email"],
                        senha_hash=row["senha_hash"],
                        telefone=row["telefone"],
                        cartao_sus=row["cartao_sus"],
                        data_nascimento=row["data_nascimento"],
                        faltas_nao_justificadas=row["faltas_nao_justificadas"],
                        ativo=bool(row["ativo"]),
                    )
                )
            return lista
        finally:
            conn.close()

    def atualizar_paciente(self, paciente: Paciente) -> None:
        """Atualiza dados do paciente em ambas as tabelas."""
        if not paciente.id:
            raise ValueError("Paciente sem ID para atualização.")
        paciente.validar()
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE usuario
                SET nome = ?, cpf = ?, email = ?, senha_hash = ?, telefone = ?, ativo = ?
                WHERE id = ?
                """,
                (
                    paciente.nome,
                    paciente.cpf,
                    paciente.email,
                    paciente.senha_hash,
                    paciente.telefone,
                    1 if paciente.ativo else 0,
                    paciente.id,
                ),
            )
            cursor.execute(
                """
                UPDATE paciente
                SET cartao_sus = ?, data_nascimento = ?, faltas_nao_justificadas = ?
                WHERE usuario_id = ?
                """,
                (
                    paciente.cartao_sus,
                    paciente.data_nascimento.isoformat(),
                    paciente.faltas_nao_justificadas,
                    paciente.id,
                ),
            )

    def excluir_paciente(self, paciente_id: int) -> bool:
        """Exclui paciente (a chave estrangeira em cascata apaga os dados de paciente)."""
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM usuario WHERE id = ?", (paciente_id,))
            return cursor.rowcount > 0

    # =========================================================================
    # CRUD - PROFISSIONAL DE SAÚDE
    # =========================================================================
    def criar_profissional(self, prof: ProfissionalSaude) -> ProfissionalSaude:
        """Cria profissional de saúde (médico/enfermeiro)."""
        prof.validar()
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO usuario (nome, cpf, email, senha_hash, telefone, perfil, ativo)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    prof.nome,
                    prof.cpf,
                    prof.email,
                    prof.senha_hash,
                    prof.telefone,
                    PerfilAcesso.PROFISSIONAL.value,
                    1 if prof.ativo else 0,
                ),
            )
            usuario_id = cursor.lastrowid
            prof.id = usuario_id

            cursor.execute(
                """
                INSERT INTO profissional_saude (usuario_id, registro_conselho, especialidade, carga_horaria_diaria)
                VALUES (?, ?, ?, ?)
                """,
                (usuario_id, prof.registro_conselho, prof.especialidade, prof.carga_horaria_diaria),
            )
            return prof

    def buscar_profissional_por_id(self, prof_id: int) -> Optional[ProfissionalSaude]:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT u.id, u.nome, u.cpf, u.email, u.senha_hash, u.telefone, u.ativo,
                       ps.registro_conselho, ps.especialidade, ps.carga_horaria_diaria
                FROM usuario u
                INNER JOIN profissional_saude ps ON u.id = ps.usuario_id
                WHERE u.id = ?
                """,
                (prof_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return ProfissionalSaude(
                id=row["id"],
                nome=row["nome"],
                cpf=row["cpf"],
                email=row["email"],
                senha_hash=row["senha_hash"],
                telefone=row["telefone"],
                registro_conselho=row["registro_conselho"],
                especialidade=row["especialidade"],
                carga_horaria_diaria=row["carga_horaria_diaria"],
                ativo=bool(row["ativo"]),
            )
        finally:
            conn.close()

    def listar_profissionais(self) -> List[ProfissionalSaude]:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT u.id, u.nome, u.cpf, u.email, u.senha_hash, u.telefone, u.ativo,
                       ps.registro_conselho, ps.especialidade, ps.carga_horaria_diaria
                FROM usuario u
                INNER JOIN profissional_saude ps ON u.id = ps.usuario_id
                ORDER BY u.nome ASC
                """
            )
            lista = []
            for row in cursor.fetchall():
                lista.append(
                    ProfissionalSaude(
                        id=row["id"],
                        nome=row["nome"],
                        cpf=row["cpf"],
                        email=row["email"],
                        senha_hash=row["senha_hash"],
                        telefone=row["telefone"],
                        registro_conselho=row["registro_conselho"],
                        especialidade=row["especialidade"],
                        carga_horaria_diaria=row["carga_horaria_diaria"],
                        ativo=bool(row["ativo"]),
                    )
                )
            return lista
        finally:
            conn.close()

    def atualizar_profissional(self, prof: ProfissionalSaude) -> None:
        if not prof.id:
            raise ValueError("Profissional sem ID para atualização.")
        prof.validar()
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE usuario
                SET nome = ?, cpf = ?, email = ?, senha_hash = ?, telefone = ?, ativo = ?
                WHERE id = ?
                """,
                (
                    prof.nome,
                    prof.cpf,
                    prof.email,
                    prof.senha_hash,
                    prof.telefone,
                    1 if prof.ativo else 0,
                    prof.id,
                ),
            )
            cursor.execute(
                """
                UPDATE profissional_saude
                SET registro_conselho = ?, especialidade = ?, carga_horaria_diaria = ?
                WHERE usuario_id = ?
                """,
                (prof.registro_conselho, prof.especialidade, prof.carga_horaria_diaria, prof.id),
            )

    def excluir_profissional(self, prof_id: int) -> bool:
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM usuario WHERE id = ?", (prof_id,))
            return cursor.rowcount > 0

    # =========================================================================
    # CRUD - GESTOR DE UNIDADE
    # =========================================================================
    def criar_gestor(self, gestor: GestorUnidade) -> GestorUnidade:
        gestor.validar()
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO usuario (nome, cpf, email, senha_hash, telefone, perfil, ativo)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    gestor.nome,
                    gestor.cpf,
                    gestor.email,
                    gestor.senha_hash,
                    gestor.telefone,
                    PerfilAcesso.GESTOR.value,
                    1 if gestor.ativo else 0,
                ),
            )
            usuario_id = cursor.lastrowid
            gestor.id = usuario_id

            cursor.execute(
                """
                INSERT INTO gestor_unidade (usuario_id, matricula, cargo)
                VALUES (?, ?, ?)
                """,
                (usuario_id, gestor.matricula, gestor.cargo),
            )
            return gestor

    def buscar_gestor_por_id(self, gestor_id: int) -> Optional[GestorUnidade]:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT u.id, u.nome, u.cpf, u.email, u.senha_hash, u.telefone, u.ativo,
                       gu.matricula, gu.cargo
                FROM usuario u
                INNER JOIN gestor_unidade gu ON u.id = gu.usuario_id
                WHERE u.id = ?
                """,
                (gestor_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return GestorUnidade(
                id=row["id"],
                nome=row["nome"],
                cpf=row["cpf"],
                email=row["email"],
                senha_hash=row["senha_hash"],
                telefone=row["telefone"],
                matricula=row["matricula"],
                cargo=row["cargo"],
                ativo=bool(row["ativo"]),
            )
        finally:
            conn.close()

    def listar_gestores(self) -> List[GestorUnidade]:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT u.id, u.nome, u.cpf, u.email, u.senha_hash, u.telefone, u.ativo,
                       gu.matricula, gu.cargo
                FROM usuario u
                INNER JOIN gestor_unidade gu ON u.id = gu.usuario_id
                ORDER BY u.nome ASC
                """
            )
            lista = []
            for row in cursor.fetchall():
                lista.append(
                    GestorUnidade(
                        id=row["id"],
                        nome=row["nome"],
                        cpf=row["cpf"],
                        email=row["email"],
                        senha_hash=row["senha_hash"],
                        telefone=row["telefone"],
                        matricula=row["matricula"],
                        cargo=row["cargo"],
                        ativo=bool(row["ativo"]),
                    )
                )
            return lista
        finally:
            conn.close()

    def atualizar_gestor(self, gestor: GestorUnidade) -> None:
        if not gestor.id:
            raise ValueError("Gestor sem ID para atualização.")
        gestor.validar()
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE usuario
                SET nome = ?, cpf = ?, email = ?, senha_hash = ?, telefone = ?, ativo = ?
                WHERE id = ?
                """,
                (
                    gestor.nome,
                    gestor.cpf,
                    gestor.email,
                    gestor.senha_hash,
                    gestor.telefone,
                    1 if gestor.ativo else 0,
                    gestor.id,
                ),
            )
            cursor.execute(
                """
                UPDATE gestor_unidade
                SET matricula = ?, cargo = ?
                WHERE usuario_id = ?
                """,
                (gestor.matricula, gestor.cargo, gestor.id),
            )

    def excluir_gestor(self, gestor_id: int) -> bool:
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM usuario WHERE id = ?", (gestor_id,))
            return cursor.rowcount > 0
