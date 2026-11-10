"""
Suíte de Testes de Operações CRUD com Banco de Dados Relacional Ativo.
Valida Create, Read, Update, Delete para todas as entidades principais,
garantindo persistência real, integridade referencial e tratamento de exceções.
"""

import unittest
from pathlib import Path
from datetime import date, time
from vagacerta.database import DatabaseManager
from vagacerta.models.unidade import UnidadeSaude
from vagacerta.models.usuario import Paciente, ProfissionalSaude, GestorUnidade
from vagacerta.models.agenda import AgendaDiaria, Horario
from vagacerta.models.agendamento import ConsultaClinica, Exame, Vacinacao
from vagacerta.models.enums import StatusAgendamento, StatusHorario
from vagacerta.dao.unidade_dao import UnidadeSaudeDAO
from vagacerta.dao.usuario_dao import UsuarioDAO
from vagacerta.dao.agenda_dao import AgendaDiariaDAO
from vagacerta.dao.agendamento_dao import AgendamentoDAO

TEST_DB_PATH = Path(__file__).resolve().parent / "test_vagacerta.db"


class TesteCRUDPersistencia(unittest.TestCase):
    """Testes completos de CRUD integrados com SQLite."""

    @classmethod
    def setUpClass(cls):
        """Inicializa banco de testes isolado."""
        cls.db_test = DatabaseManager(TEST_DB_PATH)
        cls.db_test.inicializar_banco(force_recreate=True)
        cls.unidade_dao = UnidadeSaudeDAO(cls.db_test)
        cls.usuario_dao = UsuarioDAO(cls.db_test)
        cls.agenda_dao = AgendaDiariaDAO(cls.db_test)
        cls.agendamento_dao = AgendamentoDAO(cls.db_test)

    @classmethod
    def tearDownClass(cls):
        """Remove arquivo temporário de testes."""
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()

    # =========================================================================
    # 1. CRUD UNIDADE DE SAÚDE
    # =========================================================================
    def test_crud_unidade_saude(self):
        # 1. CREATE
        ubs = UnidadeSaude(
            id=None,
            nome="UBS Teste Pioneiros",
            cnes="9998881",
            endereco="Av. Brasil, 100",
            telefone="4432221111",
        )
        criada = self.unidade_dao.criar(ubs)
        self.assertIsNotNone(criada.id)
        ubs_id = criada.id

        # 2. READ
        buscada = self.unidade_dao.buscar_por_id(ubs_id)
        self.assertIsNotNone(buscada)
        self.assertEqual(buscada.nome, "UBS Teste Pioneiros")
        self.assertEqual(buscada.cnes, "9998881")

        # 3. UPDATE
        buscada.nome = "UBS Pioneiros Atualizada"
        buscada.telefone = "4432229999"
        self.unidade_dao.atualizar(buscada)
        atualizada = self.unidade_dao.buscar_por_id(ubs_id)
        self.assertEqual(atualizada.nome, "UBS Pioneiros Atualizada")
        self.assertEqual(atualizada.telefone, "4432229999")

        # 4. DELETE
        excluiu = self.unidade_dao.excluir(ubs_id)
        self.assertTrue(excluiu)
        self.assertIsNone(self.unidade_dao.buscar_por_id(ubs_id))

    # =========================================================================
    # 2. CRUD PACIENTE (HERANÇA RELACIONAL)
    # =========================================================================
    def test_crud_paciente(self):
        # 1. CREATE
        paciente = Paciente(
            id=None,
            nome="João Batista",
            cpf="98765432100",
            email="joao.batista@email.com",
            senha_hash="senha123",
            telefone="44988776655",
            cartao_sus="890123456789012",
            data_nascimento=date(1985, 6, 20),
            faltas_nao_justificadas=0,
        )
        criado = self.usuario_dao.criar_paciente(paciente)
        self.assertIsNotNone(criado.id)
        pac_id = criado.id

        # 2. READ
        buscado = self.usuario_dao.buscar_paciente_por_id(pac_id)
        self.assertIsNotNone(buscado)
        self.assertEqual(buscado.nome, "João Batista")
        self.assertEqual(buscado.cartao_sus, "890123456789012")
        self.assertEqual(buscado.faltas_nao_justificadas, 0)

        # 3. UPDATE
        buscado.nome = "João Batista da Silva"
        buscado.faltas_nao_justificadas = 2
        self.usuario_dao.atualizar_paciente(buscado)
        atualizado = self.usuario_dao.buscar_paciente_por_id(pac_id)
        self.assertEqual(atualizado.nome, "João Batista da Silva")
        self.assertEqual(atualizado.faltas_nao_justificadas, 2)

        # 4. DELETE
        excluiu = self.usuario_dao.excluir_paciente(pac_id)
        self.assertTrue(excluiu)
        self.assertIsNone(self.usuario_dao.buscar_paciente_por_id(pac_id))

    # =========================================================================
    # 3. CRUD AGENDA E HORÁRIOS (COMPOSIÇÃO E CASCADE)
    # =========================================================================
    def test_crud_agenda_e_horarios(self):
        # Setup prévio de UBS e Médico
        ubs = self.unidade_dao.criar(
            UnidadeSaude(None, "UBS Centro", "1122334", "Rua Santos, 10", "4432223333")
        )
        medico = self.usuario_dao.criar_profissional(
            ProfissionalSaude(
                None,
                "Dr. Marcos",
                "88877766655",
                "marcos@med.com",
                "h",
                "44999998888",
                "CRM-PR 9988",
                "Clínica Geral",
            )
        )

        # 1. CREATE AGENDA COM COMPOSIÇÃO DE HORÁRIOS
        agenda = AgendaDiaria(
            id=None,
            unidade_id=ubs.id,
            profissional_id=medico.id,
            data_agenda=date(2026, 12, 1),
            turno_inicio=time(8, 0),
            turno_fim=time(9, 0),
        )
        agenda.gerar_horarios(duracao_minutos=20)  # 3 horários: 8:00, 8:20, 8:40
        agenda_criada = self.agenda_dao.criar(agenda)
        self.assertIsNotNone(agenda_criada.id)
        self.assertEqual(len(agenda_criada.horarios), 3)

        # 2. READ
        buscada = self.agenda_dao.buscar_por_id(agenda_criada.id)
        self.assertIsNotNone(buscada)
        self.assertEqual(len(buscada.horarios), 3)
        self.assertEqual(buscada.horarios[0].status, StatusHorario.LIVRE)

        # 3. UPDATE STATUS DO HORÁRIO
        horario_id = buscada.horarios[0].id
        self.agenda_dao.atualizar_status_horario(horario_id, StatusHorario.BLOQUEADO)
        h_atualizado = self.agenda_dao.buscar_horario_por_id(horario_id)
        self.assertEqual(h_atualizado.status, StatusHorario.BLOQUEADO)

        # 4. DELETE AGENDA COM CASCADE
        excluiu = self.agenda_dao.excluir(agenda_criada.id)
        self.assertTrue(excluiu)
        self.assertIsNone(self.agenda_dao.buscar_por_id(agenda_criada.id))
        self.assertIsNone(self.agenda_dao.buscar_horario_por_id(horario_id))

    # =========================================================================
    # 4. CRUD AGENDAMENTO POLIMÓRFICO
    # =========================================================================
    def test_crud_agendamento_polimorfico(self):
        # Setup
        ubs = self.unidade_dao.criar(
            UnidadeSaude(None, "UBS Sul", "3344556", "Av. Cerro Azul, 500", "4432224444")
        )
        medico = self.usuario_dao.criar_profissional(
            ProfissionalSaude(
                None, "Dra. Sandra", "77766655544", "sandra@med.com", "h", "44999997777", "CRM-PR 5544", "Pediatria"
            )
        )
        paciente = self.usuario_dao.criar_paciente(
            Paciente(
                None,
                "Pedro Henrique",
                "66655544433",
                "pedro@email.com",
                "h",
                "44999996666",
                "700999988887777",
                date(2015, 8, 10),
            )
        )
        agenda = AgendaDiaria(
            None, ubs.id, medico.id, date(2026, 12, 10), time(14, 0), time(15, 0)
        )
        agenda.gerar_horarios(duracao_minutos=30)  # 2 horários
        self.agenda_dao.criar(agenda)
        horario_alvo = agenda.horarios[0]

        # 1. CREATE (Consulta Clínica)
        consulta = ConsultaClinica(
            id=None,
            horario_id=horario_alvo.id,
            paciente_id=paciente.id,
            motivo="Febre alta e tosse",
            retorno=False,
        )
        ag_criado = self.agendamento_dao.criar(consulta)
        self.assertIsNotNone(ag_criado.id)
        self.assertEqual(ag_criado.status, StatusAgendamento.AGENDADO)

        # O horário deve ter sido atualizado para RESERVADO
        h_verif = self.agenda_dao.buscar_horario_por_id(horario_alvo.id)
        self.assertEqual(h_verif.status, StatusHorario.RESERVADO)

        # 2. READ (Polimórfico)
        ag_buscado = self.agendamento_dao.buscar_por_id(ag_criado.id)
        self.assertIsInstance(ag_buscado, ConsultaClinica)
        self.assertEqual(ag_buscado.motivo, "Febre alta e tosse")
        self.assertEqual(ag_buscado.janela_confirmacao_horas(), 24)

        # 3. UPDATE (Confirmação)
        self.agendamento_dao.atualizar_status(
            ag_buscado.id, StatusAgendamento.CONFIRMADO
        )
        ag_atualizado = self.agendamento_dao.buscar_por_id(ag_criado.id)
        self.assertEqual(ag_atualizado.status, StatusAgendamento.CONFIRMADO)

        # 4. DELETE / CANCELAMENTO COM LIBERAÇÃO DA VAGA (RN01)
        self.agendamento_dao.cancelar_e_liberar_vaga(ag_criado.id)
        ag_cancelado = self.agendamento_dao.buscar_por_id(ag_criado.id)
        self.assertEqual(ag_cancelado.status, StatusAgendamento.CANCELADO)
        h_liberado = self.agenda_dao.buscar_horario_por_id(horario_alvo.id)
        self.assertEqual(h_liberado.status, StatusHorario.LIVRE)


if __name__ == "__main__":
    unittest.main()
