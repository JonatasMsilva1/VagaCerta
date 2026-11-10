"""
Suíte de Testes das Regras de Negócio do Sistema VagaCerta.
Valida rigorosamente RN01, RN02, RN03 e RN04.
"""

import unittest
from pathlib import Path
from datetime import date, time, datetime, timedelta
from vagacerta.database import DatabaseManager
from vagacerta.models.unidade import UnidadeSaude
from vagacerta.models.usuario import Paciente, ProfissionalSaude, GestorUnidade
from vagacerta.models.agenda import AgendaDiaria
from vagacerta.models.enums import StatusHorario, StatusAgendamento
from vagacerta.dao.unidade_dao import UnidadeSaudeDAO
from vagacerta.dao.usuario_dao import UsuarioDAO
from vagacerta.dao.agenda_dao import AgendaDiariaDAO
from vagacerta.dao.agendamento_dao import AgendamentoDAO
from vagacerta.services.agendamento_service import AgendamentoService
from vagacerta.services.absenteismo_service import AbsenteismoService

TEST_RN_DB = Path(__file__).resolve().parent / "test_rn_vagacerta.db"


class TesteRegrasNegocio(unittest.TestCase):
    """Testes funcionais das regras de negócio RN01, RN02, RN03 e RN04."""

    @classmethod
    def setUpClass(cls):
        cls.db_test = DatabaseManager(TEST_RN_DB)
        cls.db_test.inicializar_banco(force_recreate=True)
        cls.unidade_dao = UnidadeSaudeDAO(cls.db_test)
        cls.usuario_dao = UsuarioDAO(cls.db_test)
        cls.agenda_dao = AgendaDiariaDAO(cls.db_test)
        cls.agendamento_dao = AgendamentoDAO(cls.db_test)
        cls.agendamento_service = AgendamentoService(
            cls.agendamento_dao, cls.agenda_dao, cls.usuario_dao
        )
        cls.absenteismo_service = AbsenteismoService(
            cls.agendamento_dao, cls.usuario_dao
        )

        # Setup básico
        cls.ubs = cls.unidade_dao.criar(
            UnidadeSaude(None, "UBS Central", "1234567", "Rua das Flores, 100", "4432220000")
        )
        cls.medico = cls.usuario_dao.criar_profissional(
            ProfissionalSaude(
                None, "Dr. Ricardo", "11111111111", "ricardo@ubs.gov", "h", "4499990001", "CRM-PR 1010", "Clínica Geral"
            )
        )
        cls.gestor = cls.usuario_dao.criar_gestor(
            GestorUnidade(
                None, "Carlos Gestor", "22222222222", "carlos@ubs.gov", "h", "4499990002", "GES-10", "Coordenador"
            )
        )

    @classmethod
    def tearDownClass(cls):
        if TEST_RN_DB.exists():
            TEST_RN_DB.unlink()

    # =========================================================================
    # RN01 - EXCLUSIVIDADE DE HORÁRIO
    # =========================================================================
    def test_rn01_exclusividade_horario(self):
        """RN01: Um horário admite apenas um agendamento ativo."""
        paciente1 = self.usuario_dao.criar_paciente(
            Paciente(None, "Ana", "33333333333", "ana@rn.com", "h", "44999", "700100000000001", date(1995, 1, 1))
        )
        paciente2 = self.usuario_dao.criar_paciente(
            Paciente(None, "Bruno", "44444444444", "bruno@rn.com", "h", "44998", "700200000000002", date(1992, 2, 2))
        )

        agenda = AgendaDiaria(None, self.ubs.id, self.medico.id, date(2026, 12, 15), time(8, 0), time(8, 40))
        agenda.gerar_horarios(20)  # 2 horários
        self.agenda_dao.criar(agenda)
        horario = agenda.horarios[0]

        # 1. Paciente 1 agenda no horário
        ag1 = self.agendamento_service.agendar_consulta(paciente1.id, horario.id, "Dor de cabeça")
        self.assertIsNotNone(ag1.id)

        # 2. Paciente 2 tenta agendar no MESMO horário -> Deve falhar com erro amigável de indisponibilidade
        with self.assertRaises(ValueError) as ctx:
            self.agendamento_service.agendar_consulta(paciente2.id, horario.id, "Checkup")
        self.assertIn("indisponível", str(ctx.exception).lower())

        # 3. Paciente 1 cancela o agendamento -> Horário deve retornar IMEDIATAMENTE para LIVRE
        self.agendamento_service.cancelar_agendamento(ag1.id)
        h_verif = self.agenda_dao.buscar_horario_por_id(horario.id)
        self.assertEqual(h_verif.status, StatusHorario.LIVRE)

        # 4. Agora Paciente 2 consegue reservar
        ag2 = self.agendamento_service.agendar_consulta(paciente2.id, horario.id, "Checkup")
        self.assertIsNotNone(ag2.id)

    # =========================================================================
    # RN02 - JANELA DIFERENCIADA E MOTOR DE AUTOLIBERAÇÃO
    # =========================================================================
    def test_rn02_motor_autoliberacao_descarte(self):
        """
        RN02: Janela de confirmação diferenciada. Ausência de confirmação
        no prazo resulta em liberação automática do horário para a fila.
        """
        paciente = self.usuario_dao.criar_paciente(
            Paciente(None, "Carla", "55555555555", "carla@rn.com", "h", "44997", "700300000000003", date(1989, 3, 3))
        )

        # Criar agenda para amanhã às 10:00
        data_amanha = date.today() + timedelta(days=1)
        agenda = AgendaDiaria(None, self.ubs.id, self.medico.id, data_amanha, time(10, 0), time(11, 0))
        agenda.gerar_horarios(20)  # 3 horários
        self.agenda_dao.criar(agenda)

        h_consulta = agenda.horarios[0]
        h_exame = agenda.horarios[1]
        h_confirmada = agenda.horarios[2]

        # Agendamento 1: Consulta (Janela 24h) - NÃO CONFIRMADA
        ag_consulta = self.agendamento_service.agendar_consulta(paciente.id, h_consulta.id, "Gripe")

        # Agendamento 2: Exame (Janela 48h) - NÃO CONFIRMADO
        ag_exame = self.agendamento_service.agendar_exame(paciente.id, h_exame.id, "Glicemia", "Jejum 12h")

        # Agendamento 3: Consulta (Janela 24h) - CONFIRMADA PELO PACIENTE
        ag_confirmada = self.agendamento_service.agendar_consulta(paciente.id, h_confirmada.id, "Retorno")
        self.agendamento_service.confirmar_presenca(ag_confirmada.id)

        # Simula momento atual: Faltam 12 horas para o atendimento (exame e consulta estouraram a janela)
        momento_simulado = datetime.combine(data_amanha, time(10, 0)) - timedelta(hours=12)

        recuperadas = self.agendamento_service.executar_motor_autoliberacao(momento_referencia=momento_simulado)

        # Devem ter sido recuperadas exatamente 2 vagas (ag_consulta e ag_exame)
        recuperados_ids = [item["agendamento_id"] for item in recuperadas]
        self.assertIn(ag_consulta.id, recuperados_ids)
        self.assertIn(ag_exame.id, recuperados_ids)
        self.assertNotIn(ag_confirmada.id, recuperados_ids)  # O confirmado foi protegido!

        # Os horários recuperados devem estar LIVRES novamente no banco
        h_cons_check = self.agenda_dao.buscar_horario_por_id(h_consulta.id)
        self.assertEqual(h_cons_check.status, StatusHorario.LIVRE)

        h_ex_check = self.agenda_dao.buscar_horario_por_id(h_exame.id)
        self.assertEqual(h_ex_check.status, StatusHorario.LIVRE)

    # =========================================================================
    # RN03 - RESTRIÇÃO POR REINCIDÊNCIA DE ABSENTEÍSMO
    # =========================================================================
    def test_rn03_bloqueio_por_reincidencia_e_acolhimento(self):
        """
        RN03: Três faltas não justificadas bloqueiam agendamento online.
        Atendimento presencial no setor de acolhimento desabona e restabelece.
        """
        paciente = self.usuario_dao.criar_paciente(
            Paciente(None, "Daniel", "66666666666", "daniel@rn.com", "h", "44996", "700400000000004", date(1991, 4, 4), faltas_nao_justificadas=2)
        )

        agenda = AgendaDiaria(None, self.ubs.id, self.medico.id, date(2026, 12, 20), time(14, 0), time(15, 0))
        agenda.gerar_horarios(20)
        self.agenda_dao.criar(agenda)

        # Paciente com 2 faltas ainda pode agendar online
        pode, _ = paciente.pode_agendar_online()
        self.assertTrue(pode)

        # Agenda e comete a 3ª falta
        ag = self.agendamento_service.agendar_consulta(paciente.id, agenda.horarios[0].id, "Rotina")
        self.absenteismo_service.registrar_falta(ag.id)

        # Paciente agora possui 3 faltas -> Bloqueado!
        pac_atualizado = self.usuario_dao.buscar_paciente_por_id(paciente.id)
        self.assertEqual(pac_atualizado.faltas_nao_justificadas, 3)
        self.assertTrue(pac_atualizado.esta_bloqueado())

        # Tentar novo agendamento online deve lançar PermissionError com instrução de acolhimento
        with self.assertRaises(PermissionError) as ctx:
            self.agendamento_service.agendar_consulta(paciente.id, agenda.horarios[1].id, "Nova consulta")
        self.assertIn("acolhimento presencial", str(ctx.exception).lower())

        # Paciente comparece ao acolhimento e gestor justifica a falta com atestado
        faltas = self.agendamento_dao.listar_faltas_paciente(paciente.id)
        falta_id = faltas[0]["id"]
        res_abono = self.absenteismo_service.acolher_e_justificar_falta(
            registro_falta_id=falta_id,
            motivo_justificativa="Atestado de internação hospitalar apresentado no acolhimento",
            gestor_id=self.gestor.id,
        )
        self.assertTrue(res_abono["sucesso"])

        # Paciente tem contador decrementado para 2 e desbloqueia!
        pac_desbloqueado = self.usuario_dao.buscar_paciente_por_id(paciente.id)
        self.assertEqual(pac_desbloqueado.faltas_nao_justificadas, 2)
        self.assertFalse(pac_desbloqueado.esta_bloqueado())

        # Agora consegue agendar novamente
        novo_ag = self.agendamento_service.agendar_consulta(paciente.id, agenda.horarios[1].id, "Nova consulta")
        self.assertIsNotNone(novo_ag.id)

    # =========================================================================
    # RN04 - GERAÇÃO DINÂMICA DA GRADE
    # =========================================================================
    def test_rn04_geracao_dinamica_grade(self):
        """RN04: Parametrização por turno e duração do procedimento."""
        agenda = AgendaDiaria(
            id=None,
            unidade_id=self.ubs.id,
            profissional_id=self.medico.id,
            data_agenda=date(2026, 12, 22),
            turno_inicio=time(8, 0),
            turno_fim=time(9, 0),  # 60 minutos
        )

        # Consulta: 20 min -> 3 blocos
        horarios_consulta = agenda.gerar_horarios(duracao_minutos=20)
        self.assertEqual(len(horarios_consulta), 3)

        # Exame: 30 min -> 2 blocos
        horarios_exame = agenda.gerar_horarios(duracao_minutos=30)
        self.assertEqual(len(horarios_exame), 2)

        # Vacina: 5 min -> 12 blocos
        horarios_vacina = agenda.gerar_horarios(duracao_minutos=5)
        self.assertEqual(len(horarios_vacina), 12)


if __name__ == "__main__":
    unittest.main()
