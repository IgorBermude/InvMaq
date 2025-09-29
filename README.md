# Inventário e Histórico de Máquinas

Este projeto é um app de desktop (Tkinter + SQLite) para gerenciar inventário de máquinas e o histórico de eventos. Foi desenvolvido para facilitar e automatizar o cadastro de maquinas e eventos em uma rede.

## Como executar

No Windows (PowerShell), a depender do seu ponto de entrada atual:

```powershell
# Se o main.py é o ponto de entrada
python .\main.py

# ou, se você roda direto o inventario_gui.py
python .\inventario_gui.py
```

Tkinter e sqlite3 fazem parte da biblioteca padrão do Python, então não há dependências externas.

O arquivo main.py vai gerar um banco de dados SQLite e inserir nele os dados de uma planilha, nesse caso "Inventario-clinica.csv". Após a criação do banco, ao executar o inventario_gui.py sera possivel visualizar todos os dados das maquinas cadastradas no banco e manipula-los.

# Gerar um executavel
Para gerar um executavel funcional foi utilizado do seguintes comandos no terminal:
New-Item -ItemType Directory -Force C:\dev\out\dist | Out-Null
New-Item -ItemType Directory -Force C:\dev\out\build | Out-Null
python -m PyInstaller --noconsole --onefile --name Inventario ` --add-data "Inventario-clinica.csv;." ` --distpath "C:\dev\out\dist" --workpath "C:\dev\out\build" `inventario_gui.py

Após isso eu movi o arquivo do banco para a mesma pasta do arquivo executavel.
