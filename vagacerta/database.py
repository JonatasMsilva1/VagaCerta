"""
Módulo de Gerenciamento de Conexão e Transações do Banco de Dados.
Fornece contexto transacional seguro, ativando suporte a Foreign Keys no SQLite.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator
from vagacerta.config import DB_PATH, SCHEMA_FILE


class DatabaseManager:
    """
    Gerenciador singleton-like para conexões SQLite com suporte a transações ACID.
    """

    def __init__(self, db_path: Path | str = DB_PATH):
        self.db_path = Path(db_path)

    def get_connection(self) -> sqlite3.Connection:
        """
        Retorna uma conexão ativa com SQLite com foreign keys habilitadas
        e row_factory configurado para acesso por nome de coluna.
        """
        # Garante que a pasta pai exista
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Context manager para transações atômicas. Faz commit automático ao finalizar
        ou rollback em caso de exceção.
        """
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def inicializar_banco(self, force_recreate: bool = False) -> None:
        """
        Executa o script DDL schema.sql para criar todas as tabelas e índices.
        Se force_recreate for True, remove o arquivo existente antes de recriar.
        """
        if force_recreate and self.db_path.exists():
            self.db_path.unlink()

        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            ddl_script = f.read()

        with self.transaction() as conn:
            conn.executescript(ddl_script)


# Instância padrão utilizada pela aplicação
db = DatabaseManager()
