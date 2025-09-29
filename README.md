# Inventário e Histórico de Máquinas

Este projeto é um app de desktop (Tkinter + SQLite) para gerenciar inventário de máquinas e o histórico de eventos.

## Manter tudo em um arquivo ou estruturar?

Funciona em um arquivo único, mas conforme o código cresce, separar por módulos traz benefícios:

- Manutenção mais simples: responsabilidades claras (banco, UI, repositórios, diálogos).
- Testes mais fáceis: testar DB e lógica sem abrir a UI.
- Reuso: funções de consulta podem ser reaproveitadas (ex.: na aba de pesquisa).
- Legibilidade: arquivos menores e focados.

Se o projeto for ficar pequeno e estável, deixar em um arquivo não é um problema. Se você pretende evoluir (mais campos, filtros, exportação, permissões), modularizar ajuda bastante.

## Estrutura sugerida (incremental e segura)

Sem mudar o comportamento atual, uma separação mínima pode ser:

```
Banco Historico Maquinario/
├─ historico_maquinas.db
├─ Inventario-clinica.csv
├─ main.py                # ponto de entrada (abre o Tk e instancia a App)
├─ inventario_gui.py      # pode ficar por enquanto, mas vamos enxugar
├─ app/
│  ├─ __init__.py
│  ├─ db.py               # get_conn(), run_query(), inicialização do banco
│  ├─ repository.py       # CRUD de máquinas e eventos (chama db.run_query)
│  ├─ models.py           # (opcional) dataclasses Maquina/Evento
│  └─ ui/
│     ├─ app.py           # classe InventarioApp (somente UI e orquestração)
│     └─ dialogs.py       # MaquinaDialog, EventoDialog
└─ README.md
```

Você pode migrar por etapas sem quebrar nada:

1) Extrair o módulo `app/db.py`
- Mover `get_conn()` e `run_query()` para `app/db.py`.
- Em `inventario_gui.py`, trocar `from app.db import run_query, get_conn` e remover as duplicatas.

2) Extrair os diálogos
- Criar `app/ui/dialogs.py` com `MaquinaDialog` e `EventoDialog`.
- Importar em `inventario_gui.py` com `from app.ui.dialogs import MaquinaDialog, EventoDialog`.

3) Criar o repositório
- Criar `app/repository.py` com funções `listar_maquinas`, `criar_maquina`, `atualizar_maquina`, `remover_maquina`, `listar_eventos`, etc.
- A UI passa a chamar o repositório ao invés de montar SQL diretamente.

4) Mover a App para `app/ui/app.py`
- Copiar a classe `InventarioApp` para `app/ui/app.py`.
- Deixar `inventario_gui.py` só com imports/compatibilidade, ou removê-lo e atualizar `main.py`.

5) Limpeza e testes
- Garantir que `main.py` inicializa a aplicação: `from app.ui.app import InventarioApp`.
- Rodar o app e testar as operações básicas (listar, adicionar, editar, remover, ordenar, pesquisar, histórico).

## Como executar

No Windows (PowerShell), a depender do seu ponto de entrada atual:

```powershell
# Se o main.py é o ponto de entrada
python .\main.py

# ou, se você roda direto o inventario_gui.py
python .\inventario_gui.py
```

Tkinter e sqlite3 fazem parte da biblioteca padrão do Python, então não há dependências externas.

## Dicas de refatoração

- Faça mudanças pequenas e teste a cada etapa (abrir o app, listar, adicionar, editar, remover, pesquisar).
- Mantenha o caminho do banco consistente (use caminhos relativos ou `Path(__file__).parent`).
- Evite mudar nomes de funções públicas na UI durante a extração; primeiro mova, depois renomeie.
- Use `try/except` onde já existe para não alterar mensagens/fluxos.

## Próximos passos opcionais

- Exportar CSV/Excel do inventário e do histórico.
- Adicionar logs (ex.: `logging`) para depuração.
- Criar testes de unidade para o repositório.
- Empacotar com PyInstaller para gerar um executável.
