from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.models import DIAS_SEMANA, CursoFixo, CursoLivre, Escala, Instrutor, db
from app.scheduler import anexar_curso_livre

bp = Blueprint("cursos", __name__)


def _parse_time(valor):
    return datetime.strptime(valor, "%H:%M").time()


def _parse_date(valor):
    return datetime.strptime(valor, "%Y-%m-%d").date()


def _int_ou_none(valor):
    if valor is None or valor == "":
        return None
    return int(valor)


# ---------- Cursos fixos ----------


@bp.route("/cursos-fixos")
def listar_fixos():
    cursos = CursoFixo.query.order_by(CursoFixo.nome).all()
    return render_template("cursos/fixos_list.html", cursos=cursos, dias_semana=dict(DIAS_SEMANA))


@bp.route("/cursos-fixos/novo", methods=["GET", "POST"])
def novo_fixo():
    instrutores = Instrutor.query.filter_by(ativo=True).order_by(Instrutor.nome).all()
    if request.method == "POST":
        try:
            curso = CursoFixo(
                nome=request.form["nome"].strip(),
                categoria=request.form["categoria"].strip(),
                carga_horaria=_int_ou_none(request.form.get("carga_horaria")),
                dia_semana=int(request.form["dia_semana"]),
                hora_inicio=_parse_time(request.form["hora_inicio"]),
                hora_fim=_parse_time(request.form["hora_fim"]),
                data_inicio=_parse_date(request.form["data_inicio"]),
                data_fim=_parse_date(request.form["data_fim"]),
                vagas=_int_ou_none(request.form.get("vagas")),
                instrutor_fixo_id=_int_ou_none(request.form.get("instrutor_fixo_id")),
            )
            if curso.hora_inicio >= curso.hora_fim:
                raise ValueError("horário de início deve ser antes do horário de fim")
            if curso.data_inicio > curso.data_fim:
                raise ValueError("data de início deve ser antes ou igual à data de fim")
            db.session.add(curso)
            db.session.commit()
            flash("Curso fixo cadastrado.", "success")
            return redirect(url_for("cursos.listar_fixos"))
        except (KeyError, ValueError) as exc:
            flash(f"Não foi possível salvar: {exc}", "danger")

    return render_template(
        "cursos/fixos_form.html", curso=None, instrutores=instrutores, dias_semana=DIAS_SEMANA
    )


@bp.route("/cursos-fixos/<int:curso_id>/editar", methods=["GET", "POST"])
def editar_fixo(curso_id):
    curso = CursoFixo.query.get_or_404(curso_id)
    instrutores = Instrutor.query.filter_by(ativo=True).order_by(Instrutor.nome).all()
    if request.method == "POST":
        try:
            curso.nome = request.form["nome"].strip()
            curso.categoria = request.form["categoria"].strip()
            curso.carga_horaria = _int_ou_none(request.form.get("carga_horaria"))
            curso.dia_semana = int(request.form["dia_semana"])
            curso.hora_inicio = _parse_time(request.form["hora_inicio"])
            curso.hora_fim = _parse_time(request.form["hora_fim"])
            curso.data_inicio = _parse_date(request.form["data_inicio"])
            curso.data_fim = _parse_date(request.form["data_fim"])
            curso.vagas = _int_ou_none(request.form.get("vagas"))
            curso.instrutor_fixo_id = _int_ou_none(request.form.get("instrutor_fixo_id"))
            if curso.hora_inicio >= curso.hora_fim:
                raise ValueError("horário de início deve ser antes do horário de fim")
            if curso.data_inicio > curso.data_fim:
                raise ValueError("data de início deve ser antes ou igual à data de fim")
            db.session.commit()
            flash("Curso fixo atualizado.", "success")
            return redirect(url_for("cursos.listar_fixos"))
        except (KeyError, ValueError) as exc:
            flash(f"Não foi possível salvar: {exc}", "danger")

    return render_template(
        "cursos/fixos_form.html", curso=curso, instrutores=instrutores, dias_semana=DIAS_SEMANA
    )


@bp.route("/cursos-fixos/<int:curso_id>/excluir", methods=["POST"])
def excluir_fixo(curso_id):
    curso = CursoFixo.query.get_or_404(curso_id)
    db.session.delete(curso)
    db.session.commit()
    flash("Curso fixo removido.", "success")
    return redirect(url_for("cursos.listar_fixos"))


# ---------- Cursos livres ----------


@bp.route("/cursos-livres")
def listar_livres():
    cursos = CursoLivre.query.order_by(CursoLivre.data).all()
    escalas = Escala.query.order_by(Escala.id.desc()).all()
    return render_template("cursos/livres_list.html", cursos=cursos, escalas=escalas)


@bp.route("/cursos-livres/novo", methods=["GET", "POST"])
def novo_livre():
    if request.method == "POST":
        try:
            curso = CursoLivre(
                nome=request.form["nome"].strip(),
                categoria=request.form["categoria"].strip(),
                carga_horaria=_int_ou_none(request.form.get("carga_horaria")),
                data=_parse_date(request.form["data"]),
                hora_inicio=_parse_time(request.form["hora_inicio"]),
                hora_fim=_parse_time(request.form["hora_fim"]),
                vagas=_int_ou_none(request.form.get("vagas")),
            )
            if curso.hora_inicio >= curso.hora_fim:
                raise ValueError("horário de início deve ser antes do horário de fim")
            db.session.add(curso)
            db.session.commit()
            flash("Curso livre cadastrado.", "success")
            return redirect(url_for("cursos.listar_livres"))
        except (KeyError, ValueError) as exc:
            flash(f"Não foi possível salvar: {exc}", "danger")

    return render_template("cursos/livres_form.html", curso=None)


@bp.route("/cursos-livres/<int:curso_id>/editar", methods=["GET", "POST"])
def editar_livre(curso_id):
    curso = CursoLivre.query.get_or_404(curso_id)
    if request.method == "POST":
        try:
            curso.nome = request.form["nome"].strip()
            curso.categoria = request.form["categoria"].strip()
            curso.carga_horaria = _int_ou_none(request.form.get("carga_horaria"))
            curso.data = _parse_date(request.form["data"])
            curso.hora_inicio = _parse_time(request.form["hora_inicio"])
            curso.hora_fim = _parse_time(request.form["hora_fim"])
            curso.vagas = _int_ou_none(request.form.get("vagas"))
            if curso.hora_inicio >= curso.hora_fim:
                raise ValueError("horário de início deve ser antes do horário de fim")
            db.session.commit()
            flash("Curso livre atualizado.", "success")
            return redirect(url_for("cursos.listar_livres"))
        except (KeyError, ValueError) as exc:
            flash(f"Não foi possível salvar: {exc}", "danger")

    return render_template("cursos/livres_form.html", curso=curso)


@bp.route("/cursos-livres/<int:curso_id>/excluir", methods=["POST"])
def excluir_livre(curso_id):
    curso = CursoLivre.query.get_or_404(curso_id)
    db.session.delete(curso)
    db.session.commit()
    flash("Curso livre removido.", "success")
    return redirect(url_for("cursos.listar_livres"))


@bp.route("/cursos-livres/<int:curso_id>/anexar", methods=["POST"])
def anexar_livre_a_escala(curso_id):
    curso = CursoLivre.query.get_or_404(curso_id)
    escala_id = request.form.get("escala_id")
    if not escala_id:
        flash("Selecione uma escala para anexar o curso.", "danger")
        return redirect(url_for("cursos.listar_livres"))

    escala = Escala.query.get_or_404(int(escala_id))
    if any(s.curso_livre_id == curso.id for s in escala.sessoes):
        flash("Este curso livre já está anexado a essa escala.", "warning")
        return redirect(url_for("escala.ver", escala_id=escala.id))

    sessao = anexar_curso_livre(escala, curso)
    if sessao.status == "confirmado":
        flash(f'Curso livre "{curso.nome}" anexado e alocado para {sessao.instrutor.nome}.', "success")
    else:
        flash(
            f'Curso livre "{curso.nome}" anexado, mas nenhum instrutor elegível está disponível — '
            "atribua manualmente na tela da escala.",
            "warning",
        )
    return redirect(url_for("escala.ver", escala_id=escala.id))
