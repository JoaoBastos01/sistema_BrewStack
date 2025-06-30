from db import get_conn

def listar_itens_cardapio():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM itens_cardapio")
            colnames = [desc[0] for desc in cur.description]
            return [dict(zip(colnames, row)) for row in cur.fetchall()]

def persiste_item_cardapio(criaItemDto):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO itens_cardapio (nome, preco, descricao, quantidade_estoque)
                VALUES (%s, %s, %s, %s)
            """, (criaItemDto["nome"], criaItemDto["preco"], criaItemDto["descricao"], criaItemDto["quantidade_estoque"])
            )