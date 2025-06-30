import psycopg2
from flask import g, current_app

def get_conn():
    if 'db_conn' not in g:
        g.db_conn = psycopg2.connect(current_app.config['DATABASE_URI'])
    return g.db_conn

def close_conn(e=None):
    db_conn = g.pop('db_conn', None)
    if db_conn is not None:
        db_conn.close()
