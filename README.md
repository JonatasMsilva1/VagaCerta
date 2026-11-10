# VagaCerta - Sistema de Agendamento e Combate ao Absenteísmo em UBS

Este repositório contém os fontes corrigidos do projeto **VagaCerta**, desenvolvido para a disciplina de Engenharia de Software (UniCesumar).

## Estrutura do Projeto

```
vagacerta/
├── metadata.json
├── README.md
├── src/
│   └── App.tsx
└── java-backend/
    └── src/
        └── main/
            └── java/
                └── br/
                    └── com/
                        └── vagacerta/
                            └── model/
                                └── enums/
                                    ├── PerfilAcesso.java
                                    ├── StatusHorario.java
                                    ├── TipoAgendamento.java
                                    └── StatusAgendamento.java
```

## Ajustes e Correções Efetuadas

1. **`src/App.tsx`**: Fechamento sintático da interface `PacienteData` e da função principal `App()`.
2. **`metadata.json`**: Atualização do stack do backend para **Java 17 (Pure JDBC)** e inclusão de descrição completa.
3. **`java-backend/.../enums/`**: Correção de truncamento de sintaxe nos enums Java (`PerfilAcesso`, `StatusHorario`, `TipoAgendamento`, `StatusAgendamento`).
