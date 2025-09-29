import csv
import os
import sqlite3
from datetime import datetime

DB = "historico_maquinas.db"
CSV_PATH = "Inventario-clinica.csv"


def _connect():
    """Abre conexão SQLite com foreign_keys habilitado."""
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def _ensure_hist_schema(conn: sqlite3.Connection):
    """Garante que as colunas ip e mac existam na tabela historico_maquinas (migração leve)."""
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(historico_maquinas);")
    cols = {row[1] for row in cur.fetchall()}  # row[1] = name
    if "ip" not in cols:
        cur.execute("ALTER TABLE historico_maquinas ADD COLUMN ip TEXT;")
    if "mac" not in cols:
        cur.execute("ALTER TABLE historico_maquinas ADD COLUMN mac TEXT;")


def cria_db():
    """Cria apenas duas tabelas: maquinas e historico_maquinas."""
    conn = _connect()
    c = conn.cursor()
    # Tabela de maquinas
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS maquinas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            linha INTEGER,
            nome TEXT,
            usuario TEXT,
            setor TEXT,
            andar TEXT,
            ip TEXT,
            mac TEXT UNIQUE NOT NULL,
            ponto TEXT,
            comentario TEXT
        );
        """
    )
    # Historico atrelado a uma maquina especifica (via maquina_id)
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS historico_maquinas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            maquina_id INTEGER NOT NULL,
            evento TEXT,
            responsavel TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip TEXT,
            mac TEXT,
            FOREIGN KEY(maquina_id) REFERENCES maquinas(id) ON DELETE CASCADE
        );
        """
    )
    # Índices úteis
    c.execute("CREATE INDEX IF NOT EXISTS idx_maquinas_ip ON maquinas(ip);")
    c.execute("CREATE INDEX IF NOT EXISTS idx_hist_maquina_id ON historico_maquinas(maquina_id);")
    # Garante colunas novas mesmo se a tabela já existia
    _ensure_hist_schema(conn)
    conn.commit()
    conn.close()


def _normaliza_mac(mac: str) -> str:
    if not mac:
        return ""
    mac = mac.strip().upper()
    mac = mac.replace("-", ":").replace(" ", "")
    return mac


def importar_csv(caminho_csv: str = CSV_PATH) -> int:
    """
        Importa dados do CSV para a tabela maquinas.
        - Colunas usadas do CSV e gravadas na tabela maquinas:
            Linha -> linha (INTEGER)
            Nome -> nome
            Usuário/Usuario -> usuario
            Setor -> setor
            Andar -> andar
            IP -> ip
            Endereço MAC/Endereco MAC -> mac (UNIQUE, NOT NULL)
            Ponto -> ponto
            Comentario -> comentario
        - Ignora linhas sem MAC.
        - Faz UPSERT por mac (atualiza todas as colunas quando mac já existe).
    Retorna quantidade de linhas inseridas/atualizadas.
    """
    if not os.path.exists(caminho_csv):
        raise FileNotFoundError(f"CSV não encontrado: {caminho_csv}")

    conn = _connect()
    c = conn.cursor()

    count = 0
    # Envolve tudo em transação para performance
    try:
        with open(caminho_csv, mode="r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Extrai e normaliza campos
                linha_str = (row.get("Linha") or "").strip()
                try:
                    linha = int(linha_str) if linha_str else None
                except ValueError:
                    linha = None

                nome = (row.get("Nome") or "").strip()
                usuario = (row.get("Usuário") or row.get("Usuario") or "").strip()
                setor = (row.get("Setor") or "").strip()
                andar = (row.get("Andar") or "").strip()
                ip = (row.get("IP") or "").strip()
                mac = _normaliza_mac(row.get("Endereço MAC") or row.get("Endereco MAC") or "")
                ponto = (row.get("Ponto") or "").strip()
                comentario = (row.get("Comentario") or "").strip()

                if not mac:
                    continue  # sem MAC, não cadastra

                # UPSERT por mac com todas as colunas mapeadas
                c.execute(
                    """
                    INSERT INTO maquinas (linha, nome, usuario, setor, andar, ip, mac, ponto, comentario)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(mac) DO UPDATE SET
                        linha=excluded.linha,
                        nome=excluded.nome,
                        usuario=excluded.usuario,
                        setor=excluded.setor,
                        andar=excluded.andar,
                        ip=excluded.ip,
                        ponto=excluded.ponto,
                        comentario=excluded.comentario
                    ;
                    """,
                    (linha, nome, usuario, setor, andar, ip, mac, ponto, comentario),
                )
                count += 1
        conn.commit()
    finally:
        conn.close()

    return count


def _get_maquina_id_by_mac(mac: str):
    conn = _connect()
    try:
        c = conn.cursor()
        c.execute("SELECT id FROM maquinas WHERE mac=?", (_normaliza_mac(mac),))
        row = c.fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def adicionar_evento_por_mac(mac, evento, responsavel):
    """Adiciona evento (texto) no historico_maquinas para a maquina com este MAC, salvando também IP e MAC."""
    maquina_id = _get_maquina_id_by_mac(mac)
    if not maquina_id:
        raise ValueError(f"Máquina com MAC {mac} não encontrada para adicionar evento.")
    conn = _connect()
    try:
        c = conn.cursor()
        # Buscar IP e MAC atuais da máquina
        c.execute("SELECT ip, mac FROM maquinas WHERE id=?", (maquina_id,))
        row = c.fetchone()
        ip_atual = row[0] if row else None
        mac_atual = _normaliza_mac(row[1]) if row and row[1] else _normaliza_mac(mac)

        c.execute(
            "INSERT INTO historico_maquinas (maquina_id, evento, responsavel, ip, mac) VALUES (?,?,?,?,?)",
            (maquina_id, evento, responsavel, ip_atual, mac_atual),
        )
        conn.commit()
    finally:
        conn.close()


def listar_eventos_por_mac(mac):
    conn = _connect()
    try:
        c = conn.cursor()
        c.execute(
            """
            SELECT hm.evento, hm.responsavel, hm.created_at, hm.ip, hm.mac
            FROM historico_maquinas hm
            JOIN maquinas m ON m.id = hm.maquina_id
            WHERE m.mac = ?
            ORDER BY hm.created_at DESC
            """,
            (_normaliza_mac(mac),),
        )
        rows = c.fetchall()
        for row in rows:
            print(row)
    finally:
        conn.close()


if __name__ == "__main__":
    # 1) Cria o banco com as 2 tabelas solicitadas
    cria_db()

    # 2) Importa o CSV para a tabela maquinas
    try:
        total = importar_csv(CSV_PATH)
        print(f"Importação concluída. Linhas processadas: {total}")
    except Exception as e:
        print(f"Falha ao importar CSV: {e}")

    # 3) Exemplo opcional: adicionar e listar eventos para um MAC específico já existente no CSV
    # mac_exemplo = "C8:08:E9:5D:DF:F8"
    # adicionar_evento_por_mac(mac_exemplo, "Troca de HD", "SSD 480GB no lugar do HD antigo", "Igor")
    # adicionar_evento_por_mac(mac_exemplo, "Instalação", "Office 2021 + Antivirus Kaspersky", "Igor")
    # listar_eventos_por_mac(mac_exemplo)