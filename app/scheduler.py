"""Motor de geração de escala.

Estratégia: varre cronologicamente todas as sessões (cursos fixos expandidos
pela recorrência semanal + cursos livres do período) e, para cada uma, escolhe
o instrutor elegível com menor carga horária já alocada (heurística gulosa de
balanceamento). Um curso fixo pode ter um instrutor "titular" pré-definido,
que é priorizado quando está disponível.
"""

from datetime import datetime, timedelta

from app.models import Bloqueio, CursoFixo, CursoLivre, Disponibilidade, Escala, Instrutor, Sessao, db


def _duracao_horas(hora_inicio, hora_fim):
    inicio = datetime.combine(datetime.min, hora_inicio)
    fim = datetime.combine(datetime.min, hora_fim)
    return (fim - inicio).total_seconds() / 3600


def _expandir_cursos_fixos(data_inicio, data_fim):
    ocorrencias = []
    for curso in CursoFixo.query.all():
        inicio_efetivo = max(data_inicio, curso.data_inicio)
        fim_efetivo = min(data_fim, curso.data_fim)
        if inicio_efetivo > fim_efetivo:
            continue
        dia = inicio_efetivo
        while dia <= fim_efetivo:
            if dia.weekday() == curso.dia_semana:
                ocorrencias.append(
                    {
                        "origem": "fixo",
                        "curso_fixo_id": curso.id,
                        "curso_livre_id": None,
                        "nome_curso": curso.nome,
                        "categoria": curso.categoria,
                        "data": dia,
                        "hora_inicio": curso.hora_inicio,
                        "hora_fim": curso.hora_fim,
                        "instrutor_titular_id": curso.instrutor_fixo_id,
                    }
                )
            dia += timedelta(days=1)
    return ocorrencias


def _coletar_cursos_livres(data_inicio, data_fim):
    ocorrencias = []
    cursos = CursoLivre.query.filter(
        CursoLivre.data >= data_inicio, CursoLivre.data <= data_fim
    ).all()
    for curso in cursos:
        ocorrencias.append(
            {
                "origem": "livre",
                "curso_fixo_id": None,
                "curso_livre_id": curso.id,
                "nome_curso": curso.nome,
                "categoria": curso.categoria,
                "data": curso.data,
                "hora_inicio": curso.hora_inicio,
                "hora_fim": curso.hora_fim,
                "instrutor_titular_id": None,
            }
        )
    return ocorrencias


def _disponivel(instrutor, data, hora_inicio, hora_fim):
    for bloqueio in instrutor.bloqueios:
        if bloqueio.data_inicio <= data <= bloqueio.data_fim:
            return False

    if not instrutor.disponibilidades:
        return True

    dia_semana = data.weekday()
    for disp in instrutor.disponibilidades:
        if disp.dia_semana == dia_semana and disp.hora_inicio <= hora_inicio and disp.hora_fim >= hora_fim:
            return True
    return False


def _sem_conflito(agenda_instrutor, data, hora_inicio, hora_fim):
    for (d, inicio, fim) in agenda_instrutor:
        if d == data and hora_inicio < fim and inicio < hora_fim:
            return False
    return True


def gerar_escala(data_inicio, data_fim):
    if data_inicio > data_fim:
        raise ValueError("data_inicio deve ser anterior ou igual a data_fim")

    escala = Escala(data_inicio=data_inicio, data_fim=data_fim)
    db.session.add(escala)

    ocorrencias = _expandir_cursos_fixos(data_inicio, data_fim) + _coletar_cursos_livres(
        data_inicio, data_fim
    )
    ocorrencias.sort(key=lambda o: (o["data"], o["hora_inicio"]))

    instrutores = Instrutor.query.filter_by(ativo=True).all()
    qualificados_por_categoria = {}
    for instrutor in instrutores:
        for categoria in instrutor.categorias():
            qualificados_por_categoria.setdefault(categoria, []).append(instrutor)

    horas_alocadas = {i.id: 0.0 for i in instrutores}
    horas_semana = {}  # (instrutor_id, (ano, semana)) -> horas
    agenda = {i.id: [] for i in instrutores}

    for oc in ocorrencias:
        duracao = _duracao_horas(oc["hora_inicio"], oc["hora_fim"])
        ano, semana, _ = oc["data"].isocalendar()
        semana_chave = (ano, semana)

        candidatos = [
            i
            for i in qualificados_por_categoria.get(oc["categoria"], [])
            if _disponivel(i, oc["data"], oc["hora_inicio"], oc["hora_fim"])
            and _sem_conflito(agenda[i.id], oc["data"], oc["hora_inicio"], oc["hora_fim"])
            and (
                i.carga_horaria_semanal_max is None
                or horas_semana.get((i.id, semana_chave), 0.0) + duracao <= i.carga_horaria_semanal_max
            )
        ]

        escolhido = None
        titular_id = oc["instrutor_titular_id"]
        if titular_id is not None:
            titular = next((c for c in candidatos if c.id == titular_id), None)
            if titular is not None:
                escolhido = titular

        if escolhido is None and candidatos:
            escolhido = min(candidatos, key=lambda i: (horas_alocadas[i.id], i.id))

        sessao = Sessao(
            escala=escala,
            origem=oc["origem"],
            curso_fixo_id=oc["curso_fixo_id"],
            curso_livre_id=oc["curso_livre_id"],
            nome_curso=oc["nome_curso"],
            categoria=oc["categoria"],
            data=oc["data"],
            hora_inicio=oc["hora_inicio"],
            hora_fim=oc["hora_fim"],
        )

        if escolhido is not None:
            sessao.instrutor_id = escolhido.id
            sessao.status = "confirmado"
            horas_alocadas[escolhido.id] += duracao
            horas_semana[(escolhido.id, semana_chave)] = (
                horas_semana.get((escolhido.id, semana_chave), 0.0) + duracao
            )
            agenda[escolhido.id].append((oc["data"], oc["hora_inicio"], oc["hora_fim"]))
        else:
            sessao.status = "sem_instrutor"

        db.session.add(sessao)

    db.session.commit()
    return escala
