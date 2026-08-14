import csv
import io
from datetime import datetime

from flask import Blueprint, Response, flash, redirect, render_template, request, url_for

from app.models import DIAS_SEMANA, Escala, Instrutor, Sessao, db
from app.scheduler import gerar_escala

bp = Blueprint("escala", __name__, url_prefix="/escala")


def _parse_date(valor):
    return datetime.strptime(valor, "%Y-%m-%d").date()


@bp.route("/")
def listar():
    escalas = Escala.query.order_by(Escala.id.desc()).all()
    return render_template("escala/listar.html", escalas=escalas)


@bp.route("/gerar", methods=["POST"])
def gerar():
    try:
        data_inicio = _parse_date(request.form["data_inicio"])
        data_fim = _parse_date(request.form["data_fim"])
        escala = gerar_escala(data_inicio, data_fim)
        pendentes = sum(1 for s in escala.sessoes if s.status == "sem_instrutor")
        if pendentes:
            flash(
                f"Escala gerada com {pendentes} sessão(ões) sem instrutor disponível — "
                "revise manualmente abaixo.",
                "warning",
            )
        else:
            flash("Escala gerada com sucesso — todas as sessões têm instrutor.", "success")
        return redirect(url_for("escala.ver", escala_id=escala.id))
    except (KeyError, ValueError) as exc:
        flash(f"Não foi possível gerar a escala: {exc}", "danger")
        return redirect(url_for("escala.listar"))


@bp.route("/<int:escala_id>")
def ver(escala_id):
    escala = Escala.query.get_or_404(escala_id)
    instrutores = Instrutor.query.filter_by(ativo=True).order_by(Instrutor.nome).all()

    sessoes_por_dia = {}
    for sessao in escala.sessoes:
        sessoes_por_dia.setdefault(sessao.data, []).append(sessao)

    horas_por_instrutor = {}
    for sessao in escala.sessoes:
        if sessao.instrutor_id:
            inicio = datetime.combine(datetime.min, sessao.hora_inicio)
            fim = datetime.combine(datetime.min, sessao.hora_fim)
            horas = (fim - inicio).total_seconds() / 3600
            chave = sessao.instrutor.nome
            horas_por_instrutor[chave] = horas_por_instrutor.get(chave, 0) + horas

    return render_template(
        "escala/ver.html",
        escala=escala,
        sessoes_por_dia=sorted(sessoes_por_dia.items()),
        instrutores=instrutores,
        dias_semana=dict(DIAS_SEMANA),
        horas_por_instrutor=sorted(horas_por_instrutor.items(), key=lambda kv: -kv[1]),
    )


@bp.route("/<int:escala_id>/sessao/<int:sessao_id>/reatribuir", methods=["POST"])
def reatribuir(escala_id, sessao_id):
    sessao = Sessao.query.get_or_404(sessao_id)
    if sessao.escala_id != escala_id:
        flash("Sessão não pertence a esta escala.", "danger")
        return redirect(url_for("escala.ver", escala_id=escala_id))

    instrutor_id = request.form.get("instrutor_id") or None
    sessao.instrutor_id = int(instrutor_id) if instrutor_id else None
    sessao.status = "confirmado" if sessao.instrutor_id else "sem_instrutor"
    db.session.commit()
    flash("Sessão atualizada manualmente.", "success")
    return redirect(url_for("escala.ver", escala_id=escala_id))


@bp.route("/<int:escala_id>/excluir", methods=["POST"])
def excluir(escala_id):
    escala = Escala.query.get_or_404(escala_id)
    db.session.delete(escala)
    db.session.commit()
    flash("Escala removida.", "success")
    return redirect(url_for("escala.listar"))


@bp.route("/<int:escala_id>/exportar.csv")
def exportar(escala_id):
    escala = Escala.query.get_or_404(escala_id)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["data", "dia_semana", "hora_inicio", "hora_fim", "curso", "categoria", "origem", "instrutor", "status"])
    for sessao in escala.sessoes:
        writer.writerow(
            [
                sessao.data.isoformat(),
                dict(DIAS_SEMANA)[sessao.data.weekday()],
                sessao.hora_inicio.strftime("%H:%M"),
                sessao.hora_fim.strftime("%H:%M"),
                sessao.nome_curso,
                sessao.categoria,
                sessao.origem,
                sessao.instrutor.nome if sessao.instrutor else "",
                sessao.status,
            ]
        )

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=escala_{escala.data_inicio}_{escala.data_fim}.csv"
        },
    )
