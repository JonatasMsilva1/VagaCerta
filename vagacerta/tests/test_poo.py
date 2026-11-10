"""
Suíte de Testes dos Pilares de Programação Orientada a Objetos (POO).
Valida Herança, Composição e Polimorfismo no modelo de domínio do VagaCerta.
"""

import unittest
from datetime import date, time, datetime, timedelta
from vagacerta.models.enums import PerfilAcesso, StatusHorario, StatusAgendamento, TipoAgendamento
from vagacerta.models.usuario import Usuario, Paciente, ProfissionalSaude, GestorUnidade
from vagacerta.models.agenda import AgendaDiaria, Horario
from vagacerta.models.agendamento import Agendamento, ConsultaClinica, Exame, Vacinacao


class TestePilaresPOO(unittest.TestCase):
    """Verifica a conformidade rigorosa dos 3 pilares da POO."""

    # =========================================================================
    # 1. TESTES DE HERANÇA
    # =========================================================================
    def test_heranca_hierarquia_usuarios(self):
        """Verifica herança legítima a partir da classe base abstrata Usuario."""
        paciente = Paciente(
            id=1,
            nome="Maria Silva",
            cpf="12345678901",
            email="maria@email.com",
            senha_hash="hash1",
            telefone="44999990000",
            cartao_sus="700111122223333",
            data_nascimento=date(1990, 1, 1),
        )
        medico = ProfissionalSaude(
            id=2,
            nome="Dr. Roberto",
            cpf="23456789012",
            email="roberto@email.com",
            senha_hash="hash2",
            telefone="44999991111",
            registro_conselho="CRM-PR 12345",
            especialidade="Cardiologia",
        )
        gestor = GestorUnidade(
            id=3,
            nome="Ana Diretora",
            cpf="34567890123",
            email="ana@email.com",
            senha_hash="hash3",
            telefone="44999992222",
            matricula="GES-001",
            cargo="Diretora UBS",
        )

        # Todas as subclasses devem ser instâncias da classe base Usuario
        self.assertIsInstance(paciente, Usuario)
        self.assertIsInstance(medico, Usuario)
        self.assertIsInstance(gestor, Usuario)

        # Classes filhas possuem atributos especializados que não existem na base
        self.assertEqual(paciente.cartao_sus, "700111122223333")
        self.assertEqual(medico.registro_conselho, "CRM-PR 12345")
        self.assertEqual(gestor.matricula, "GES-001")

        # Não deve ser possível instanciar a classe base abstrata diretamente
        with self.assertRaises(TypeError):
            Usuario(None, "X", "111", "x@x", "h", "t")

    # =========================================================================
    # 2. TESTES DE COMPOSIÇÃO
    # =========================================================================
    def test_composicao_agenda_e_horarios(self):
        """
        Verifica composição: AgendaDiaria contém e administra Horarios.
        Demonstra que Horario não herda de AgendaDiaria, mas é contido nela (has-a).
        """
        agenda = AgendaDiaria(
            id=10,
            unidade_id=1,
            profissional_id=2,
            data_agenda=date(2026, 11, 1),
            turno_inicio=time(8, 0),
            turno_fim=time(10, 0),
        )

        # A agenda inicia com lista vazia de horários
        self.assertEqual(len(agenda.horarios), 0)

        # Geração dinâmica dos horários compostos (RN04) de 30 min cada (8:00 às 10:00 = 4 horários)
        horarios = agenda.gerar_horarios(duracao_minutos=30)
        self.assertEqual(len(horarios), 4)
        self.assertEqual(agenda.total_horarios(), 4)

        # Verifica integridade dos objetos Horario compostos
        primeiro_horario = agenda.horarios[0]
        self.assertIsInstance(primeiro_horario, Horario)
        self.assertNotIsInstance(primeiro_horario, AgendaDiaria)  # Composição, não herança!
        self.assertEqual(primeiro_horario.hora_inicio, time(8, 0))
        self.assertEqual(primeiro_horario.hora_fim, time(8, 30))
        self.assertTrue(primeiro_horario.esta_livre())

        # Teste de ocupação pela composição
        primeiro_horario.reservar()
        self.assertFalse(primeiro_horario.esta_livre())
        self.assertEqual(agenda.taxa_ocupacao(), 25.0)  # 1 de 4 reservado = 25%

    # =========================================================================
    # 3. TESTES DE POLIMORFISMO
    # =========================================================================
    def test_polimorfismo_agendamentos(self):
        """
        Verifica polimorfismo: Diferentes especializações de Agendamento
        respondem de maneira distinta aos mesmos métodos de interface.
        """
        consulta = ConsultaClinica(
            id=1,
            horario_id=101,
            paciente_id=1,
            motivo="Hipertensão",
            retorno=True,
        )
        exame = Exame(
            id=2,
            horario_id=102,
            paciente_id=1,
            tipo_exame="Ultrassonografia",
            orientacao_preparo="Bexiga cheia, ingerir 4 copos d'água 1h antes.",
        )
        vacina = Vacinacao(
            id=3,
            horario_id=103,
            paciente_id=1,
            imunobiologico="Hepatite B",
            dose="2ª Dose",
        )

        # Todos derivam da mesma classe base polimórfica
        procedimentos: list[Agendamento] = [consulta, exame, vacina]

        # 1. Polimorfismo em janela_confirmacao_horas() - RN02
        janelas = [p.janela_confirmacao_horas() for p in procedimentos]
        self.assertEqual(janelas, [24, 48, 0])

        # 2. Polimorfismo em duracao_minutos() - RN04
        duracoes = [p.duracao_minutos() for p in procedimentos]
        self.assertEqual(duracoes, [20, 30, 5])

        # 3. Polimorfismo em exige_preparo()
        preparos = [p.exige_preparo() for p in procedimentos]
        self.assertEqual(preparos, [False, True, False])

        # 4. Polimorfismo na geração de instruções ao paciente
        for p in procedimentos:
            instrucoes = p.gerar_instrucoes_atendimento()
            self.assertIsInstance(instrucoes, str)
            self.assertTrue(len(instrucoes) > 20)

        # 5. Polimorfismo na regra de autoliberação por descarte (RN02)
        # Suponha que o atendimento é amanhã às 10:00 (daqui a 20 horas)
        data_atend = date.today() + timedelta(days=1)
        hora_atend = time(10, 0)
        agora = datetime.combine(date.today(), time(14, 0))  # 20h de antecedência

        # Exame exige 48h de confirmação. Como faltam 20h (< 48h) e não confirmou, deve autoliberar!
        self.assertTrue(exame.deve_ser_autoliberado(data_atend, hora_atend, agora))

        # Consulta exige 24h. Como faltam 20h (< 24h) e não confirmou, deve autoliberar!
        self.assertTrue(consulta.deve_ser_autoliberado(data_atend, hora_atend, agora))

        # Vacinação é isenta (janela 0h). Nunca deve ser autoliberada!
        self.assertFalse(vacina.deve_ser_autoliberado(data_atend, hora_atend, agora))


if __name__ == "__main__":
    unittest.main()
