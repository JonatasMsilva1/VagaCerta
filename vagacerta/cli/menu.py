"""
Interface de Linha de Comando (CLI) Interativa do VagaCerta.
Permite executar todas as operações CRUD, testar polimorfismo,
simular o motor de autoliberação e consultar relatórios de BI.
"""

from datetime import date, time, datetime
from typing import Optional
from vagacerta.database import db
from vagacerta.models.unidade import UnidadeSaude
from vagacerta.models.usuario import Paciente, ProfissionalSaude
from vagacerta.models.agenda import AgendaDiaria
from vagacerta.models.enums import StatusHorario
from vagacerta.dao.unidade_dao import UnidadeSaudeDAO
from vagacerta.dao.usuario_dao import UsuarioDAO
from vagacerta.dao.agenda_dao import AgendaDiariaDAO
from vagacerta.dao.agendamento_dao import AgendamentoDAO
from vagacerta.services.agendamento_service import AgendamentoService
from vagacerta.services.absenteismo_service import AbsenteismoService
from vagacerta.services.relatorios_service import RelatoriosService


class VagaCertaCLI:
    """Menu interativo do sistema VagaCerta."""

    def __init__(self):
        self.unidade_dao = UnidadeSaudeDAO(db)
        self.usuario_dao = UsuarioDAO(db)
        self.agenda_dao = AgendaDiariaDAO(db)
        self.agendamento_dao = AgendamentoDAO(db)
        self.agendamento_service = AgendamentoService(
            self.agendamento_dao, self.agenda_dao, self.usuario_dao
        )
        self.absenteismo_service = AbsenteismoService(
            self.agendamento_dao, self.usuario_dao
        )
        self.relatorios_service = RelatoriosService(db)

    def iniciar(self) -> None:
        """Loop principal do menu CLI."""
        while True:
            print("\n" + "=" * 65)
            print("         SISTEMA VAGACERTA - UBS & COMBATE AO ABSENTEÍSMO")
            print("=" * 65)
            print(" [1] Pacientes (CRUD e Status de Bloqueio RN03)")
            print(" [2] Profissionais de Saúde e Unidades UBS (CRUD)")
            print(" [3] Gerar Grade Diária de Atendimentos (RN04 - Composição)")
            print(" [4] Realizar Agendamento (Consulta / Exame / Vacina - Polimorfismo)")
            print(" [5] Confirmar Presença (RN02)")
            print(" [6] Executar Motor de Autoliberação de Vagas (RN02)")
            print(" [7] Registrar Falta ou Acolher Justificativa (RN03)")
            print(" [8] Relatório de Business Intelligence (BI & Absenteísmo)")
            print(" [9] Executar Demonstração Automatizada Ponta a Ponta")
            print(" [0] Sair")
            print("=" * 65)

            opcao = input("Selecione uma opção: ").strip()

            if opcao == "1":
                self.menu_pacientes()
            elif opcao == "2":
                self.menu_profissionais_ubs()
            elif opcao == "3":
                self.menu_gerar_grade()
            elif opcao == "4":
                self.menu_agendar()
            elif opcao == "5":
                self.menu_confirmar()
            elif opcao == "6":
                self.menu_motor_autoliberacao()
            elif opcao == "7":
                self.menu_faltas_acolhimento()
            elif opcao == "8":
                self.menu_relatorios()
            elif opcao == "9":
                self.executar_demonstracao_completa()
            elif opcao == "0":
                print("\nEncerrando VagaCerta. Até logo!")
                break
            else:
                print("\n[!] Opção inválida. Tente novamente.")

    # =========================================================================
    # MENUS ESPECÍFICOS
    # =========================================================================
    def menu_pacientes(self) -> None:
        print("\n--- GESTÃO DE PACIENTES (CRUD) ---")
        print("1. Listar Pacientes")
        print("2. Cadastrar Novo Paciente")
        print("3. Atualizar Paciente")
        print("4. Excluir Paciente")
        print("5. Consultar Extrato de Assiduidade e Bloqueio")
        sub = input("Escolha: ").strip()

        if sub == "1":
            pacientes = self.usuario_dao.listar_pacientes()
            print(f"\nTotal: {len(pacientes)} pacientes cadastrados:")
            for p in pacientes:
                bloq = " [BLOQUEADO - RN03]" if p.esta_bloqueado() else " [Apto Online]"
                print(
                    f" ID {p.id:02d} | {p.nome:<25} | CPF: {p.cpf} | SUS: {p.cartao_sus} | Faltas: {p.faltas_nao_justificadas}{bloq}"
                )

        elif sub == "2":
            try:
                nome = input("Nome completo: ").strip()
                cpf = input("CPF (11 dígitos): ").strip()
                email = input("E-mail: ").strip()
                telefone = input("Telefone: ").strip()
                sus = input("Cartão SUS (15 dígitos): ").strip()
                nasc = input("Data Nascimento (AAAA-MM-DD): ").strip()
                p = Paciente(
                    id=None,
                    nome=nome,
                    cpf=cpf,
                    email=email,
                    senha_hash="hash_padrao",
                    telefone=telefone,
                    cartao_sus=sus,
                    data_nascimento=nasc,
                )
                criado = self.usuario_dao.criar_paciente(p)
                print(f"[OK] Paciente cadastrado com sucesso! ID gerado: {criado.id}")
            except Exception as e:
                print(f"[ERRO] Falha ao cadastrar paciente: {e}")

        elif sub == "3":
            try:
                pid = int(input("ID do paciente a atualizar: "))
                paciente = self.usuario_dao.buscar_paciente_por_id(pid)
                if not paciente:
                    print("[!] Paciente não encontrado.")
                    return
                print(f"Editando: {paciente.nome}")
                novo_nome = input(f"Novo nome [{paciente.nome}]: ").strip()
                novo_tel = input(f"Novo telefone [{paciente.telefone}]: ").strip()
                if novo_nome:
                    paciente.nome = novo_nome
                if novo_tel:
                    paciente.telefone = novo_tel
                self.usuario_dao.atualizar_paciente(paciente)
                print("[OK] Paciente atualizado com sucesso!")
            except Exception as e:
                print(f"[ERRO] {e}")

        elif sub == "4":
            try:
                pid = int(input("ID do paciente a excluir: "))
                sucesso = self.usuario_dao.excluir_paciente(pid)
                if sucesso:
                    print(f"[OK] Paciente {pid} excluído com sucesso.")
                else:
                    print(f"[!] Paciente {pid} não encontrado.")
            except Exception as e:
                print(f"[ERRO] {e}")

        elif sub == "5":
            try:
                pid = int(input("ID do paciente: "))
                extrato = self.absenteismo_service.obter_extrato_paciente(pid)
                print(f"\nPaciente: {extrato['nome']} (SUS: {extrato['cartao_sus']})")
                print(f"Faltas não justificadas: {extrato['faltas_nao_justificadas']}")
                print(f"Status Agendamento Online: {extrato['motivo_status']}")
            except Exception as e:
                print(f"[ERRO] {e}")

    def menu_profissionais_ubs(self) -> None:
        print("\n--- PROFISSIONAIS E UBS ---")
        print("1. Listar Unidades Básicas de Saúde (UBS)")
        print("2. Listar Profissionais de Saúde")
        print("3. Cadastrar Nova UBS")
        sub = input("Escolha: ").strip()

        if sub == "1":
            unidades = self.unidade_dao.listar_todas()
            for u in unidades:
                print(f" UBS ID {u.id} | {u.nome} | CNES: {u.cnes} | Tel: {u.telefone}")
        elif sub == "2":
            profissionais = self.usuario_dao.listar_profissionais()
            for pr in profissionais:
                print(
                    f" PROF ID {pr.id} | {pr.nome} | {pr.especialidade} | Reg: {pr.registro_conselho}"
                )
        elif sub == "3":
            try:
                nome = input("Nome da UBS: ").strip()
                cnes = input("CNES (7 dígitos): ").strip()
                endereco = input("Endereço: ").strip()
                tel = input("Telefone: ").strip()
                ubs = self.unidade_dao.criar(
                    UnidadeSaude(None, nome, cnes, endereco, tel)
                )
                print(f"[OK] UBS criada com ID {ubs.id}")
            except Exception as e:
                print(f"[ERRO] {e}")

    def menu_gerar_grade(self) -> None:
        print("\n--- GERAÇÃO DINÂMICA DA GRADE (RN04 - COMPOSIÇÃO) ---")
        try:
            unidades = self.unidade_dao.listar_todas()
            if not unidades:
                print("[!] Nenhuma UBS cadastrada.")
                return
            ubs_id = unidades[0].id

            profs = self.usuario_dao.listar_profissionais()
            if not profs:
                print("[!] Nenhum profissional cadastrado.")
                return

            print("Selecione o profissional:")
            for p in profs:
                print(f" [{p.id}] {p.nome} - {p.especialidade}")
            prof_id = int(input("ID do Profissional: "))

            data_str = input("Data da agenda (AAAA-MM-DD): ").strip()
            data_agenda = date.fromisoformat(data_str)

            print("Tipo de atendimento para parametrizar a duração (RN04):")
            print(" [1] Consulta Clínica (20 min)")
            print(" [2] Exame Diagnóstico (30 min)")
            print(" [3] Vacinação (5 min)")
            tipo_op = input("Opção: ").strip()
            duracao = 20 if tipo_op == "1" else (30 if tipo_op == "2" else 5)

            hora_ini_str = input("Horário de início do turno (HH:MM) [08:00]: ").strip() or "08:00"
            hora_fim_str = input("Horário de término do turno (HH:MM) [12:00]: ").strip() or "12:00"

            agenda = AgendaDiaria(
                id=None,
                unidade_id=ubs_id,
                profissional_id=prof_id,
                data_agenda=data_agenda,
                turno_inicio=time.fromisoformat(hora_ini_str),
                turno_fim=time.fromisoformat(hora_fim_str),
            )
            agenda.gerar_horarios(duracao_minutos=duracao)
            criada = self.agenda_dao.criar(agenda)

            print(f"\n[OK] Grade gerada com sucesso! ID da Agenda: {criada.id}")
            print(f"Total de {len(criada.horarios)} horários discretos de {duracao} minutos criados:")
            for h in criada.horarios[:8]:
                print(f"   - Horário ID {h.id}: {h.hora_inicio.strftime('%H:%M')} às {h.hora_fim.strftime('%H:%M')} [{h.status.value}]")
            if len(criada.horarios) > 8:
                print(f"   ... e mais {len(criada.horarios) - 8} horários.")
        except Exception as e:
            print(f"[ERRO] {e}")

    def menu_agendar(self) -> None:
        print("\n--- REALIZAR AGENDAMENTO POLIMÓRFICO ---")
        try:
            paciente_id = int(input("ID do Paciente: "))
            horario_id = int(input("ID do Horário Livre desejado: "))

            print("Qual o tipo de procedimento?")
            print(" [1] Consulta Clínica (Janela: 24h)")
            print(" [2] Exame (Janela: 48h c/ preparo)")
            print(" [3] Vacinação (Isenta de confirmação)")
            tp = input("Opção: ").strip()

            if tp == "1":
                motivo = input("Motivo da consulta: ").strip()
                retorno = input("É retorno médico? (s/n): ").strip().lower() == "s"
                ag = self.agendamento_service.agendar_consulta(
                    paciente_id, horario_id, motivo, retorno
                )
            elif tp == "2":
                exame_nome = input("Tipo do exame (ex: Sangue, ECG): ").strip()
                preparo = input("Orientações de preparo: ").strip()
                ag = self.agendamento_service.agendar_exame(
                    paciente_id, horario_id, exame_nome, preparo
                )
            elif tp == "3":
                imuno = input("Imunobiológico (Vacina): ").strip()
                dose = input("Dose (ex: 1ª Dose, Reforço): ").strip()
                ag = self.agendamento_service.agendar_vacinacao(
                    paciente_id, horario_id, imuno, dose
                )
            else:
                print("[!] Opção inválida.")
                return

            print(f"\n[OK] Agendamento #{ag.id} realizado com sucesso!")
            print(f"Tipo: {ag.tipo().value}")
            print(f"Janela de Confirmação Obrigatória (RN02): {ag.janela_confirmacao_horas()} horas antes")
            print(f"Orientações ao Paciente:\n-> {ag.gerar_instrucoes_atendimento()}")

        except Exception as e:
            print(f"[BLOQUEIO / ERRO] {e}")

    def menu_confirmar(self) -> None:
        print("\n--- CONFIRMAR PRESENÇA (RN02) ---")
        try:
            ag_id = int(input("ID do Agendamento a confirmar: "))
            ag = self.agendamento_service.confirmar_presenca(ag_id)
            print(f"[OK] Agendamento #{ag.id} confirmado com sucesso!")
            print(f"Horário de confirmação registrado: {ag.confirmado_em}")
            print("A vaga está garantida e protegida contra descarte automático.")
        except Exception as e:
            print(f"[ERRO] {e}")

    def menu_motor_autoliberacao(self) -> None:
        print("\n--- MOTOR DE AUTOLIBERAÇÃO E COMBATE AO ABSENTEÍSMO (RN02) ---")
        print("Executando varredura em tempo real para detectar vagas que estouraram a janela de confirmação...")
        recuperadas = self.agendamento_service.executar_motor_autoliberacao()
        if not recuperadas:
            print("[INFO] Nenhuma vaga precisou ser autoliberada no momento. Todos os horários estão confirmados ou fora da janela de descarte.")
        else:
            print(f"[SUCESSO] O motor recuperou e reofertou {len(recuperadas)} vaga(s) para a fila pública:")
            for item in recuperadas:
                print(f" -> Agendamento #{item['agendamento_id']} ({item['tipo']}) - Paciente: {item['paciente']}")
                print(f"    Data/Hora: {item['data']} às {item['horario']}")
                print(f"    Motivo: {item['motivo_liberacao']}")

    def menu_faltas_acolhimento(self) -> None:
        print("\n--- GESTÃO DE FALTAS E ACOLHIMENTO (RN03) ---")
        print("1. Registrar Falta de Paciente")
        print("2. Acolher Paciente e Justificar Falta (Abono)")
        op = input("Opção: ").strip()

        if op == "1":
            try:
                ag_id = int(input("ID do agendamento não comparecido: "))
                res = self.absenteismo_service.registrar_falta(ag_id)
                print(f"\n[OK] {res['aviso']}")
                print(f"Total de faltas acumuladas por {res['paciente_nome']}: {res['total_faltas_nao_justificadas']}")
            except Exception as e:
                print(f"[ERRO] {e}")
        elif op == "2":
            try:
                paciente_id = int(input("ID do Paciente em acolhimento: "))
                faltas = self.agendamento_dao.listar_faltas_paciente(paciente_id)
                faltas_injustificadas = [f for f in faltas if not f["justificada"]]
                if not faltas_injustificadas:
                    print("[INFO] Não há faltas pendentes de justificativa para este paciente.")
                    return

                print("\nFaltas pendentes:")
                for f in faltas_injustificadas:
                    print(f" [ID Falta: {f['id']}] Ocorrida em {f['data_falta']}")

                falta_id = int(input("ID da falta a abonar: "))
                motivo = input("Motivo/Atestado apresentado: ").strip()
                gestores = self.usuario_dao.listar_gestores()
                gestor_id = gestores[0].id if gestores else 1

                res = self.absenteismo_service.acolher_e_justificar_falta(
                    falta_id, motivo, gestor_id
                )
                print(f"[OK] {res['mensagem']}")
            except Exception as e:
                print(f"[ERRO] {e}")

    def menu_relatorios(self) -> None:
        print("\n--- MÓDULO DE BUSINESS INTELLIGENCE (BI - F6) ---")
        dados = self.relatorios_service.relatorio_geral_absenteismo()
        print("\n" + "-" * 50)
        print(" INDICADORES ESTRATÉGICOS DA REDE DE SAÚDE")
        print("-" * 50)
        print(f" Total de Agendamentos:       {dados['total_agendamentos']}")
        print(f" Agendados (Aguardando):      {dados['agendados_pendentes']}")
        print(f" Confirmados Ativos:          {dados['confirmados']}")
        print(f" Atendimentos Realizados:     {dados['realizados']}")
        print(f" Faltas Registradas:          {dados['faltas']}")
        print(f" Vagas Descartadas/Liberadas: {dados['cancelados_autoliberados']}")
        print(f" TAXA GERAL DE ABSENTEÍSMO:   {dados['taxa_absenteismo_percentual']}%")
        print("-" * 50)
        print(f" Capacidade Total da Grade:   {dados['total_horarios_grade']} horários")
        print(f" Vagas Livres para Reserva:   {dados['horarios_disponiveis_livres']}")
        print(f" Taxa de Ocupação da Grade:   {dados['taxa_ocupacao_grade_percentual']}%")
        print("-" * 50)

        criticos = self.relatorios_service.relatorio_pacientes_criticos(limite_faltas=2)
        if criticos:
            print("\n[ALERTA DE GESTÃO] Pacientes com risco de bloqueio ou bloqueados:")
            for c in criticos:
                status = "BLOQUEADO (RN03)" if c["bloqueado"] else "ALERTA (2 faltas)"
                print(f" * {c['nome']} (SUS: {c['cartao_sus']}) - {c['faltas_nao_justificadas']} faltas [{status}]")

    def executar_demonstracao_completa(self) -> None:
        """Executa um roteiro automatizado ponta a ponta sem pausas manuais."""
        from vagacerta.main import demonstracao_ponta_a_ponta
        demonstracao_ponta_a_ponta()
