-- ============================================================================
-- VagaCerta - Esquema Relacional de Banco de Dados (SQLite 3)
-- Alinhado ao DER e às Regras de Negócio do Projeto de Engenharia de Software
--
-- Regras Fundamentais:
-- 1. RN01 - Exclusividade de Horário: UNIQUE(horario_id) em agendamento
-- 2. Herança Relacional com Tabelas Separadas (PF - Primary / Foreign Key)
-- 3. Composição estrita: horario pertence a agenda_diaria com ON DELETE CASCADE
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- 1. Tabela de Unidade de Saúde (UBS)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS unidade_saude (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(120) NOT NULL,
    cnes CHAR(7) NOT NULL UNIQUE,
    endereco VARCHAR(160) NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 2. Tabela Base: Usuario (Hierarquia Abstrata)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(120) NOT NULL,
    cpf CHAR(11) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    senha_hash VARCHAR(128) NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    perfil VARCHAR(20) NOT NULL CHECK(perfil IN ('PACIENTE', 'PROFISSIONAL', 'GESTOR')),
    ativo BOOLEAN NOT NULL DEFAULT 1,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 2.1 Especialização: Paciente (Herança)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS paciente (
    usuario_id INTEGER PRIMARY KEY,
    cartao_sus CHAR(15) NOT NULL UNIQUE,
    data_nascimento DATE NOT NULL,
    faltas_nao_justificadas INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 2.2 Especialização: Profissional de Saúde (Herança)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS profissional_saude (
    usuario_id INTEGER PRIMARY KEY,
    registro_conselho VARCHAR(20) NOT NULL UNIQUE,
    especialidade VARCHAR(60) NOT NULL,
    carga_horaria_diaria INTEGER NOT NULL DEFAULT 8,
    FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 2.3 Especialização: Gestor da Unidade (Herança)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gestor_unidade (
    usuario_id INTEGER PRIMARY KEY,
    matricula VARCHAR(20) NOT NULL UNIQUE,
    cargo VARCHAR(60) NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 3. Tabela: Agenda Diária (RN04)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS agenda_diaria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unidade_id INTEGER NOT NULL,
    profissional_id INTEGER NOT NULL,
    data DATE NOT NULL,
    turno_inicio TIME NOT NULL,
    turno_fim TIME NOT NULL,
    bloqueada BOOLEAN NOT NULL DEFAULT 0,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (unidade_id) REFERENCES unidade_saude(id) ON DELETE RESTRICT,
    FOREIGN KEY (profissional_id) REFERENCES profissional_saude(usuario_id) ON DELETE RESTRICT,
    UNIQUE (profissional_id, data)
);

-- ----------------------------------------------------------------------------
-- 4. Tabela: Horário (Composição 1:N com Agenda Diária)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS horario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agenda_id INTEGER NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fim TIME NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'LIVRE' CHECK(status IN ('LIVRE', 'RESERVADO', 'BLOQUEADO')),
    FOREIGN KEY (agenda_id) REFERENCES agenda_diaria(id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 5. Tabela Base: Agendamento (RN01 - Exclusividade de Horário)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS agendamento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    horario_id INTEGER NOT NULL,
    paciente_id INTEGER NOT NULL,
    tipo_agendamento VARCHAR(20) NOT NULL CHECK(tipo_agendamento IN ('CONSULTA', 'EXAME', 'VACINA')),
    status VARCHAR(20) NOT NULL DEFAULT 'AGENDADO' CHECK(status IN ('AGENDADO', 'CONFIRMADO', 'REALIZADO', 'FALTA', 'CANCELADO')),
    confirmado_em DATETIME NULL,
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (horario_id) REFERENCES horario(id) ON DELETE RESTRICT,
    FOREIGN KEY (paciente_id) REFERENCES paciente(usuario_id) ON DELETE RESTRICT
);

-- RN01: Índice Único Parcial que impede mais de uma reserva ativa para o mesmo horário
CREATE UNIQUE INDEX IF NOT EXISTS uq_agendamento_horario_ativo 
ON agendamento(horario_id) 
WHERE status IN ('AGENDADO', 'CONFIRMADO', 'REALIZADO');

-- ----------------------------------------------------------------------------
-- 5.1 Especialização: Consulta Clínica (Polimorfismo)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS consulta_clinica (
    agendamento_id INTEGER PRIMARY KEY,
    motivo VARCHAR(160) NOT NULL,
    retorno BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (agendamento_id) REFERENCES agendamento(id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 5.2 Especialização: Exame (Polimorfismo)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS exame (
    agendamento_id INTEGER PRIMARY KEY,
    tipo_exame VARCHAR(60) NOT NULL,
    orientacao_preparo VARCHAR(255) NOT NULL,
    FOREIGN KEY (agendamento_id) REFERENCES agendamento(id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 5.3 Especialização: Vacinação (Polimorfismo)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vacinacao (
    agendamento_id INTEGER PRIMARY KEY,
    imunobiologico VARCHAR(60) NOT NULL,
    dose VARCHAR(20) NOT NULL,
    FOREIGN KEY (agendamento_id) REFERENCES agendamento(id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 6. Histórico de Faltas e Justificativas (RN03 - Auditoria e Desbloqueio)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS registro_falta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    agendamento_id INTEGER NOT NULL,
    data_falta DATETIME NOT NULL,
    justificada BOOLEAN NOT NULL DEFAULT 0,
    motivo_justificativa TEXT NULL,
    justificado_em DATETIME NULL,
    justificado_por INTEGER NULL,
    FOREIGN KEY (paciente_id) REFERENCES paciente(usuario_id) ON DELETE CASCADE,
    FOREIGN KEY (agendamento_id) REFERENCES agendamento(id) ON DELETE CASCADE,
    FOREIGN KEY (justificado_por) REFERENCES gestor_unidade(usuario_id)
);
