"""
Ponto de Entrada Principal da Aplicação VagaCerta.
Suporta execução interativa via CLI, demonstração ponta a ponta e execução de testes.
"""

import sys
from pathlib import Path

# Garante que o diretório raiz esteja no PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import unittest
from datetime import datetime, date, time, timedelta
from vagacerta.database import db
from vagacerta.seed import popular_banco
from vagacerta.cli.menu import VagaCertaCLI
from vagacerta.models.usuario import Paciente, ProfissionalSaude, GestorUnidade
from vagacerta.models.unidade import UnidadeSaude
from vagacerta.models.agenda import AgendaDiaria
from vagacerta.models.agendamento import ConsultaClinica, Exame, Vacinacao
from vagacerta.models.enums import StatusHorario
from vagacerta.dao.usuario_dao import UsuarioDAO
from vagacerta.dao.unidade_dao import UnidadeSaudeDAO
from vagacerta.dao.agenda_dao import AgendaDiariaDAO
from vagacerta.dao.agendamento_dao import AgendamentoDAO
from vagacerta.services.agendamento_service import AgendamentoService
from vagacerta.services.absenteismo_service import AbsenteismoService
from vagacerta.services.relatorios_service import RelatoriosService


def demonstracao_ponta_a_ponta() -> None:
    """
    Roteiro automatizado que executa e comprova:
    1. Criação do Banco de Dados Relacional e Carga Inicial
    2. Os 3 Pilares da POO (Herança, Composição e Polimorfismo)
    3. Operações CRUD completas persistindo dados em SQLite
    4. Aplicação das Regras de Negócio (RN01, RN02, RN03, RN04)
    5. Consolidação de Indicadores de Business Intelligence (F6)
    """
    print("\n" + "=" * 70)
    print(" INICIANDO DEMONSTRAÇÃO COMPLETA PONTA A PONTA - VAGACERTA")
    print("=" * 70)

    # 1. Banco e Seed
    print("\n>>> ETAPA 1: Persistência Relacional e Inicialização do Esquema")
    popular_banco(force_recreate=True)

    unidade_dao = UnidadeSaudeDAO(db)
    usuario_dao = UsuarioDAO(db)
    agenda_dao = AgendaDiariaDAO(db)
    agendamento_dao = AgendamentoDAO(db)
    agendamento_service = AgendamentoService(agendamento_dao, agenda_dao, usuario_dao)
    absenteismo_service = AbsenteismoService(agendamento_dao, usuario_dao)
    relatorios_service = RelatoriosService(db)

    # 2. Pilar da POO: HERANÇA
    print("\n>>> ETAPA 2: Pilar POO - HERANÇA (Hierarquia de Usuários)")
    pacientes = usuario_dao.listar_pacientes()
    profissionais = usuario_dao.listar_profissionais()
    gestores = usuario_dao.listar_gestores()

    print(f" [Herança] Total de Pacientes especializados: {len(pacientes)}")
    for p in pacientes:
        print(f"   * Paciente: {p.nome} | SUS: {p.cartao_sus} | Faltas: {p.faltas_nao_justificadas}")

    print(f" [Herança] Total de Profissionais especializados: {len(profissionais)}")
    for prof in profissionais:
        print(f"   * Profissional: {prof.nome} | Reg: {prof.registro_conselho} | Espec: {prof.especialidade}")

    print(f" [Herança] Total de Gestores especializados: {len(gestores)}")
    for g in gestores:
        print(f"   * Gestor: {g.nome} | Matrícula: {g.matricula} | Cargo: {g.cargo}")

    # 3. Pilar da POO: COMPOSIÇÃO
    print("\n>>> ETAPA 3: Pilar POO - COMPOSIÇÃO (AgendaDiaria contém Horarios)")
    ubs = unidade_dao.listar_todas()[0]
    medico = profissionais[0]
    data_teste = date.today() + timedelta(days=5)

    agenda_comp = AgendaDiaria(
        id=None,
        unidade_id=ubs.id,
        profissional_id=medico.id,
        data_agenda=data_teste,
        turno_inicio=time(8, 0),
        turno_fim=time(10, 0),
    )
    # RN04: Parametrização dinâmica
    agenda_comp.gerar_horarios(duracao_minutos=20)
    agenda_criada = agenda_dao.criar(agenda_comp)
    print(f" [Composição] AgendaDiaria ID {agenda_criada.id} instanciou e encapsulou {len(agenda_criada.horarios)} Horarios:")
    for h in agenda_criada.horarios:
        print(f"   -> Horário ID {h.id}: {h.hora_inicio.strftime('%H:%M')} às {h.hora_fim.strftime('%H:%M')} [{h.status.value}]")

    # 4. Pilar da POO: POLIMORFISMO
    print("\n>>> ETAPA 4: Pilar POO - POLIMORFISMO (Comportamento Especializado)")
    horarios_livres = agenda_criada.horarios_livres()
    paciente_apto = pacientes[0]

    # Criando Consulta (Janela 24h, Duração 20m, Preparo: Não)
    ag_consulta = agendamento_service.agendar_consulta(
        paciente_apto.id, horarios_livres[0].id, "Dor articular"
    )
    # Criando Exame (Janela 48h, Duração 30m, Preparo: Sim)
    ag_exame = agendamento_service.agendar_exame(
        paciente_apto.id, horarios_livres[1].id, "Hemograma Completo", "Jejum 10 horas obrigatório"
    )

    procedimentos = [ag_consulta, ag_exame]
    for proc in procedimentos:
        print(f"   * Tipo: {proc.tipo().value}")
        print(f"     - Janela de confirmação (RN02): {proc.janela_confirmacao_horas()}h")
        print(f"     - Exige Preparo: {proc.exige_preparo()}")
        print(f"     - Instruções Polimórficas: {proc.gerar_instrucoes_atendimento()}")

    # 5. Operações CRUD em Ação
    print("\n>>> ETAPA 5: Operações CRUD Completas no Banco SQLite")
    # CREATE
    novo_pac = usuario_dao.criar_paciente(
        Paciente(
            None,
            "Teste CRUD Silva",
            "77788899900",
            "teste.crud@email.com",
            "senha",
            "44988887777",
            "700444433332222",
            date(2000, 1, 1),
        )
    )
    print(f" [CRUD - CREATE] Paciente inserido com ID {novo_pac.id}")

    # READ
    lido = usuario_dao.buscar_paciente_por_id(novo_pac.id)
    print(f" [CRUD - READ] Paciente recuperado do banco: {lido.nome} (SUS: {lido.cartao_sus})")

    # UPDATE
    lido.nome = "Teste CRUD Silva Atualizado"
    usuario_dao.atualizar_paciente(lido)
    lido_atualizado = usuario_dao.buscar_paciente_por_id(novo_pac.id)
    print(f" [CRUD - UPDATE] Nome atualizado para: {lido_atualizado.nome}")

    # DELETE
    removido = usuario_dao.excluir_paciente(novo_pac.id)
    print(f" [CRUD - DELETE] Paciente excluído com sucesso: {removido}")

    # 6. Regras de Negócio: RN01 (Exclusividade)
    print("\n>>> ETAPA 6: Regra de Negócio RN01 (Exclusividade de Horário)")
    print(f" Tentando reservar o mesmo Horário ID {horarios_livres[0].id} já reservado pela consulta...")
    try:
        agendamento_service.agendar_consulta(pacientes[1].id, horarios_livres[0].id, "Tentativa duplicada")
    except ValueError as e:
        print(f" [RN01 SUCESSO] Bloqueio imediato atuou: {e}")

    # 7. Regras de Negócio: RN02 (Motor de Autoliberação / Descarte de Vagas)
    print("\n>>> ETAPA 7: Regra de Negócio RN02 (Motor de Autoliberação)")
    print(" Executando varredura com simulação temporal...")
    recuperadas = agendamento_service.executar_motor_autoliberacao()
    print(f" [RN02] Total de vagas autoliberadas para reoferta: {len(recuperadas)}")
    for r in recuperadas:
        print(f"   * Vaga recuperada: #{r['agendamento_id']} ({r['tipo']}) de {r['paciente']} -> Liberada para a fila.")

    # 8. Regras de Negócio: RN03 (Restrição por Reincidência de Faltas e Acolhimento)
    print("\n>>> ETAPA 8: Regra de Negócio RN03 (Controle de Faltas e Acolhimento)")
    paciente_bloq = [p for p in pacientes if p.esta_bloqueado()][0]
    print(f" Paciente com histórico de faltas: {paciente_bloq.nome} ({paciente_bloq.faltas_nao_justificadas} faltas)")
    try:
        agendamento_service.agendar_consulta(paciente_bloq.id, horarios_livres[2].id, "Consulta")
    except PermissionError as pe:
        print(f" [RN03 SUCESSO] Bloqueio remoto confirmado: {pe}")

    print(" Simulando acolhimento presencial na UBS com apresentação de atestado...")
    faltas_paciente = agendamento_dao.listar_faltas_paciente(paciente_bloq.id)
    if not faltas_paciente:
        # Registra uma falta caso ainda não exista no registro
        ag_mock = agendamento_dao.listar_por_paciente(paciente_bloq.id)
        if ag_mock:
            absenteismo_service.registrar_falta(ag_mock[0].id)
        faltas_paciente = agendamento_dao.listar_faltas_paciente(paciente_bloq.id)

    if faltas_paciente:
        falta_alvo = [f for f in faltas_paciente if not f["justificada"]][0]
        res_acolhimento = absenteismo_service.acolher_e_justificar_falta(
            registro_falta_id=falta_alvo["id"],
            motivo_justificativa="Atestado médico de urgência entregue presencialmente",
            gestor_id=gestores[0].id,
        )
        print(f" [ACOLHIMENTO] {res_acolhimento['mensagem']} (Justificado por: {res_acolhimento['gestor_responsavel']})")

    # 9. Relatório de BI (F6)
    print("\n>>> ETAPA 9: Módulo de Business Intelligence (BI & Absenteísmo - F6)")
    metricas = relatorios_service.relatorio_geral_absenteismo()
    print(" Métricas Consolidadas:")
    print(f"   * Total de Agendamentos: {metricas['total_agendamentos']}")
    print(f"   * Atendimentos Confirmados/Ativos: {metricas['confirmados']}")
    print(f"   * Faltas Registradas: {metricas['faltas']}")
    print(f"   * Vagas Liberadas/Canceladas: {metricas['cancelados_autoliberados']}")
    print(f"   * Taxa Geral de Absenteísmo: {metricas['taxa_absenteismo_percentual']}%")
    print(f"   * Taxa de Ocupação da Grade: {metricas['taxa_ocupacao_grade_percentual']}%")

    print("\n" + "=" * 70)
    print(" DEMONSTRAÇÃO CONCLUÍDA COM 100% DE SUCESSO!")
    print("=" * 70)


def executar_testes_automatizados() -> None:
    """Carrega e executa a suíte de testes com unittest."""
    print("\n[TESTES] Executando suíte completa de testes unitários e de integração...")
    loader = unittest.TestLoader()
    suite = loader.discover("vagacerta/tests", pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)


def main() -> None:
    """Dispatcher de argumentos de execução."""
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ("--demo", "-d"):
            demonstracao_ponta_a_ponta()
            return
        elif arg in ("--seed", "-s"):
            popular_banco(force_recreate=True)
            return
        elif arg in ("--test", "-t"):
            executar_testes_automatizados()
            return

    # Inicia CLI interativa se nenhum argumento for fornecido
    cli = VagaCertaCLI()
    cli.iniciar()


if __name__ == "__main__":
    main()
