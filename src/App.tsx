import React, { useState } from 'react';
import {
  Calendar,
  Clock,
  User,
  Stethoscope,
  Syringe,
  FileText,
  Database,
  Layers,
  Activity,
  CheckCircle2,
  RefreshCw,
  ShieldAlert,
  ArrowRight,
  BookOpen,
  Code2,
  Terminal,
} from 'lucide-react';

interface PacienteData {
  id: number;
  nome: string;
  cpf: string;
  cartaoSus: string;
  faltas: number;
  bloqueado: boolean;
}

interface HorarioData {
  id: number;
  hora: string;
  status: 'LIVRE' | 'RESERVADO' | 'BLOQUEADO';
  procedimento?: string;
  pacienteNome?: string;
  tipo?: 'CONSULTA' | 'EXAME' | 'VACINA';
  confirmado: boolean;
  janelaHoras: number;
}

export default function App() {
  const [activeTab, setActiveTab] = useState<'painel' | 'poo' | 'banco' | 'equipe'>('painel');

  const [pacientes, setPacientes] = useState<PacienteData[]>([
    {
      id: 1,
      nome: 'Lucas Pereira dos Santos',
      cpf: '444.555.666-77',
      cartaoSus: '700123456789012',
      faltas: 0,
      bloqueado: false,
    },
    {
      id: 2,
      nome: 'Ana Paula de Souza',
      cpf: '555.666.777-88',
      cartaoSus: '700987654321098',
      faltas: 1,
      bloqueado: false,
    },
    {
      id: 3,
      nome: 'Roberto Alves da Silva',
      cpf: '666.777.888-99',
      cartaoSus: '700555666777888',
      faltas: 3,
      bloqueado: true,
    },
  ]);

  const [horarios, setHorarios] = useState<HorarioData[]>([
    {
      id: 1,
      hora: '08:00 - 08:20',
      status: 'RESERVADO',
      procedimento: 'Consulta Clínica (Hipertensão)',
      pacienteNome: 'Lucas Pereira dos Santos',
      tipo: 'CONSULTA',
      confirmado: true,
      janelaHoras: 24,
    },
    {
      id: 2,
      hora: '08:20 - 08:40',
      status: 'RESERVADO',
      procedimento: 'Exame de Sangue / Glicemia',
      pacienteNome: 'Ana Paula de Souza',
      tipo: 'EXAME',
      confirmado: false,
      janelaHoras: 48,
    },
    {
      id: 3,
      hora: '08:40 - 09:00',
      status: 'RESERVADO',
      procedimento: 'Consulta Clínica (Retorno)',
      pacienteNome: 'Ana Paula de Souza',
      tipo: 'CONSULTA',
      confirmado: false,
      janelaHoras: 24,
    },
    {
      id: 4,
      hora: '09:00 - 09:05',
      status: 'RESERVADO',
      procedimento: 'Vacina Febre Amarela',
      pacienteNome: 'Lucas Pereira dos Santos',
      tipo: 'VACINA',
      confirmado: false,
      janelaHoras: 0,
    },
    { id: 5, hora: '09:20 - 09:40', status: 'LIVRE', confirmado: false, janelaHoras: 24 },
    { id: 6, hora: '09:40 - 10:00', status: 'LIVRE', confirmado: false, janelaHoras: 24 },
  ]);

  const [notificacoes, setNotificacoes] = useState<string[]>([
    'Sistema inicializado com banco SQLite relacional ativo e dados de seed carregados.',
    'RN01 e RN04 em vigor: grade gerada dinamicamente conforme parâmetros de tempo.',
  ]);

  const [selectedPacienteId, setSelectedPacienteId] = useState<number>(1);
  const [selectedProcedimento, setSelectedProcedimento] = useState<'CONSULTA' | 'EXAME' | 'VACINA'>('CONSULTA');

  const addLog = (msg: string) => {
    setNotificacoes((prev) => [msg, ...prev.slice(0, 9)]);
  };

  const executarMotorAutoliberacao = () => {
    let vagasLiberadas = 0;
    const novosHorarios = horarios.map((h) => {
      if (h.status === 'RESERVADO' && !h.confirmado && h.janelaHoras > 0) {
        vagasLiberadas++;
        addLog(
          `[RN02 - AUTOLIBERAÇÃO] Horário ${h.hora} (${h.procedimento}) foi devolvido à fila pública por falta de confirmação na janela de ${h.janelaHoras}h.`
        );
        return {
          ...h,
          status: 'LIVRE' as const,
          procedimento: undefined,
          pacienteNome: undefined,
          tipo: undefined,
          confirmado: false,
        };
      }
      return h;
    });

    setHorarios(novosHorarios);
    if (vagasLiberadas === 0) {
      addLog('[RN02] Nenhuma vaga precisou ser autoliberada no momento. Todas estão confirmadas ou são isentas.');
    } else {
      addLog(`[RN02 SUCESSO] ${vagasLiberadas} vaga(s) recuperada(s) para o SUS sem custo de infraestrutura!`);
    }
  };

  const tentarAgendamento = (horarioId: number) => {
    const paciente = pacientes.find((p) => p.id === selectedPacienteId);
    if (!paciente) return;

    if (paciente.bloqueado) {
      addLog(
        `[RN03 BLOQUEIO] Paciente ${paciente.nome} possui 3 faltas. Agendamento remoto RECUSADO. Acolhimento presencial exigido!`
      );
      return;
    }

    const horario = horarios.find((h) => h.id === horarioId);
    if (!horario || horario.status !== 'LIVRE') {
      addLog(`[RN01 ERRO] Horário ${horario?.hora} já se encontra reservado. Integridade UNIQUE garantida.`);
      return;
    }

    const procedNome =
      selectedProcedimento === 'CONSULTA'
        ? 'Consulta Clínica Geral'
        : selectedProcedimento === 'EXAME'
        ? 'Eletrocardiograma (ECG)'
        : 'Vacina Influenza';

    const janela = selectedProcedimento === 'CONSULTA' ? 24 : selectedProcedimento === 'EXAME' ? 48 : 0;

    setHorarios((prev) =>
      prev.map((h) =>
        h.id === horarioId
          ? {
              ...h,
              status: 'RESERVADO',
              procedimento: procedNome,
              pacienteNome: paciente.nome,
              tipo: selectedProcedimento,
              confirmado: selectedProcedimento === 'VACINA',
              janelaHoras: janela,
            }
          : h
      )
    );

    addLog(
      `[AGENDAMENTO CRIADO] Horário ${horario.hora} reservado com sucesso para ${paciente.nome} (${procedNome}). Janela: ${janela}h.`
    );
  };

  const confirmarHorario = (horarioId: number) => {
    setHorarios((prev) =>
      prev.map((h) => {
        if (h.id === horarioId) {
          addLog(`[CONFIRMAÇÃO RN02] Presença confirmada para o horário ${h.hora}. Vaga protegida contra autoliberação!`);
          return { ...h, confirmado: true };
        }
        return h;
      })
    );
  };

  const acolherPaciente = (pacienteId: number) => {
    setPacientes((prev) =>
      prev.map((p) => {
        if (p.id === pacienteId) {
          addLog(
            `[ACOLHIMENTO UBS - RN03] Paciente ${p.nome} acolhido presencialmente. Atestado validado por Gestor e falta abonada!`
          );
          return { ...p, faltas: Math.max(0, p.faltas - 1), bloqueado: false };
        }
        return p;
      })
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-50 px-6 py-4">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-teal-500/20 border border-teal-500/40 flex items-center justify-center text-teal-400 font-bold shadow-lg shadow-teal-500/10">
              VC
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold tracking-tight text-white">VagaCerta</h1>
                <span className="px-2 py-0.5 text-xs font-semibold rounded bg-teal-500/20 text-teal-300 border border-teal-500/30">
                  2º Bimestre Final
                </span>
                <span className="px-2 py-0.5 text-xs font-semibold rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                  Java 17 (Pure JDBC)
                </span>
                <span className="px-2 py-0.5 text-xs font-semibold rounded bg-sky-500/20 text-sky-300 border border-sky-500/30">
                  React + TypeScript
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Sistema de Agendamento e Combate ao Absenteísmo em Unidades Básicas de Saúde
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1 bg-slate-800/80 p-1 rounded-xl border border-slate-700">
            <button
              onClick={() => setActiveTab('painel')}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors flex items-center gap-1.5 ${
                activeTab === 'painel' ? 'bg-teal-600 text-white shadow' : 'text-slate-300 hover:text-white'
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              Simulador Operacional
            </button>
            <button
              onClick={() => setActiveTab('poo')}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors flex items-center gap-1.5 ${
                activeTab === 'poo' ? 'bg-teal-600 text-white shadow' : 'text-slate-300 hover:text-white'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              Pilares da POO
            </button>
            <button
              onClick={() => setActiveTab('banco')}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors flex items-center gap-1.5 ${
                activeTab === 'banco' ? 'bg-teal-600 text-white shadow' : 'text-slate-300 hover:text-white'
              }`}
            >
              <Database className="w-3.5 h-3.5" />
              Banco & CRUD
            </button>
            <button
              onClick={() => setActiveTab('equipe')}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors flex items-center gap-1.5 ${
                activeTab === 'equipe' ? 'bg-teal-600 text-white shadow' : 'text-slate-300 hover:text-white'
              }`}
            >
              <BookOpen className="w-3.5 h-3.5" />
              Equipe & Docs
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto w-full p-6 space-y-6">
        <div className="bg-gradient-to-r from-teal-950/60 via-slate-900 to-indigo-950/50 border border-teal-800/40 rounded-2xl p-5 flex flex-col md:flex-row items-center justify-between gap-4 shadow-xl">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs uppercase tracking-wider font-semibold text-teal-400">
                Alinhamento ONU: ODS 3 — Saúde e Bem-Estar (Metas 3.8 e 3.4)
              </span>
            </div>
            <h2 className="text-lg font-semibold text-slate-100">
              Otimização de Agenda Pública & Recuperação Automática de Vagas Ociosas
            </h2>
            <p className="text-xs text-slate-400 max-w-3xl leading-relaxed">
              O VagaCerta elimina o desperdício de consultas decorrente do absenteísmo sem exigir ampliação de infraestrutura
              física. As vagas não confirmadas são autoliberadas e reofertadas à fila pública através de regras polimórficas de negócio.
            </p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={executarMotorAutoliberacao}
              className="px-4 py-2.5 bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-500 hover:to-emerald-500 text-white font-medium text-xs rounded-xl shadow-lg shadow-teal-900/30 flex items-center gap-2 transition-all cursor-pointer"
            >
              <RefreshCw className="w-4 h-4" />
              Disparar Motor de Autoliberação (RN02)
            </button>
          </div>
        </div>

        {activeTab === 'painel' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="space-y-6">
              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-lg">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                    <User className="w-4 h-4 text-teal-400" />
                    Pacientes & Controle de Faltas (RN03)
                  </h3>
                  <span className="text-xs text-slate-400">Teto: 3 faltas</span>
                </div>
                <div className="space-y-3">
                  {pacientes.map((p) => (
                    <div
                      key={p.id}
                      onClick={() => setSelectedPacienteId(p.id)}
                      className={`p-3.5 rounded-xl border transition-all cursor-pointer ${
                        selectedPacienteId === p.id
                          ? 'bg-teal-950/40 border-teal-500/60 shadow-md shadow-teal-500/10'
                          : 'bg-slate-950/60 border-slate-800/80 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="text-xs font-semibold text-white">{p.nome}</p>
                          <p className="text-[11px] text-slate-400">SUS: {p.cartaoSus}</p>
                        </div>
                        {p.bloqueado ? (
                          <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-rose-500/20 text-rose-300 border border-rose-500/30 flex items-center gap-1">
                            <ShieldAlert className="w-3 h-3" /> Bloqueado (RN03)
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" /> Apto Online
                          </span>
                        )}
                      </div>
                      <div className="mt-3 flex items-center justify-between text-[11px] pt-2 border-t border-slate-800/60">
                        <span className="text-slate-400">
                          Faltas acumuladas: <strong className={p.faltas >= 3 ? 'text-rose-400' : 'text-slate-200'}>{p.faltas}</strong>
                        </span>
                        {p.bloqueado && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              acolherPaciente(p.id);
                            }}
                            className="text-[10px] bg-indigo-600/30 hover:bg-indigo-600/50 text-indigo-300 border border-indigo-500/30 px-2 py-0.5 rounded transition"
                          >
                            Acolher / Abonar Falta
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-4 p-3 bg-slate-950/80 rounded-xl border border-slate-800 text-[11px] text-slate-400 space-y-1">
                  <p className="font-semibold text-slate-300">Regra de Negócio RN03:</p>
                  <p>
                    3 faltas injustificadas bloqueiam agendamento remoto pelo próprio paciente, exigindo acolhimento presencial na UBS.
                  </p>
                </div>
              </div>

              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-lg space-y-3">
                <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <Stethoscope className="w-4 h-4 text-sky-400" />
                  Procedimento para Agendamento
                </h3>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    onClick={() => setSelectedProcedimento('CONSULTA')}
                    className={`p-2.5 rounded-xl border text-center transition ${
                      selectedProcedimento === 'CONSULTA'
                        ? 'bg-sky-600/30 border-sky-500 text-sky-200'
                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    <Stethoscope className="w-4 h-4 mx-auto mb-1" />
                    <span className="text-xs font-medium block">Consulta</span>
                    <span className="text-[10px] text-slate-400">20 min | 24h</span>
                  </button>
                  <button
                    onClick={() => setSelectedProcedimento('EXAME')}
                    className={`p-2.5 rounded-xl border text-center transition ${
                      selectedProcedimento === 'EXAME'
                        ? 'bg-amber-600/30 border-amber-500 text-amber-200'
                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    <FileText className="w-4 h-4 mx-auto mb-1" />
                    <span className="text-xs font-medium block">Exame</span>
                    <span className="text-[10px] text-slate-400">30 min | 48h</span>
                  </button>
                  <button
                    onClick={() => setSelectedProcedimento('VACINA')}
                    className={`p-2.5 rounded-xl border text-center transition ${
                      selectedProcedimento === 'VACINA'
                        ? 'bg-emerald-600/30 border-emerald-500 text-emerald-200'
                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    <Syringe className="w-4 h-4 mx-auto mb-1" />
                    <span className="text-xs font-medium block">Vacina</span>
                    <span className="text-[10px] text-slate-400">5 min | Isenta</span>
                  </button>
                </div>
              </div>
            </div>

            <div className="lg:col-span-2 space-y-6">
              <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-lg">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-4 border-b border-slate-800 gap-2">
                  <div>
                    <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-teal-400" />
                      Grade Diária — Dr. Carlos Eduardo Menezes (CRM-PR 34512)
                    </h3>
                    <p className="text-xs text-slate-400">
                      UBS Zona 7 — Maringá, PR | Turno: Manhã (RN04: Parametrização Dinâmica)
                    </p>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="flex items-center gap-1 text-slate-400">
                      <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Livre
                    </span>
                    <span className="flex items-center gap-1 text-slate-400">
                      <span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> Reservado
                    </span>
                  </div>
                </div>

                <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {horarios.map((h) => (
                    <div
                      key={h.id}
                      className={`p-4 rounded-xl border transition-all ${
                        h.status === 'LIVRE'
                          ? 'bg-slate-950/70 border-emerald-900/40 hover:border-emerald-500/60'
                          : 'bg-slate-950/90 border-slate-800'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                          <Clock className="w-3.5 h-3.5 text-teal-400" />
                          {h.hora}
                        </span>
                        {h.status === 'LIVRE' ? (
                          <span className="px-2 py-0.5 text-[10px] font-semibold rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                            LIVRE (RN01)
                          </span>
                        ) : (
                          <span
                            className={`px-2 py-0.5 text-[10px] font-semibold rounded border ${
                              h.confirmado
                                ? 'bg-teal-500/20 text-teal-300 border-teal-500/30'
                                : 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                            }`}
                          >
                            {h.confirmado ? 'CONFIRMADO' : 'AGENDADO (PENDENTE)'}
                          </span>
                        )}
                      </div>
                      {h.status === 'RESERVADO' ? (
                        <div className="mt-3 space-y-1.5 text-xs border-t border-slate-800/80 pt-2.5">
                          <p className="text-white font-medium">{h.procedimento}</p>
                          <p className="text-slate-400 text-[11px]">Paciente: {h.pacienteNome}</p>
                          <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1">
                            <span>Janela: {h.janelaHoras === 0 ? 'Isenta' : `${h.janelaHoras}h obrigatória`}</span>
                            {!h.confirmado && (
                              <button
                                onClick={() => confirmarHorario(h.id)}
                                className="px-2 py-0.5 rounded bg-teal-600/40 hover:bg-teal-600/60 text-teal-200 border border-teal-500/40 transition"
                              >
                                Confirmar Presença
                              </button>
                            )}
                          </div>
                        </div>
                      ) : (
                        <div className="mt-3 border-t border-slate-800/60 pt-2 flex items-center justify-between">
                          <span className="text-[11px] text-slate-400">Vaga disponível</span>
                          <button
                            onClick={() => tentarAgendamento(h.id)}
                            className="px-2.5 py-1 text-xs rounded-lg bg-teal-600 hover:bg-teal-500 text-white font-medium transition cursor-pointer flex items-center gap-1"
                          >
                            Reservar Agora <ArrowRight className="w-3 h-3" />
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                <div className="mt-6 bg-slate-950 rounded-xl p-3.5 border border-slate-800">
                  <div className="flex items-center gap-2 mb-2 text-xs font-semibold text-slate-300">
                    <Terminal className="w-3.5 h-3.5 text-teal-400" />
                    Auditoria de Eventos do Sistema VagaCerta:
                  </div>
                  <div className="space-y-1 max-h-36 overflow-y-auto text-[11px] font-mono text-slate-400">
                    {notificacoes.map((log, idx) => (
                      <p key={idx} className="leading-relaxed">
                        <span className="text-teal-400">[{new Date().toLocaleTimeString()}]</span> {log}
                      </p>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'poo' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-lg space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-sky-500/20 border border-sky-500/40 flex items-center justify-center text-sky-400">
                    <Layers className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-white text-sm">Pilar 1: Herança</h3>
                    <p className="text-xs text-sky-400">Hierarquias Legítimas</p>
                  </div>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Implementação genuína sem classes artificiais em dois eixos essenciais do sistema:
                </p>
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-[11px] font-mono space-y-1 text-slate-300">
                  <p className="text-sky-400 font-semibold">Usuario (Abstrata - ABC)</p>
                  <p className="pl-3">├─ Paciente (SUS, faltas, RN03)</p>
                  <p className="pl-3">├─ ProfissionalSaude (CRM, turno)</p>
                  <p className="pl-3">└─ GestorUnidade (Matrícula, BI)</p>
                </div>
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-[11px] font-mono space-y-1 text-slate-300">
                  <p className="text-sky-400 font-semibold">Agendamento (Abstrata - ABC)</p>
                  <p className="pl-3">├─ ConsultaClinica</p>
                  <p className="pl-3">├─ Exame</p>
                  <p className="pl-3">└─ Vacinacao</p>
                </div>
              </div>

              <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-lg space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-teal-500/20 border border-teal-500/40 flex items-center justify-center text-teal-400">
                    <Database className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-white text-sm">Pilar 2: Composição</h3>
                    <p className="text-xs text-teal-400">AgendaDiaria & Horario</p>
                  </div>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Justificativa técnica rigorosa de por que usar <strong>Composição e NÃO Herança</strong>:
                </p>
                <div className="space-y-2 text-xs text-slate-300">
                  <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                    <strong className="text-teal-400 block mb-1">1. Has-a vs. Is-a</strong>
                    Um Horário não <em>é uma</em> Agenda. Um Horário <em>é parte integrante</em> de uma Agenda. Herança violaria o LSP.
                  </div>
                  <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                    <strong className="text-teal-400 block mb-1">2. Ciclo de Vida Acoplado</strong>
                    Se a Agenda for excluída, todos os seus Horários deixam de existir conjuntamente (ON DELETE CASCADE).
                  </div>
                </div>
              </div>

              <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-lg space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400">
                    <Code2 className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-white text-sm">Pilar 3: Polimorfismo</h3>
                    <p className="text-xs text-amber-400">Comportamento Dinâmico</p>
                  </div>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Objetos diferentes respondem à mesma interface polimórfica com resultados especializados:
                </p>
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-[11px] space-y-2">
                  <div>
                    <span className="text-slate-400">janela_confirmacao_horas():</span>
                    <div className="flex justify-between font-mono text-slate-200 mt-0.5">
                      <span>Consulta: 24h</span>
                      <span>Exame: 48h</span>
                      <span>Vacina: 0h</span>
                    </div>
                  </div>
                  <div className="pt-2 border-t border-slate-800">
                    <span className="text-slate-400">duracao_minutos():</span>
                    <div className="flex justify-between font-mono text-slate-200 mt-0.5">
                      <span>Consulta: 20m</span>
                      <span>Exame: 30m</span>
                      <span>Vacina: 5m</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'banco' && (
          <div className="space-y-6">
            <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-lg space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                    <Database className="w-4 h-4 text-teal-400" />
                    Modelo Físico Relacional (SQLite 3 com Foreign Keys Ativas)
                  </h3>
                  <p className="text-xs text-slate-400">
                    Esquema DDL relacional com herança em tabelas separadas (PF) e restrições de unicidade.
                  </p>
                </div>
                <span className="px-2.5 py-1 text-xs font-medium rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  Integridade ACID Ativa
                </span>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'equipe' && (
          <div className="space-y-6">
            <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-lg space-y-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-teal-400" />
                Entrega Oficial do 2º Bimestre — UniCesumar
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-1">
                  <h4 className="font-semibold text-white text-xs">Gustavo Antunes da Silva</h4>
                  <p className="text-[11px] text-teal-400 font-mono">RA: 25000468-2</p>
                </div>
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-1">
                  <h4 className="font-semibold text-white text-xs">Jonatas Marques da Silva</h4>
                  <p className="text-[11px] text-teal-400 font-mono">RA: 25006769-2</p>
                </div>
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-1">
                  <h4 className="font-semibold text-white text-xs">Rafael Garcia Ribeiro</h4>
                  <p className="text-[11px] text-teal-400 font-mono">RA: 25000457-2</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="border-t border-slate-800/80 bg-slate-950 px-6 py-4 text-center text-xs text-slate-500">
        VagaCerta • 2026 • Engenharia de Software • Centro Universitário de Maringá (UniCesumar)
      </footer>
    </div>
  );
}
