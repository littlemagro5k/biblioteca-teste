const JSON_CONTENT = 'application/json';

async function request(path, { method = 'GET', body, headers = {} } = {}) {
  const options = {
    method,
    credentials: 'include',
    headers: { ...headers },
  };

  if (body !== undefined) {
    options.body = typeof body === 'string' ? body : JSON.stringify(body);
    options.headers['Content-Type'] = JSON_CONTENT;
  }

  const response = await fetch(path, options);
  const contentType = response.headers.get('content-type') || '';
  const isJson = contentType.includes(JSON_CONTENT);
  const payload = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    const message =
      (payload && (payload.erro || payload.mensagem)) ||
      (typeof payload === 'string' && payload) ||
      'Erro desconhecido';
    throw new Error(message);
  }

  return payload;
}

export async function loginBibliotecario(usuario, senha) {
  return request('/login', {
    method: 'POST',
    body: { usuario, senha },
  });
}

export async function logoutBibliotecario() {
  return request('/logout', { method: 'POST' });
}

export async function fetchBooks(busca = '') {
  const query = busca ? `?busca=${encodeURIComponent(busca)}` : '';
  return request(`/api/livros${query}`);
}

export async function createBook(dados) {
  return request('/api/livros', {
    method: 'POST',
    body: dados,
  });
}

export async function updateBook(id, dados) {
  return request(`/api/livros/${id}`, {
    method: 'PUT',
    body: dados,
  });
}

export async function deleteBook(id) {
  return request(`/api/livros/${id}`, {
    method: 'DELETE',
  });
}

export async function registerStudent({ nomeCompleto, serie, sala, senha }) {
  return request('/api/alunos', {
    method: 'POST',
    body: { nomeCompleto, serie, sala, senha },
  });
}

export async function loginStudent(nomeCompleto, senha) {
  return request('/api/alunos/login', {
    method: 'POST',
    body: { nomeCompleto, senha },
  });
}
