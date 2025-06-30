DROP TABLE IF EXISTS logs;
DROP TABLE IF EXISTS itens_pedido;
DROP TABLE IF EXISTS pedidos;
DROP TABLE IF EXISTS itens_cardapio;
DROP TABLE IF EXISTS usuarios;
DROP TYPE IF EXISTS status_pedido_enum;

CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE itens_cardapio (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    preco NUMERIC(10,2) NOT NULL,
    descricao TEXT,
    quantidade_estoque INTEGER NOT NULL DEFAULT 0
);

CREATE TYPE status_pedido_enum AS ENUM (
    'em preparo',
    'pronto',
    'entregue',
    'cancelado'
);

CREATE TABLE pedidos (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER REFERENCES usuarios(id),
    status status_pedido_enum NOT NULL DEFAULT 'em preparo',
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE itens_pedido (
    id SERIAL PRIMARY KEY,
    pedido_id INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
    item_id INTEGER NOT NULL REFERENCES itens_cardapio(id),
    quantidade INTEGER NOT NULL CHECK (quantidade > 0),
    preco_unitario NUMERIC(10,2) NOT NULL
);

CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    pedido_id INTEGER REFERENCES pedidos(id),
    acao VARCHAR(100) NOT NULL,
    data_hora TIMESTAMP NOT NULL DEFAULT NOW()
);


CREATE OR REPLACE FUNCTION registrar_pedido(cliente_id INTEGER, itens JSON)
RETURNS INTEGER AS $$
DECLARE
    novo_pedido_id INTEGER;
    item JSON;
    item_id INTEGER;
    quantidade INTEGER;
    preco_item NUMERIC(10,2);
BEGIN
    INSERT INTO pedidos (cliente_id) VALUES (cliente_id) RETURNING id INTO novo_pedido_id;

    FOR item IN SELECT * FROM json_array_elements(itens)
    LOOP
        item_id := (item->>'item_id')::INTEGER;
        quantidade := (item->>'quantidade')::INTEGER;


        IF (SELECT quantidade_estoque FROM itens_cardapio WHERE id = item_id) < quantidade THEN
            RAISE EXCEPTION 'Estoque insuficiente para o item %', item_id;
        END IF;

      
        SELECT preco INTO preco_item FROM itens_cardapio WHERE id = item_id;

       
        INSERT INTO itens_pedido (pedido_id, item_id, quantidade, preco_unitario)
        VALUES (novo_pedido_id, item_id, quantidade, preco_item);

        
        UPDATE itens_cardapio SET quantidade_estoque = quantidade_estoque - quantidade
        WHERE id = item_id;
    END LOOP;

    RETURN novo_pedido_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION log_alteracao_pedido()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        INSERT INTO logs (pedido_id, acao, data_hora)
        VALUES (NEW.id, 'Pedido atualizado', NOW());
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_log_alteracao
AFTER UPDATE ON pedidos
FOR EACH ROW
EXECUTE FUNCTION log_alteracao_pedido();


CREATE OR REPLACE FUNCTION validar_estoque()
RETURNS TRIGGER AS $$
DECLARE
    estoque_atual INTEGER;
BEGIN
    SELECT quantidade_estoque INTO estoque_atual FROM itens_cardapio WHERE id = NEW.item_id;
    IF estoque_atual < NEW.quantidade THEN
        RAISE EXCEPTION 'Estoque insuficiente para o item %', NEW.item_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validar_estoque
BEFORE INSERT ON itens_pedido
FOR EACH ROW
EXECUTE FUNCTION validar_estoque();


CREATE OR REPLACE FUNCTION descontar_estoque()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE itens_cardapio
    SET quantidade_estoque = quantidade_estoque - NEW.quantidade
    WHERE id = NEW.item_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_descontar_estoque
AFTER INSERT ON itens_pedido
FOR EACH ROW
EXECUTE FUNCTION descontar_estoque();


CREATE OR REPLACE FUNCTION validar_transicao_status()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status = 'entregue' AND NEW.status <> 'entregue' THEN
        RAISE EXCEPTION 'Não é possível alterar um pedido já entregue.';
    END IF;
    IF OLD.status = 'cancelado' AND NEW.status <> 'cancelado' THEN
        RAISE EXCEPTION 'Não é possível reativar um pedido cancelado.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validar_status
BEFORE UPDATE OF status ON pedidos
FOR EACH ROW
EXECUTE FUNCTION validar_transicao_status();


CREATE OR REPLACE FUNCTION log_cancelamento()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'cancelado' AND OLD.status <> 'cancelado' THEN
        INSERT INTO logs (pedido_id, acao, data_hora)
        VALUES (NEW.id, 'Pedido cancelado', NOW());
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_log_cancelamento
AFTER UPDATE OF status ON pedidos
FOR EACH ROW
EXECUTE FUNCTION log_cancelamento();


INSERT INTO usuarios (username, senha_hash, is_admin)
VALUES (
    'admin',
    '$pbkdf2-sha256$29000$coloque_o_hash_gerado_aqui',
    TRUE
);


INSERT INTO itens_cardapio (nome, preco, descricao, quantidade_estoque)
VALUES ('Pizza Calabresa', 45.00, 'Pizza de calabresa com queijo e cebola', 10);


CREATE OR REPLACE FUNCTION listar_pedidos(status_pedido TEXT)
RETURNS TABLE (
    id INT,
    cliente_id INT,
    status status_pedido_enum,
    data_hora TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT pedidos.id, pedidos.cliente_id, pedidos.status, pedidos.data_hora
    FROM pedidos
    WHERE pedidos.status = status_pedido::status_pedido_enum;
END;
$$ LANGUAGE plpgsql;
