# Inventário e Histórico de Máquinas

Este projeto é um app de desktop (Tkinter + PostgreSQL) para gerenciar inventário de máquinas e o histórico de eventos. Foi desenvolvido para facilitar e automatizar o cadastro de maquinas e eventos em uma rede.

Tkinter e sqlite3 fazem parte da biblioteca padrão do Python, então não há dependências externas.

# Gerar um executavel
Para gerar um executavel funcional foi utilizado do seguintes comandos no terminal:
python -m PyInstaller --noconsole --onefile --name Inventario `
>>   --distpath "C:\inventario\dist" --workpath "C:\inventario\build" `
>>   inventario_gui.py
