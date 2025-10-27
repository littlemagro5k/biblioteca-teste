import importlib.util
import os
import sqlite3


def _ensure_flask_installed() -> None:
    """Garante que o Flask esteja disponível antes de iniciar a aplicação."""

    if importlib.util.find_spec('flask') is None:
        mensagem = (
            'Flask não está instalado. Execute `pip install -r backend/requeriments.txt` '
            'ou `pip install -r requirements.txt` antes de iniciar o servidor.'
        )
        raise SystemExit(mensagem)


_ensure_flask_installed()

from flask import Flask, jsonify, request, session

app = Flask(__name__, static_folder='static', static_url_path='')
app.secret_key = 'chave_super_secreta'  # troque por algo seguro

DB = 'biblioteca.db'


def conectar():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_livro(row):
    return {
        'id': row['id'],
        'titulo': row['titulo'],
        'autor': row['autor'] or '',
        'genero': row['genero'] or '',
        'quantidade': row['quantidade'] if row['quantidade'] is not None else 0,
        'capa': row['capa'] or '',
        'ano': row['ano'],
    }


def row_to_aluno(row):
    return {
        'id': row['id'],
        'nomeCompleto': row['nome_completo'],
        'serie': row['serie'],
        'sala': row['sala'],
    }


@app.route('/')
def index():
    if app.static_folder:
        index_path = os.path.join(app.static_folder, 'index.html')
        if os.path.exists(index_path):
            return app.send_static_file('index.html')

    mensagem = (
        'Frontend não encontrado. Execute `npm run dev` para desenvolvimento '
        'ou `npm run build` para gerar os arquivos estáticos.'
    )
    return mensagem, 503, {'Content-Type': 'text/plain; charset=utf-8'}


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    usuario = (data.get('usuario') or '').strip()
    senha = data.get('senha') or ''

    if not usuario or not senha:
        return jsonify({'erro': 'Usuário e senha são obrigatórios'}), 400

    if usuario == 'admin' and senha == '1234':
        session['usuario'] = usuario
        return jsonify({'mensagem': 'Login realizado com sucesso!', 'usuario': usuario})

    conn = conectar()
    cur = conn.cursor()
    cur.execute(
        "SELECT username FROM usuarios WHERE username = ? AND senha = ?",
        (usuario, senha),
    )
    row = cur.fetchone()
    conn.close()

    if row:
        session['usuario'] = row['username']
        return jsonify({'mensagem': 'Login realizado com sucesso!', 'usuario': row['username']})

    return jsonify({'erro': 'Usuário ou senha incorretos'}), 401


@app.route('/api/alunos', methods=['POST'])
def cadastrar_aluno():
    data = request.get_json() or {}
    nome = (data.get('nomeCompleto') or '').strip()
    serie = (data.get('serie') or '').strip()
    sala = (data.get('sala') or '').strip()
    senha = data.get('senha') or ''

    if not nome or not serie or not sala or not senha:
        return jsonify({'erro': 'Nome, série, sala e senha são obrigatórios.'}), 400
    if len(senha) < 4:
        return jsonify({'erro': 'A senha deve ter pelo menos 4 caracteres.'}), 400

    conn = conectar()
    cur = conn.cursor()
    cur.execute(
        '''
        SELECT id
        FROM alunos
        WHERE lower(nome_completo) = lower(?)
          AND serie = ?
          AND sala = ?
        ''',
        (nome, serie, sala),
    )
    if cur.fetchone():
        conn.close()
        return jsonify({'erro': 'Aluno já cadastrado para esta turma.'}), 409

    cur.execute(
        '''
        INSERT INTO alunos (nome_completo, serie, sala, senha)
        VALUES (?, ?, ?, ?)
        ''',
        (nome, serie, sala, senha),
    )
    aluno_id = cur.lastrowid
    conn.commit()

    cur.execute(
        'SELECT id, nome_completo, serie, sala FROM alunos WHERE id = ?',
        (aluno_id,),
    )
    aluno = cur.fetchone()
    conn.close()

    return (
        jsonify(
            {
                'mensagem': 'Aluno cadastrado com sucesso!',
                'aluno': row_to_aluno(aluno),
            }
        ),
        201,
    )


@app.route('/api/alunos/login', methods=['POST'])
def login_aluno():
    data = request.get_json() or {}
    nome = (data.get('nomeCompleto') or '').strip()
    senha = data.get('senha') or ''

    if not nome or not senha:
        return jsonify({'erro': 'Nome completo e senha são obrigatórios.'}), 400

    conn = conectar()
    cur = conn.cursor()
    cur.execute(
        '''
        SELECT id, nome_completo, serie, sala
        FROM alunos
        WHERE lower(nome_completo) = lower(?)
          AND senha = ?
        ''',
        (nome, senha),
    )
    aluno = cur.fetchone()
    conn.close()

    if not aluno:
        return jsonify({'erro': 'Aluno não encontrado ou senha incorreta.'}), 401

    return jsonify(row_to_aluno(aluno))


@app.route('/logout', methods=['POST'])
def logout():
    session.pop('usuario', None)
    return jsonify({'mensagem': 'Logout realizado'})


@app.route('/api/livros', methods=['GET'])
def listar_livros():
    busca = request.args.get('busca', '').strip()
    conn = conectar()
    cur = conn.cursor()

    if busca:
        like_term = f'%{busca}%'
        cur.execute(
            """
            SELECT id, titulo, autor, genero, quantidade, capa, ano
            FROM livros
            WHERE titulo LIKE ? OR autor LIKE ?
            ORDER BY titulo COLLATE NOCASE
            """,
            (like_term, like_term),
        )
    else:
        cur.execute(
            """
            SELECT id, titulo, autor, genero, quantidade, capa, ano
            FROM livros
            ORDER BY titulo COLLATE NOCASE
            """
        )

    livros = [row_to_livro(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(livros)


@app.route('/api/livros', methods=['POST'])
def adicionar_livro():
    if 'usuario' not in session:
        return jsonify({'erro': 'Não autorizado'}), 403

    data = request.get_json() or {}
    titulo = (data.get('titulo') or '').strip()
    if not titulo:
        return jsonify({'erro': 'Título é obrigatório'}), 400

    autor = (data.get('autor') or '').strip()
    genero = (data.get('genero') or '').strip()
    capa = (data.get('capa') or '').strip()
    ano = data.get('ano')
    ano_int = None
    if ano not in (None, ''):
        try:
            ano_int = int(ano)
        except (TypeError, ValueError):
            return jsonify({'erro': 'Ano inválido'}), 400

    quantidade = data.get('quantidade', 0)
    try:
        quantidade_int = int(quantidade)
    except (TypeError, ValueError):
        return jsonify({'erro': 'Quantidade inválida'}), 400

    conn = conectar()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO livros (titulo, autor, genero, quantidade, capa, ano)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (titulo, autor, genero, quantidade_int, capa, ano_int),
    )
    novo_id = cur.lastrowid
    conn.commit()

    cur.execute(
        "SELECT id, titulo, autor, genero, quantidade, capa, ano FROM livros WHERE id = ?",
        (novo_id,),
    )
    livro = cur.fetchone()
    conn.close()

    return (
        jsonify({'mensagem': 'Livro adicionado com sucesso!', 'livro': row_to_livro(livro)}),
        201,
    )


@app.route('/api/livros/<int:livro_id>', methods=['PUT'])
def atualizar_livro(livro_id):
    if 'usuario' not in session:
        return jsonify({'erro': 'Não autorizado'}), 403

    data = request.get_json() or {}
    campos_validos = {
        'titulo': lambda v: (v or '').strip(),
        'autor': lambda v: (v or '').strip(),
        'genero': lambda v: (v or '').strip(),
        'capa': lambda v: (v or '').strip(),
        'ano': lambda v: v,
        'quantidade': lambda v: v,
    }

    updates = []
    valores = []

    for campo, normalizer in campos_validos.items():
        if campo not in data:
            continue
        valor = normalizer(data.get(campo))
        if campo == 'ano':
            if valor in (None, ''):
                valor = None
            else:
                try:
                    valor = int(valor)
                except (TypeError, ValueError):
                    return jsonify({'erro': 'Ano inválido'}), 400
        if campo == 'quantidade':
            try:
                valor = int(valor)
            except (TypeError, ValueError):
                return jsonify({'erro': 'Quantidade inválida'}), 400
        updates.append(f"{campo} = ?")
        valores.append(valor)

    if not updates:
        return jsonify({'erro': 'Nenhum dado para atualizar'}), 400

    conn = conectar()
    cur = conn.cursor()
    cur.execute(
        f"UPDATE livros SET {', '.join(updates)} WHERE id = ?",
        (*valores, livro_id),
    )

    if cur.rowcount == 0:
        conn.close()
        return jsonify({'erro': 'Livro não encontrado'}), 404

    conn.commit()
    cur.execute(
        "SELECT id, titulo, autor, genero, quantidade, capa, ano FROM livros WHERE id = ?",
        (livro_id,),
    )
    livro = cur.fetchone()
    conn.close()

    return jsonify({'mensagem': 'Livro atualizado com sucesso!', 'livro': row_to_livro(livro)})


@app.route('/api/livros/<int:livro_id>', methods=['DELETE'])
def excluir_livro(livro_id):
    if 'usuario' not in session:
        return jsonify({'erro': 'Não autorizado'}), 403

    data = request.get_json() or {}
    campos_validos = {
        'titulo': lambda v: (v or '').strip(),
        'autor': lambda v: (v or '').strip(),
        'genero': lambda v: (v or '').strip(),
        'capa': lambda v: (v or '').strip(),
        'ano': lambda v: v,
        'quantidade': lambda v: v,
    }

    updates = []
    valores = []

    for campo, normalizer in campos_validos.items():
        if campo not in data:
            continue
        valor = normalizer(data.get(campo))
        if campo == 'ano':
            if valor in (None, ''):
                valor = None
            else:
                try:
                    valor = int(valor)
                except (TypeError, ValueError):
                    return jsonify({'erro': 'Ano inválido'}), 400
        if campo == 'quantidade':
            try:
                valor = int(valor)
            except (TypeError, ValueError):
                return jsonify({'erro': 'Quantidade inválida'}), 400
        updates.append(f"{campo} = ?")
        valores.append(valor)

    if not updates:
        return jsonify({'erro': 'Nenhum dado para atualizar'}), 400

    conn = conectar()
    cur = conn.cursor()
    cur.execute("DELETE FROM livros WHERE id = ?", (livro_id,))
    if cur.rowcount == 0:
        conn.close()
        return jsonify({'erro': 'Livro não encontrado'}), 404

    conn.commit()
    conn.close()
    return jsonify({'mensagem': 'Livro removido com sucesso!'})


if __name__ == '__main__':
    if not os.path.exists(DB):
        print('Banco não encontrado. Criando automaticamente...')
        from init_db import criar_banco

        criar_banco()
    app.run(debug=True)
