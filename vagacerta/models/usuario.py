"""
Módulo de Usuários e Perfis de Acesso.
Demonstração do Pilar POO: HERANÇA e POLIMORFISMO.

Hierarquia:
  Usuario (Classe Base Abstrata)
    ├── Paciente (Especialização com regras de SUS, histórico de faltas e restrição RN03)
    ├── ProfissionalSaude (Especialização com registro de classe médica/enfermagem e turnos)
    └── GestorUnidade (Especialização com matrícula e escopo de fiscalização e relatórios)
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Tuple
from vagacerta.models.enums import PerfilAcesso
from vagacerta.config import LIMITE_FALTAS_BLOQUEIO


class Usuario(ABC):
    """
    Classe base abstrata para todos os atores do sistema VagaCerta.
    Encapsula atributos comuns de identificação, credenciais e contato.
    """

    def __init__(
        self,
        id: int | None,
        nome: str,
        cpf: str,
        email: str,
        senha_hash: str,
        telefone: str,
        ativo: bool = True,
    ):
        self.id = id
        self.nome = nome.strip()
        self.cpf = "".join(filter(str.isdigit, cpf))
        self.email = email.strip().lower()
        self.senha_hash = senha_hash
        self.telefone = telefone.strip()
        self.ativo = ativo

    @abstractmethod
    def perfil(self) -> PerfilAcesso:
        """Retorna o perfil formal de acesso deste usuário (Polimorfismo)."""
        pass

    @abstractmethod
    def pode_agendar_online(self) -> Tuple[bool, str]:
        """
        Avalia se o usuário possui permissão para realizar agendamentos online.
        Comportamento polimórfico especializado em cada subclasse.
        """
        pass

    def validar(self) -> None:
        """Validações fundamentais de integridade do usuário."""
        if not self.nome:
            raise ValueError("Nome do usuário não pode ser vazio.")
        if len(self.cpf) != 11:
            raise ValueError(f"CPF inválido ({self.cpf}): deve conter exatamente 11 dígitos.")
        if "@" not in self.email:
            raise ValueError(f"E-mail inválido ({self.email}).")

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id} nome='{self.nome}' perfil={self.perfil().value}>"


class Paciente(Usuario):
    """
    Especialização para cidadãos e pacientes do SUS.
    Implementa a Regra de Negócio RN03 (Restrição por reincidência de faltas).
    """

    def __init__(
        self,
        id: int | None,
        nome: str,
        cpf: str,
        email: str,
        senha_hash: str,
        telefone: str,
        cartao_sus: str,
        data_nascimento: date | str,
        faltas_nao_justificadas: int = 0,
        ativo: bool = True,
    ):
        super().__init__(id, nome, cpf, email, senha_hash, telefone, ativo)
        self.cartao_sus = "".join(filter(str.isdigit, str(cartao_sus)))
        self.data_nascimento = (
            date.fromisoformat(data_nascimento)
            if isinstance(data_nascimento, str)
            else data_nascimento
        )
        self.faltas_nao_justificadas = max(0, int(faltas_nao_justificadas))

    def perfil(self) -> PerfilAcesso:
        return PerfilAcesso.PACIENTE

    def esta_bloqueado(self) -> bool:
        """Verifica se o paciente atingiu o teto de reincidência de faltas (RN03)."""
        return self.faltas_nao_justificadas >= LIMITE_FALTAS_BLOQUEIO

    def pode_agendar_online(self) -> Tuple[bool, str]:
        """
        RN03 - Três faltas não justificadas no período bloqueiam o agendamento
        remoto pelo próprio paciente, exigindo acolhimento presencial na UBS.
        """
        if not self.ativo:
            return False, "Cadastro de paciente inativo no sistema."
        if self.esta_bloqueado():
            return (
                False,
                f"Agendamento remoto bloqueado (RN03): Paciente possui {self.faltas_nao_justificadas} "
                f"faltas não justificadas. Dirija-se ao setor de acolhimento presencial da UBS.",
            )
        return True, "Paciente apto para agendamento online."

    def registrar_falta(self) -> None:
        """Incrementa contador de faltas não justificadas."""
        self.faltas_nao_justificadas += 1

    def abonar_falta(self) -> None:
        """Decrementa contador após justificativa acolhida pelo gestor."""
        if self.faltas_nao_justificadas > 0:
            self.faltas_nao_justificadas -= 1

    def validar(self) -> None:
        super().validar()
        if len(self.cartao_sus) != 15:
            raise ValueError(
                f"Cartão Nacional de Saúde (SUS) inválido: deve ter 15 dígitos (recebido: {self.cartao_sus})."
            )


class ProfissionalSaude(Usuario):
    """
    Especialização para médicos, enfermeiros e corpo clínico da unidade.
    Possui registro de conselho de classe (CRM, COREN) e especialidade.
    """

    def __init__(
        self,
        id: int | None,
        nome: str,
        cpf: str,
        email: str,
        senha_hash: str,
        telefone: str,
        registro_conselho: str,
        especialidade: str,
        carga_horaria_diaria: int = 8,
        ativo: bool = True,
    ):
        super().__init__(id, nome, cpf, email, senha_hash, telefone, ativo)
        self.registro_conselho = registro_conselho.strip()
        self.especialidade = especialidade.strip()
        self.carga_horaria_diaria = carga_horaria_diaria

    def perfil(self) -> PerfilAcesso:
        return PerfilAcesso.PROFISSIONAL

    def pode_agendar_online(self) -> Tuple[bool, str]:
        if not self.ativo:
            return False, "Profissional inativo."
        return True, "Profissional de saúde pode agendar e remanejar atendimentos."

    def validar(self) -> None:
        super().validar()
        if not self.registro_conselho:
            raise ValueError("Registro de conselho (CRM/COREN) é obrigatório.")
        if not self.especialidade:
            raise ValueError("Especialidade do profissional é obrigatória.")


class GestorUnidade(Usuario):
    """
    Especialização para a coordenação e diretoria da UBS.
    Responsável pelo monitoramento de BI, fiscais de absenteísmo e acolhimento.
    """

    def __init__(
        self,
        id: int | None,
        nome: str,
        cpf: str,
        email: str,
        senha_hash: str,
        telefone: str,
        matricula: str,
        cargo: str,
        ativo: bool = True,
    ):
        super().__init__(id, nome, cpf, email, senha_hash, telefone, ativo)
        self.matricula = matricula.strip()
        self.cargo = cargo.strip()

    def perfil(self) -> PerfilAcesso:
        return PerfilAcesso.GESTOR

    def pode_agendar_online(self) -> Tuple[bool, str]:
        if not self.ativo:
            return False, "Gestor inativo."
        return True, "Gestor possui privilégio administrativo irrestrito."

    def validar(self) -> None:
        super().validar()
        if not self.matricula:
            raise ValueError("Matrícula funcional do gestor é obrigatória.")
        if not self.cargo:
            raise ValueError("Cargo do gestor é obrigatório.")
