### Sistema Web de Gestão de Pedidos para Restaurante

**Período:** Maio – Junho 2025  
**Função:** Desenvolvimento Full-Stack / Banco de Dados  

---

#### Descrição

Aplicação web para gerenciamento de pedidos de restaurante, com frontend em Flask/Jinja2 e toda a lógica de negócio e integridade implementadas diretamente no PostgreSQL por meio de stored procedures, funções e triggers.

---

#### Tecnologias Utilizadas

- **Backend:** Python (Flask)  
- **Banco de Dados:** PostgreSQL (psycopg2)  
- **Templates:** Jinja2  
- **Doc:** Markdown via Docsify
- **Orquestração:** Docker / docker-compose

---

#### Principais Atividades

- **Modelagem de dados:**  

  • 7 tabelas: `usuarios`, `itens_cardapio`, `pedidos`, `itens_pedido`, `estoque`, `status_pedido`, `logs`.

- **Stored procedures:**  

  • `registrar_pedido(cliente_id, itens[])` – cria pedido com múltiplos itens e valida estoque.  
  • `calcular_total_pedido(pedido_id)` – soma valores dos itens.  
  • `listar_pedidos(status)` – retorna pedidos por status.  
  • `trocar_status_pedido(pedido_id, novo_status)` – altera status, validando transições.  
- **Triggers e funções de apoio:**  

  1. `trg_validar_estoque` – impede inserção de item sem estoque suficiente.  
  2. `trg_descontar_estoque` – debita automaticamente o estoque após inclusão de item no pedido.  
  3. `trg_validar_status` – aplica regras de transição de status (e.g. “entregue” não retorna a “em preparo”).  
  4. `trg_log_alteracao` – registra auditoria de qualquer atualização na tabela `pedidos`.  
  5. `trg_log_cancelamento` – gera log específico em casos de cancelamento de pedido.  
- **Desenvolvimento de interface:**  

  • Rotas Flask para visualização de cardápio, criação de pedido e painel administrativo.  
  • Templates Jinja2 para renderização dinâmica de listas e detalhes de pedidos.  
- **Documentação técnica:**  

---

#### Resultados e Benefícios

- **Consistência e integridade** garantidas no nível de banco de dados, reduzindo possibilidade de falhas no backend.  
- **Trilha de auditoria completa** sem depender de implementação adicional no código da aplicação.  
- **Interface unificada** e de fácil manutenção, com atualizações de docs imediatas via Markdown.


## Estrutura e Principais Blocos de Código

---

## app.py

- **Função `create_app()`**  
  - Instancia o objeto Flask.  
  - Carrega configurações de `Config` (em `config.py`).  
  - Registra os blueprints de autenticação (`auth_bp`) e de pedidos (`pedidos_bp`).  
  - Define `close_conn` (em `db.py`) como handler de *teardown* para fechar conexões ao final de cada request.  
- **Bloco `if __name__ == '__main__'`**  
  - Cria o app e executa em modo debug.

---

## config.py

- **Classe `Config`**  
  - `SECRET_KEY`: chave para sessões e formulários.  
  - `DATABASE_URI`: string de conexão com PostgreSQL (`postgresql://postgres:1234@localhost:5432/restaurante`).

---

## db.py

- **Função `get_conn()`**  
  - Armazena conexão no objeto global `g` do Flask.  
  - Usa `psycopg2.connect()` com `DATABASE_URI`.  
  - Retorna `g.db_conn`.  
- **Função `close_conn(e=None)`**  
  - Fecha a conexão armazenada em `g.db_conn`, se existir.

---

## DAO (`dao/`)

### cardapio_dao.py

- **`listar_itens_cardapio()`**  
  - Executa `SELECT * FROM itens_cardapio`.  
  - Retorna lista de dicionários com os campos de cada item.  
- **`persiste_item_cardapio(criaItemDto)`**  
  - Insere um novo registro em `itens_cardapio` (nome, preço, descrição, estoque).

### pedido_dao.py

- **`registrar_pedido(cliente_id, itens)`**  
  - Chama a função SQL `registrar_pedido(cliente_id, json)` no banco.  
  - Retorna o `pedido_id` criado.  
- **`listar_pedidos(status)`**  
  - Busca pedidos com status dado, juntando com `usuarios` para obter `cliente_nome`.  
  - Retorna lista de dicionários (id, status, cliente_nome, data_hora).  
- **`detalhes_pedido(pedido_id)`**  
  - Busca dados do pedido e cliente.  
  - Busca itens do pedido (`nome` e `quantidade`).  
  - Retorna um dicionário com `id`, `status`, `cliente_nome` e lista de `itens`.  
- **`trocar_status(pedido_id, novo_status)`**  
  - Atualiza o campo `status` em `pedidos`.  

### usuario_dao.py

- **`autenticar_usuario(username, senha)`**  
  - Busca usuário por `username`.  
  - Verifica hash da senha (`werkzeug.security`).  
  - Retorna dicionário com `id`, `username` e `is_admin` (se válido).  
- **(Possível função adicional) `buscar_usuario_por_username` / `criar_usuario`**  
  - Buscam/criam usuário; usadas em `auth/routes.py`.

---

## Blueprint de Autenticação (`auth/`)

### decorators.py

- **`login_required(f)`**  
  - Decorator que verifica `session['user_id']`.  
  - Redireciona para login com mensagem se não autenticado.

### routes.py

- **`@bp.route('/register')`**  
  - **GET**: renderiza formulário de cadastro.  
  - **POST**: valida dados, cria usuário, inicia sessão e redireciona para `/cardapio`.  
- **`@bp.route('/login')`**  
  - **GET**: renderiza formulário de login.  
  - **POST**: autentica, seta sessão e redireciona.  
- **`@bp.route('/logout')`**  
  - Limpa sessão e redireciona para login.

---

## Blueprint de Pedidos (`pedidos/`)

### routes.py

- **`@bp.route('/')`**  
  - Página inicial (pode redirecionar ou mostrar landing).  
- **`@bp.route('/cardapio', methods=['GET','POST'])`**  
  - **GET**: lista itens via `listar_itens_cardapio()`.  
  - **POST**: somente admin insere novo item (`persiste_item_cardapio`); faz redirect.  
- **`@bp.route('/novo', methods=['GET','POST'])`**  
  - **GET**: renderiza formulário de pedido.  
  - **POST**: coleta `cliente_id` da sessão e itens do form; chama `registrar_pedido`; redireciona para painel ou detalhes.  
- **`@bp.route('/painel')`**  
  - Lista pedidos filtrados por status (e.g., “em preparo”, “pronto”) usando `listar_pedidos`.  
- **`@bp.route('/detalhes/<int:pedido_id>', methods=['GET','POST'])`**  
  - **GET**: mostra detalhes via `detalhes_pedido()` e opções de transição de status.  
  - **POST**: aplica `trocar_status()` e retorna ao mesmo detalhe com mensagem de sucesso/erro.

---
