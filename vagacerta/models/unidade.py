"""
Módulo de Unidade de Saúde (UBS).
Representa a infraestrutura física de atendimento do SUS.
"""


class UnidadeSaude:
    """
    Entidade representando uma Unidade Básica de Saúde ou Centro de Especialidades.
    """

    def __init__(
        self,
        id: int | None,
        nome: str,
        cnes: str,
        endereco: str,
        telefone: str,
    ):
        self.id = id
        self.nome = nome.strip()
        self.cnes = "".join(filter(str.isdigit, str(cnes)))
        self.endereco = endereco.strip()
        self.telefone = telefone.strip()

    def validar(self) -> None:
        if not self.nome:
            raise ValueError("Nome da Unidade de Saúde é obrigatório.")
        if len(self.cnes) != 7:
            raise ValueError(f"Código CNES deve ter exatamente 7 dígitos (recebido: {self.cnes}).")
        if not self.endereco:
            raise ValueError("Endereço da Unidade de Saúde é obrigatório.")

    def __repr__(self) -> str:
        return f"<UnidadeSaude id={self.id} nome='{self.nome}' cnes={self.cnes}>"
