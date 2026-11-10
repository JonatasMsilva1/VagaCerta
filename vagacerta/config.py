"""
Módulo de Configuração do Sistema VagaCerta.
Isola caminhos, parâmetros de conexão e configurações de negócio
para não fixar credenciais ou caminhos no código-fonte.
"""

import os
from pathlib import Path

# Diretório raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# Configurações de Banco de Dados
# Permite sobrescrever via variável de ambiente VAGACERTA_DB_PATH
DEFAULT_DB_FILE = BASE_DIR / "vagacerta.db"
DB_PATH = Path(os.getenv("VAGACERTA_DB_PATH", str(DEFAULT_DB_FILE)))

# Caminho do script de criação DDL
SCHEMA_FILE = Path(__file__).resolve().parent / "schema.sql"

# Configurações de Regras de Negócio (RN03, RN04)
LIMITE_FALTAS_BLOQUEIO = int(os.getenv("LIMITE_FALTAS_BLOQUEIO", "3"))
MESES_JANELA_FALTAS = int(os.getenv("MESES_JANELA_FALTAS", "6"))

# Janelas de confirmação obrigatória (RN02) em horas
JANELA_CONFIRMACAO_CONSULTA_HORAS = 24
JANELA_CONFIRMACAO_EXAME_HORAS = 48
JANELA_CONFIRMACAO_VACINA_HORAS = 0  # Isenta

# Duração padrão dos atendimentos (RN04) em minutos
DURACAO_CONSULTA_MINUTOS = 20
DURACAO_EXAME_MINUTOS = 30
DURACAO_VACINA_MINUTOS = 5
