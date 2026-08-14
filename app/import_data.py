"""Importação de instrutores e cursos a partir de planilhas CSV/Excel.

Pensado para receber arquivos exportados do SIGOP (ou preenchidos manualmente)
seguindo os modelos em data/exemplo_*.csv. Colunas desconhecidas são ignoradas;
colunas obrigatórias ausentes geram erro por linha, reportado ao usuário.
"""

from datetime import datetime

import pandas as pd

from app.models import CursoFixo, CursoLivre, Instrutor, Qualificacao, db

DIAS_SEMANA_NOMES = {
    "segunda": 0,
    "segunda-feira": 0,
    "terca": 1,
    "terça": 1,
    "terca-feira": 1,
    "terça-feira": 1,
    "quarta": 2,
    "quarta-feira": 2,
    "quinta": 3,
    "quinta-feira": 3,
    "sexta": 4,
    "sexta-feira": 4,
    "sabado": 5,
    "sábado": 5,
    "domingo": 6,
}


def _ler_planilha(arquivo):
    nome = (arquivo.filename or "").lower()
    if nome.endswith(".xlsx") or nome.endswith(".xls"):
        return pd.read_excel(arquivo)
    return pd.read_csv(arquivo)


def _parse_dia_semana(valor):
    texto = str(valor).strip().lower()
    if texto in DIAS_SEMANA_NOMES:
        return DIAS_SEMANA_NOMES[texto]
    try:
        dia = int(texto)
    except ValueError as exc:
        raise ValueError(f"dia_semana inválido: {valor!r}") from exc
    if not 0 <= dia <= 6:
        raise ValueError(f"dia_semana fora do intervalo 0-6: {valor!r}")
    return dia


def _parse_hora(valor):
    texto = str(valor).strip()
    for formato in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(texto, formato).time()
        except ValueError:
            continue
    raise ValueError(f"horário inválido (use HH:MM): {valor!r}")


def _parse_data(valor):
    if isinstance(valor, datetime):
        return valor.date()
    texto = str(valor).strip()
    for formato in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    raise ValueError(f"data inválida (use AAAA-MM-DD): {valor!r}")


def _linha_para_erro(indice, exc):
    return f"linha {indice + 2}: {exc}"


def importar_instrutores(arquivo):
    df = _ler_planilha(arquivo)
    erros = []
    criados = 0
    for indice, linha in df.iterrows():
        try:
            nome = str(linha["nome"]).strip()
            if not nome or nome.lower() == "nan":
                raise ValueError("nome é obrigatório")

            instrutor = Instrutor.query.filter_by(nome=nome).first()
            if instrutor is None:
                instrutor = Instrutor(nome=nome)
                db.session.add(instrutor)

            instrutor.email = _valor_opcional(linha, "email")
            instrutor.telefone = _valor_opcional(linha, "telefone")
            instrutor.sigop_id = _valor_opcional(linha, "sigop_id")

            carga = _valor_opcional(linha, "carga_horaria_semanal_max")
            instrutor.carga_horaria_semanal_max = int(carga) if carga else None

            categorias_raw = _valor_opcional(linha, "categorias")
            if categorias_raw:
                instrutor.qualificacoes = [
                    Qualificacao(categoria=c.strip())
                    for c in categorias_raw.split(";")
                    if c.strip()
                ]

            criados += 1
        except Exception as exc:  # noqa: BLE001 - reportamos linha a linha
            erros.append(_linha_para_erro(indice, exc))

    db.session.commit()
    return criados, erros


def importar_cursos_fixos(arquivo):
    df = _ler_planilha(arquivo)
    erros = []
    criados = 0
    for indice, linha in df.iterrows():
        try:
            instrutor_id = None
            instrutor_nome = _valor_opcional(linha, "instrutor")
            if instrutor_nome:
                instrutor = Instrutor.query.filter_by(nome=instrutor_nome).first()
                if instrutor is None:
                    raise ValueError(f"instrutor não encontrado: {instrutor_nome!r}")
                instrutor_id = instrutor.id

            curso = CursoFixo(
                nome=str(linha["nome"]).strip(),
                categoria=str(linha["categoria"]).strip(),
                carga_horaria=_valor_opcional(linha, "carga_horaria") or None,
                dia_semana=_parse_dia_semana(linha["dia_semana"]),
                hora_inicio=_parse_hora(linha["hora_inicio"]),
                hora_fim=_parse_hora(linha["hora_fim"]),
                data_inicio=_parse_data(linha["data_inicio"]),
                data_fim=_parse_data(linha["data_fim"]),
                vagas=_valor_opcional(linha, "vagas") or None,
                instrutor_fixo_id=instrutor_id,
                sigop_id=_valor_opcional(linha, "sigop_id"),
            )
            db.session.add(curso)
            criados += 1
        except Exception as exc:  # noqa: BLE001
            erros.append(_linha_para_erro(indice, exc))

    db.session.commit()
    return criados, erros


def importar_cursos_livres(arquivo):
    df = _ler_planilha(arquivo)
    erros = []
    criados = 0
    for indice, linha in df.iterrows():
        try:
            curso = CursoLivre(
                nome=str(linha["nome"]).strip(),
                categoria=str(linha["categoria"]).strip(),
                carga_horaria=_valor_opcional(linha, "carga_horaria") or None,
                data=_parse_data(linha["data"]),
                hora_inicio=_parse_hora(linha["hora_inicio"]),
                hora_fim=_parse_hora(linha["hora_fim"]),
                vagas=_valor_opcional(linha, "vagas") or None,
                sigop_id=_valor_opcional(linha, "sigop_id"),
            )
            db.session.add(curso)
            criados += 1
        except Exception as exc:  # noqa: BLE001
            erros.append(_linha_para_erro(indice, exc))

    db.session.commit()
    return criados, erros


def _valor_opcional(linha, coluna):
    if coluna not in linha or pd.isna(linha[coluna]):
        return None
    valor = str(linha[coluna]).strip()
    return valor or None
