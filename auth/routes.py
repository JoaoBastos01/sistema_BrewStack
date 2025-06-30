from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from dao.usuario_dao import buscar_usuario_por_username, criar_usuario, autenticar_usuario

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    username = request.form['username']
    senha = request.form['senha']
    is_admin = bool(request.form.get('ehAdmin', False))

    if buscar_usuario_por_username(username):
        flash('Usuário já existe.', 'danger')
        return render_template('register.html')

    criar_usuario(username, senha, is_admin)
    flash('Usuário criado com sucesso!', 'success')
    return redirect(url_for('auth.login'))
    

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    usuario = autenticar_usuario(request.form['username'], request.form['senha'])
    if usuario == None:
        flash('Dados inválidos.', 'danger')
        return render_template('login.html')

    session['username'] = usuario['username']
    session['user_id'] = usuario['id']
    session['is_admin'] = usuario['is_admin']
    flash('Login realizado com sucesso!', 'success')
    return redirect(url_for('pedidos.cardapio'))

@bp.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado.', 'info')
    return redirect(url_for('auth.login'))
