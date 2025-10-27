import sqlite3

DB_PATH = 'biblioteca.db'


def ensure_columns(cursor, table, columns):
    existing = {row[1] for row in cursor.execute(f"PRAGMA table_info({table})")}
    for column, definition in columns:
        if column not in existing:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def criar_banco():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS livros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            autor TEXT,
            genero TEXT,
            quantidade INTEGER DEFAULT 0,
            capa TEXT,
            ano INTEGER
        )
        '''
    )

    ensure_columns(
        cur,
        'livros',
        [
            ('genero', 'TEXT'),
            ('quantidade', 'INTEGER DEFAULT 0'),
            ('capa', 'TEXT'),
            ('ano', 'INTEGER'),
        ],
    )

    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            email TEXT
        )
        '''
    )

    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS alunos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_completo TEXT NOT NULL,
            serie TEXT NOT NULL,
            sala TEXT NOT NULL,
            senha TEXT NOT NULL
        )
        '''
    )

    conn.commit()

    cur.execute('SELECT COUNT(*) FROM livros')
    if cur.fetchone()[0] == 0:
        livros = [
            ("Dom Casmurro", "Machado de Assis", "Romance", 4, "", 1899),
            ("O Alquimista", "Paulo Coelho", "Ficção", 5, "", 1988),
            ("Capitães da Areia", "Jorge Amado", "Romance", 3, "", 1937),
            ("Vidas Secas", "Graciliano Ramos", "Romance", 6, "", 1938),
            (
                "Memórias Póstumas de Brás Cubas",
                "Machado de Assis",
                "Romance",
                2,
                "",
                1881,
            ),
            ("A Hora da Estrela", "Clarice Lispector", "Ficção", 4, "", 1977),
            ("Grande Sertão: Veredas", "Guimarães Rosa", "Romance", 3, "", 1956),
            ("O Cortiço", "Aluísio Azevedo", "Romance", 5, "", 1890),
            ("Iracema", "José de Alencar", "Romance", 2, "", 1865),
            ("A Moreninha", "Joaquim Manuel de Macedo", "Romance", 3, "", 1844),
        ]
        cur.executemany(
            """
            INSERT INTO livros (titulo, autor, genero, quantidade, capa, ano)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            livros,
        )

    cur.execute('SELECT COUNT(*) FROM usuarios')
    if cur.fetchone()[0] == 0:
        usuarios = [
            ('admin', '1234', 'admin@leiasj.com'),
            ('aluno1', 'senha123', 'aluno1@email.com'),
            ('aluno2', 'senha456', 'aluno2@email.com'),
        ]
        cur.executemany(
            'INSERT INTO usuarios (username, senha, email) VALUES (?, ?, ?)',
            usuarios,
        )

    conn.commit()
    conn.close()
    print('Banco e tabelas criados/atualizados com sucesso!')


if __name__ == '__main__':
    criar_banco()
