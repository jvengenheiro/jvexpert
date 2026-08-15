from flask import Blueprint, render_template

from app.models import CursoFixo, CursoLivre, Escala, Instrutor

bp = Blueprint("dashboard", __name__)


@bp.route("/")
def index():
    resumo = {
        "instrutores": Instrutor.query.filter_by(ativo=True).count(),
        "cursos_fixos": CursoFixo.query.count(),
        "cursos_livres": CursoLivre.query.count(),
    }
    ultima_escala = Escala.query.order_by(Escala.id.desc()).first()
    return render_template("dashboard.html", resumo=resumo, ultima_escala=ultima_escala)
