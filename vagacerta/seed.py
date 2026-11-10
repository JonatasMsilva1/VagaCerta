"""
Script de Carga de Dados Iniciais (Seed) do Sistema VagaCerta.
Popula o banco SQLite com dados realistas de UBS, profissionais, pacientes,
grades dinâmicas (RN04) e agendamentos para testes e demonstração imediata.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from datetime import date, time, timedelta, datetime
from vagacerta.database import db
from vagacerta.models.unidade import UnidadeSaude
from vagacerta.models.usuario import Paciente, ProfissionalSaude, GestorUnidade
from vagacerta.models.agenda import AgendaDiaria
from vagacerta.models.enums import StatusAgendamento
from vagacerta.dao.unidade_dao import UnidadeSaudeDAO
from vagacerta.dao.usuario_dao import UsuarioDAO
from vagacerta.dao.agenda_dao import AgendaDiariaDAO
from vagacerta.dao.agendamento_dao import AgendamentoDAO
from vagacerta.services.agendamento_service import AgendamentoService


def popular_banco(force_recreate: bool = True) -> None:
    """Inicializa as tabelas e insere dados iniciais demonstrativos."""
    print("[SEED] Inicializando esquema relacional do banco de dados SQLite...")
    db.inicializar_banco(force_recreate=force_recreate)

    unidade_dao = UnidadeSaudeDAO(db)
    usuario_dao = UsuarioDAO(db)
    agenda_dao = AgendaDiariaDAO(db)
    agendamento_dao = AgendamentoDAO(db)
    agendamento_service = AgendamentoService(agendamento_dao, agenda_dao, usuario_dao)

    print("[SEED] Cadastrando Unidades Básicas de Saúde...")
    ubs1 = unidade_dao.criar(
        UnidadeSaude(
            id=None,
            nome="UBS Zona 7 - Dr. Ary Rodrigues",
            cnes="2589631",
            endereco="Rua Paranaguá, 450 - Maringá, PR",
            telefone="(44) 3309-4500",
        )
    )
    ubs2 = unidade_dao.criar(
        UnidadeSaude(
            id=None,
            nome="UBS Alvorada - Vila Esperança",
            cnes="3698521",
            endereco="Av. Morangueira, 1200 - Maringá, PR",
            telefone="(44) 3309-5600",
        )
    )

    print("[SEED] Cadastrando Gestores, Profissionais e Pacientes...")
    # Gestor
    gestor = usuario_dao.criar_gestor(
        GestorUnidade(
            id=None,
            nome="Mariana Costa de Oliveira",
            cpf="11122233344",
            email="mariana.costa@saude.maringa.gov.br",
            senha_hash="hash_gestor_123",
            telefone="(44) 99881-1234",
            matricula="GES-2026-90",
            cargo="Coordenadora de Regulação e Atenção Básica",
        )
    )

    # Profissionais
    medico = usuario_dao.criar_profissional(
        ProfissionalSaude(
            id=None,
            nome="Dr. Carlos Eduardo Menezes",
            cpf="22233344455",
            email="carlos.menezes@ubs.saude.gov.br",
            senha_hash="hash_medico_123",
            telefone="(44) 99772-2345",
            registro_conselho="CRM-PR 34512",
            especialidade="Clínica Médica e Saúde da Família",
            carga_horaria_diaria=8,
        )
    )

    enfermeira = usuario_dao.criar_profissional(
        ProfissionalSaude(
            id=None,
            nome="Enfª. Juliana Rocha Peixoto",
            cpf="33344455566",
            email="juliana.rocha@ubs.saude.gov.br",
            senha_hash="hash_enf_123",
            telefone="(44) 99663-3456",
            registro_conselho="COREN-PR 88219",
            especialidade="Enfermagem da Família e Imunização",
            carga_horaria_diaria=8,
        )
    )

    # Pacientes
    # Paciente 1: Assíduo (0 faltas)
    paciente_regular = usuario_dao.criar_paciente(
        Paciente(
            id=None,
            nome="Lucas Pereira dos Santos",
            cpf="44455566677",
            email="lucas.santos@email.com",
            senha_hash="hash_pac_1",
            telefone="(44) 99111-2233",
            cartao_sus="700123456789012",
            data_nascimento=date(1994, 5, 14),
            faltas_nao_justificadas=0,
        )
    )

    # Paciente 2: 1 falta (dentro da normalidade)
    paciente_com_falta = usuario_dao.criar_paciente(
        Paciente(
            id=None,
            nome="Ana Paula de Souza",
            cpf="55566677788",
            email="ana.souza@email.com",
            senha_hash="hash_pac_2",
            telefone="(44) 99222-3344",
            cartao_sus="700987654321098",
            data_nascimento=date(1988, 11, 23),
            faltas_nao_justificadas=1,
        )
    )

    # Paciente 3: BLOQUEADO (3 faltas - RN03)
    paciente_bloqueado = usuario_dao.criar_paciente(
        Paciente(
            id=None,
            nome="Roberto Alves da Silva",
            cpf="66677788899",
            email="roberto.silva@email.com",
            senha_hash="hash_pac_3",
            telefone="(44) 99333-4455",
            cartao_sus="700555666777888",
            data_nascimento=date(1975, 3, 10),
            faltas_nao_justificadas=3,
        )
    )

    print("[SEED] Gerando Grades Dinâmicas de Horários (RN04)...")
    hoje = date.today()
    amanha = hoje + timedelta(days=1)
    depois_de_amanha = hoje + timedelta(days=2)

    # Agenda 1: Dr. Carlos (Consultas de 20 min no período da manhã)
    agenda_medico = AgendaDiaria(
        id=None,
        unidade_id=ubs1.id,
        profissional_id=medico.id,
        data_agenda=amanha,
        turno_inicio=time(8, 0),
        turno_fim=time(11, 0),
    )
    agenda_medico.gerar_horarios(duracao_minutos=20)  # RN04: Consulta = 20 min
    agenda_dao.criar(agenda_medico)

    # Agenda 2: Dr. Carlos para hoje (para demonstrar confirmação e autoliberação em tempo real)
    agenda_medico_hoje = AgendaDiaria(
        id=None,
        unidade_id=ubs1.id,
        profissional_id=medico.id,
        data_agenda=hoje,
        turno_inicio=time(13, 0),
        turno_fim=time(15, 0),
    )
    agenda_medico_hoje.gerar_horarios(duracao_minutos=20)
    agenda_dao.criar(agenda_medico_hoje)

    # Agenda 3: Enfª. Juliana (Vacinação de 5 min)
    agenda_enf = AgendaDiaria(
        id=None,
        unidade_id=ubs1.id,
        profissional_id=enfermeira.id,
        data_agenda=depois_de_amanha,
        turno_inicio=time(8, 0),
        turno_fim=time(9, 30),
    )
    agenda_enf.gerar_horarios(duracao_minutos=5)  # RN04: Vacina = 5 min
    agenda_dao.criar(agenda_enf)

    print("[SEED] Criando agendamentos demonstrativos e testando polimorfismo...")
    # Agendamento 1: Consulta Clínica para Lucas (Confirmada)
    horario1 = agenda_medico.horarios[0]
    consulta = agendamento_service.agendar_consulta(
        paciente_id=paciente_regular.id,
        horario_id=horario1.id,
        motivo="Avaliação de rotina e hipertensão",
        retorno=False,
    )
    agendamento_service.confirmar_presenca(consulta.id)

    # Agendamento 2: Exame com preparo obrigatório para Ana Paula
    horario2 = agenda_medico.horarios[1]
    exame = agendamento_service.agendar_exame(
        paciente_id=paciente_com_falta.id,
        horario_id=horario2.id,
        tipo_exame="Eletrocardiograma (ECG)",
        orientacao_preparo="Jejum de 4h, não ingerir cafeína ou fumar nas 12h que antecedem o exame.",
    )

    # Agendamento 3: Vacina para Lucas
    horario_vacina = agenda_enf.horarios[0]
    vacina = agendamento_service.agendar_vacinacao(
        paciente_id=paciente_regular.id,
        horario_id=horario_vacina.id,
        imunobiologico="Vacina Febre Amarela",
        dose="Dose Única",
    )

    # Agendamento 4: Consulta pendente NÃO CONFIRMADA em horário próximo para demonstrar AUTOLIBERAÇÃO
    horario_pendente = agenda_medico_hoje.horarios[0]
    agendamento_service.agendar_consulta(
        paciente_id=paciente_com_falta.id,
        horario_id=horario_pendente.id,
        motivo="Dor lombar persistente",
        retorno=True,
    )

    print("[SEED] Banco de dados populado com sucesso!")
    print(f"       - 2 Unidades de Saúde cadastradas")
    print(f"       - 1 Gestor, 2 Profissionais de Saúde e 3 Pacientes (1 bloqueado pela RN03)")
    print(f"       - 3 Grades diárias com total de {len(agenda_medico.horarios) + len(agenda_medico_hoje.horarios) + len(agenda_enf.horarios)} horários discretos")
    print(f"       - 4 Agendamentos com comportamentos polimórficos ativos")


if __name__ == "__main__":
    popular_banco()
