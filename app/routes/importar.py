from pathlib import Path

from flask import Blueprint, flash, redirect, render_template, request, send_from_directory, url_for

from app.import_data import importar_cursos_fixos, importar_cursos_livres, importar_instrutores

bp = Blueprint("importar", __name__, url_prefix="/importar")

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

IMPORTADORES = {
    "instrutores": importar_instrutores,
    "cursos_fixos": importar_cursos_fixos,
    "cursos_livres": importar_cursos_livres,
}

ROTA_POS_IMPORT = {
    "instrutores": "instrutores.listar",
    "cursos_fixos": "cursos.listar_fixos",
    "cursos_livres": "cursos.listar_livres",
}


@bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        tipo = request.form.get("tipo")
        arquivo = request.files.get("arquivo")

        if tipo not in IMPORTADORES:
            flash("Selecione um tipo de importação válido.", "danger")
            return redirect(url_for("importar.index"))
        if not arquivo or not arquivo.filename:
            flash("Selecione um arquivo CSV ou Excel.", "danger")
            return redirect(url_for("importar.index"))

        try:
            criados, erros = IMPORTADORES[tipo](arquivo)
        except Exception as exc:  # noqa: BLE001 - erro de leitura do arquivo (colunas ausentes etc.)
            flash(f"Falha ao ler o arquivo: {exc}", "danger")
            return redirect(url_for("importar.index"))

        if criados:
            flash(f"{criados} registro(s) importado(s) com sucesso.", "success")
        if erros:
            flash("Algumas linhas tiveram problemas: " + " | ".join(erros[:10]), "warning")

        return redirect(url_for(ROTA_POS_IMPORT[tipo]))

    return render_template("importar/index.html")


@bp.route("/exemplo/<nome_arquivo>")
def exemplo(nome_arquivo):
    return send_from_directory(DATA_DIR, nome_arquivo, as_attachment=True)
