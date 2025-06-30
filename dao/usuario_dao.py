from db import get_conn
from werkzeug.security import generate_password_hash, check_password_hash

def autenticar_usuario(username, senha):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, username, senha_hash, is_admin FROM usuarios WHERE username = %s",
                (username,)
            )
            row = cur.fetchone()
            if row and check_password_hash(row[2], senha):
                return {
                    "id": row[0],
                    "username": row[1],
                    "is_admin": row[3]
                }
            return None


def criar_usuario(username, senha, is_admin=False):
    senha_hash = generate_password_hash(senha)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO usuarios (username, senha_hash, is_admin) VALUES (%s, %s, %s) RETURNING id",
                (username, senha_hash, is_admin)
            )
            user_id = cur.fetchone()[0]
            conn.commit()
            return user_id
        

def buscar_usuario_por_username(username):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, username, senha_hash, is_admin FROM usuarios WHERE username = %s",
                (username,)
            )
            row = cur.fetchone()
            if row:
                return {
                    "id": row[0],
                    "username": row[1],
                    "senha_hash": row[2],
                    "is_admin": row[3]
                }
            return None