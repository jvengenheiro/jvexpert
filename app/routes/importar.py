from pathlib import Path

from flask import Blueprint, flash, redirect, render_template, request, send_from_directory, url_for

from app.import_data import detectar_tipo, ler_tabela, processar_cursos_fixos, processar_cursos_livres, processar_instrutores

bp = Blueprint("importar", __name__, url_prefix="/importar")

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

PROCESSADORES = {
    "instrutores": processar_instrutores,
    "cursos_fixos": processar_cursos_fixos,
    "cursos_livres": processar_cursos_livres,
}

ROTULOS_TIPO = {
    "instrutores": "instrutores",
    "cursos_fixos": "cursos fixos",
    "cursos_livres": "cursos livres",
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

        if tipo not in PROCESSADORES and tipo != "auto":
            flash("Selecione um tipo de importação válido.", "danger")
            return redirect(url_for("importar.index"))
        if not arquivo or not arquivo.filename:
            flash("Selecione um arquivo (CSV, Excel, Word ou PDF).", "danger")
            return redirect(url_for("importar.index"))

        try:
            rows, colunas = ler_tabela(arquivo)

            deteccao_automatica = tipo == "auto"
            if deteccao_automatica:
                tipo = detectar_tipo(colunas)
                if tipo is None:
                    flash(
                        "Não consegui identificar automaticamente se este arquivo é de instrutores, "
                        "cursos fixos ou cursos livres. Selecione o tipo manualmente e tente de novo. "
                        "Colunas encontradas: " + ", ".join(colunas),
                        "danger",
                    )
                    return redirect(url_for("importar.index"))

            criados, erros = PROCESSADORES[tipo](rows, colunas)
        except Exception as exc:  # noqa: BLE001 - erro de leitura do arquivo (colunas ausentes, tabela vazia etc.)
            flash(f"Falha ao ler o arquivo: {exc}", "danger")
            return redirect(url_for("importar.index"))

        prefixo = f"Detectado como {ROTULOS_TIPO[tipo]}. " if deteccao_automatica else ""
        if criados:
            flash(f"{prefixo}{criados} registro(s) importado(s) com sucesso.", "success")
        elif prefixo:
            flash(prefixo + "Nenhum registro importado.", "warning")
        if erros:
            flash("Algumas linhas tiveram problemas: " + " | ".join(erros[:10]), "warning")

        return redirect(url_for(ROTA_POS_IMPORT[tipo]))

    return render_template("importar/index.html")


@bp.route("/exemplo/<nome_arquivo>")
def exemplo(nome_arquivo):
    return send_from_directory(DATA_DIR, nome_arquivo, as_attachment=True)
