from db import get_conn
import json

def registrar_pedido(cliente_id, itens):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT registrar_pedido(%s, %s::json)",
                (cliente_id, json.dumps(itens))
            )
            pedido_id = cur.fetchone()[0]
            return pedido_id

def listar_pedidos(status):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    pedido.id id,
                    pedido.status status,
                    cliente.username cliente_nome,
                    pedido.data_hora data_hora 
                FROM pedidos pedido
                INNER JOIN usuarios cliente ON cliente.id = pedido.cliente_id
                WHERE pedido.status = %s
                ORDER BY pedido.data_hora
            """, (status,))
            colnames = [desc[0] for desc in cur.description]
            return [dict(zip(colnames, row)) for row in cur.fetchall()]

def detalhes_pedido(pedido_id):
    dados_pedido = None
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    p.id AS id, 
                    p.status AS status, 
                    cliente.username AS cliente_nome
                FROM pedidos p
                INNER JOIN usuarios cliente ON cliente.id = p.cliente_id
                WHERE p.id = %s
                """,
                (pedido_id,)
            )
            row = cur.fetchone()
            if not row:
                return None
            colnames = [desc[0] for desc in cur.description]
            dados_pedido = dict(zip(colnames, row))

        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    itens_cardapio.nome nome, 
                    itens_pedido.quantidade quantidade 
                FROM itens_pedido
                INNER JOIN itens_cardapio ON itens_cardapio.id = itens_pedido.item_id
                WHERE itens_pedido.pedido_id = %s
                """,
                (pedido_id,)
            )
            colnames = [desc[0] for desc in cur.description]
            dados_pedido["itens"] = [
                dict(zip(colnames, row)) for row in cur.fetchall()
            ]
    return dados_pedido

def trocar_status(pedido_id, novo_status):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE pedidos SET status = %s WHERE id = %s",
        (novo_status, pedido_id)
    )
    conn.commit()
    cur.close()
    conn.close()