from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app.models import DIAS_SEMANA, Bloqueio, Disponibilidade, Instrutor, Qualificacao, db

bp = Blueprint("instrutores", __name__, url_prefix="/instrutores")


def _parse_time(valor):
    return datetime.strptime(valor, "%H:%M").time()


def _parse_date(valor):
    return datetime.strptime(valor, "%Y-%m-%d").date()


@bp.route("/")
def listar():
    instrutores = Instrutor.query.order_by(Instrutor.nome).all()
    return render_template("instrutores/list.html", instrutores=instrutores)


@bp.route("/novo", methods=["GET", "POST"])
def novo():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        if not nome:
            flash("Nome é obrigatório.", "danger")
            return render_template("instrutores/form.html", instrutor=None)

        instrutor = Instrutor(
            nome=nome,
            email=request.form.get("email") or None,
            telefone=request.form.get("telefone") or None,
            carga_horaria_semanal_max=_int_ou_none(request.form.get("carga_horaria_semanal_max")),
        )
        db.session.add(instrutor)
        db.session.commit()
        flash("Instrutor cadastrado com sucesso.", "success")
        return redirect(url_for("instrutores.detalhe", instrutor_id=instrutor.id))

    return render_template("instrutores/form.html", instrutor=None)


@bp.route("/<int:instrutor_id>")
def detalhe(instrutor_id):
    instrutor = Instrutor.query.get_or_404(instrutor_id)
    return render_template(
        "instrutores/detalhe.html",
        instrutor=instrutor,
        dias_semana=dict(DIAS_SEMANA),
        dias_semana_opcoes=DIAS_SEMANA,
    )


@bp.route("/<int:instrutor_id>/editar", methods=["GET", "POST"])
def editar(instrutor_id):
    instrutor = Instrutor.query.get_or_404(instrutor_id)
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        if not nome:
            flash("Nome é obrigatório.", "danger")
            return render_template("instrutores/form.html", instrutor=instrutor)

        instrutor.nome = nome
        instrutor.email = request.form.get("email") or None
        instrutor.telefone = request.form.get("telefone") or None
        instrutor.carga_horaria_semanal_max = _int_ou_none(
            request.form.get("carga_horaria_semanal_max")
        )
        instrutor.ativo = bool(request.form.get("ativo"))
        db.session.commit()
        flash("Instrutor atualizado.", "success")
        return redirect(url_for("instrutores.detalhe", instrutor_id=instrutor.id))

    return render_template("instrutores/form.html", instrutor=instrutor)


@bp.route("/<int:instrutor_id>/excluir", methods=["POST"])
def excluir(instrutor_id):
    instrutor = Instrutor.query.get_or_404(instrutor_id)
    db.session.delete(instrutor)
    db.session.commit()
    flash("Instrutor removido.", "success")
    return redirect(url_for("instrutores.listar"))


@bp.route("/<int:instrutor_id>/qualificacoes/adicionar", methods=["POST"])
def adicionar_qualificacao(instrutor_id):
    instrutor = Instrutor.query.get_or_404(instrutor_id)
    categoria = request.form.get("categoria", "").strip()
    if categoria:
        db.session.add(Qualificacao(instrutor_id=instrutor.id, categoria=categoria))
        db.session.commit()
        flash("Qualificação adicionada.", "success")
    return redirect(url_for("instrutores.detalhe", instrutor_id=instrutor.id))


@bp.route("/<int:instrutor_id>/qualificacoes/<int:qualificacao_id>/remover", methods=["POST"])
def remover_qualificacao(instrutor_id, qualificacao_id):
    qualificacao = Qualificacao.query.get_or_404(qualificacao_id)
    if qualificacao.instrutor_id != instrutor_id:
        abort(404)
    db.session.delete(qualificacao)
    db.session.commit()
    return redirect(url_for("instrutores.detalhe", instrutor_id=instrutor_id))


@bp.route("/<int:instrutor_id>/disponibilidade/adicionar", methods=["POST"])
def adicionar_disponibilidade(instrutor_id):
    instrutor = Instrutor.query.get_or_404(instrutor_id)
    try:
        disp = Disponibilidade(
            instrutor_id=instrutor.id,
            dia_semana=int(request.form["dia_semana"]),
            hora_inicio=_parse_time(request.form["hora_inicio"]),
            hora_fim=_parse_time(request.form["hora_fim"]),
        )
        if disp.hora_inicio >= disp.hora_fim:
            raise ValueError("hora_inicio deve ser antes de hora_fim")
        db.session.add(disp)
        db.session.commit()
        flash("Disponibilidade adicionada.", "success")
    except (KeyError, ValueError) as exc:
        flash(f"Não foi possível adicionar a disponibilidade: {exc}", "danger")
    return redirect(url_for("instrutores.detalhe", instrutor_id=instrutor.id))


@bp.route("/<int:instrutor_id>/disponibilidade/<int:disponibilidade_id>/remover", methods=["POST"])
def remover_disponibilidade(instrutor_id, disponibilidade_id):
    disp = Disponibilidade.query.get_or_404(disponibilidade_id)
    if disp.instrutor_id != instrutor_id:
        abort(404)
    db.session.delete(disp)
    db.session.commit()
    return redirect(url_for("instrutores.detalhe", instrutor_id=instrutor_id))


@bp.route("/<int:instrutor_id>/bloqueios/adicionar", methods=["POST"])
def adicionar_bloqueio(instrutor_id):
    instrutor = Instrutor.query.get_or_404(instrutor_id)
    try:
        bloqueio = Bloqueio(
            instrutor_id=instrutor.id,
            data_inicio=_parse_date(request.form["data_inicio"]),
            data_fim=_parse_date(request.form["data_fim"]),
            motivo=request.form.get("motivo") or None,
        )
        if bloqueio.data_inicio > bloqueio.data_fim:
            raise ValueError("data_inicio deve ser antes ou igual a data_fim")
        db.session.add(bloqueio)
        db.session.commit()
        flash("Bloqueio adicionado.", "success")
    except (KeyError, ValueError) as exc:
        flash(f"Não foi possível adicionar o bloqueio: {exc}", "danger")
    return redirect(url_for("instrutores.detalhe", instrutor_id=instrutor.id))


@bp.route("/<int:instrutor_id>/bloqueios/<int:bloqueio_id>/remover", methods=["POST"])
def remover_bloqueio(instrutor_id, bloqueio_id):
    bloqueio = Bloqueio.query.get_or_404(bloqueio_id)
    if bloqueio.instrutor_id != instrutor_id:
        abort(404)
    db.session.delete(bloqueio)
    db.session.commit()
    return redirect(url_for("instrutores.detalhe", instrutor_id=instrutor_id))


def _int_ou_none(valor):
    if valor is None or valor == "":
        return None
    return int(valor)
