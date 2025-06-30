from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
)
from dao.pedido_dao import registrar_pedido, listar_pedidos, detalhes_pedido, trocar_status
from dao.cardapio_dao import listar_itens_cardapio, persiste_item_cardapio
from auth.decorators import login_required

bp = Blueprint("pedidos", __name__)

ALLOWED_TRANSITIONS = {
    "em preparo": ["pronto", "cancelado"],
    "pronto": ["entregue", "cancelado"],
    "entregue": [],
    "cancelado": [],
}


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/cardapio", methods=["GET", "POST"])
def cardapio():
    if request.method == "POST":
        if not session.get("is_admin"):
            flash("Acesso restrito.", "danger")
            return render_template("cardapio.html", itens=itens)

        data = request.form
        criaItemDto = {
            "nome": data.get("novo-item-nome"),
            "preco": float(data.get("novo-item-valor")),
            "descricao": data.get("novo-item-descricao"),
            "quantidade_estoque": int(data.get("novo-item-estoque", 0)),
        }

        persiste_item_cardapio(criaItemDto)
        flash("Item inserido no Cardapio", "success")
        return redirect(url_for("pedidos.cardapio"))

    itens = listar_itens_cardapio()
    return render_template("cardapio.html", itens=itens)


@bp.route("/novo", methods=["GET", "POST"])
@login_required
def novo_pedido():
    if request.method == "GET":
        itens = listar_itens_cardapio()
        return render_template("novo_pedido.html", itens=itens)

    try:
        cliente_id = session["user_id"]
        itens = []
        for key, value in request.form.items():
            if key.startswith("quantidade-"):
                try:
                    item_id = int(key.split("-")[1])
                    quantidade = int(value) if value else 0
                    if quantidade > 0:
                        itens.append({"item_id": item_id, "quantidade": quantidade})
                except (ValueError, IndexError):
                    continue
        pedido_id = registrar_pedido(cliente_id, itens)
        flash("Pedido registrado com sucesso!", "success")
        return redirect(url_for("pedidos.detalhes", pedido_id=pedido_id))
    except Exception as e:
        flash(str(e), "danger")
        itens = listar_itens_cardapio()
        return render_template("novo_pedido.html", itens=itens)


@bp.route("/painel")
@login_required
def painel_admin():
    if not session.get("is_admin"):
        flash("Acesso restrito.", "danger")
        return redirect(url_for("pedidos.cardapio"))

    pedidos = listar_pedidos("em preparo")
    return render_template("painel_admin.html", pedidos=pedidos)


@bp.route('/detalhes/<int:pedido_id>', methods=['GET', 'POST'])
@login_required
def detalhes(pedido_id):
    pedido = detalhes_pedido(pedido_id)
    if not pedido:
        flash('Pedido não encontrado.', 'danger')
        return redirect(url_for('pedidos.cardapio'))

    status_atual = pedido['status']

    if request.method == 'POST':
        novo = request.form.get('novo_status')
        permitido = ALLOWED_TRANSITIONS.get(status_atual, [])
        if novo not in permitido:
            flash(f'Transição inválida: "{status_atual}" → "{novo}".', 'danger')
            return redirect(url_for('pedidos.detalhes', pedido_id=pedido_id))

        try:
            trocar_status(pedido_id, novo)
            flash('Status atualizado com sucesso.', 'success')
        except Exception as e:
            flash(f'Erro ao atualizar status: {e}', 'danger')

        return redirect(url_for('pedidos.detalhes', pedido_id=pedido_id))

    status_options = ALLOWED_TRANSITIONS.get(status_atual, [])
    return render_template(
        'detalhes_pedido.html',
        pedido=pedido,
        status_options=status_options
    )