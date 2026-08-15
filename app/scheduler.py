"""Motor de geração de escala.

Estratégia: varre cronologicamente as sessões (cursos fixos expandidos pela
recorrência semanal dentro do período) e, para cada uma, escolhe o instrutor
elegível com menor carga horária já alocada (heurística gulosa de
balanceamento). Um curso fixo pode ter um instrutor "titular" pré-definido,
que é priorizado quando está disponível.

Cursos livres não entram automaticamente: como são turmas avulsas abertas sob
demanda, eles são anexados manualmente a uma escala já gerada (ver
`anexar_curso_livre`), a partir dos cursos livres cadastrados.
"""

from datetime import datetime, timedelta

from app.models import CursoFixo, Escala, Instrutor, Sessao, db


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


def _ocorrencia_curso_livre(curso):
    return {
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


def _estado_inicial(instrutores):
    return (
        {i.id: 0.0 for i in instrutores},  # horas_alocadas
        {},  # horas_semana: (instrutor_id, (ano, semana)) -> horas
        {i.id: [] for i in instrutores},  # agenda: instrutor_id -> [(data, inicio, fim)]
    )


def _estado_a_partir_da_escala(instrutores, escala):
    horas_alocadas, horas_semana, agenda = _estado_inicial(instrutores)
    for sessao in escala.sessoes:
        if not sessao.instrutor_id or sessao.instrutor_id not in horas_alocadas:
            continue
        duracao = _duracao_horas(sessao.hora_inicio, sessao.hora_fim)
        ano, semana, _ = sessao.data.isocalendar()
        horas_alocadas[sessao.instrutor_id] += duracao
        chave_semana = (sessao.instrutor_id, (ano, semana))
        horas_semana[chave_semana] = horas_semana.get(chave_semana, 0.0) + duracao
        agenda[sessao.instrutor_id].append((sessao.data, sessao.hora_inicio, sessao.hora_fim))
    return horas_alocadas, horas_semana, agenda


def _qualificados_por_categoria(instrutores):
    mapa = {}
    for instrutor in instrutores:
        for categoria in instrutor.categorias():
            mapa.setdefault(categoria, []).append(instrutor)
    return mapa


def _escolher_instrutor(oc, qualificados_por_categoria, horas_alocadas, horas_semana, agenda):
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

    titular_id = oc["instrutor_titular_id"]
    if titular_id is not None:
        titular = next((c for c in candidatos if c.id == titular_id), None)
        if titular is not None:
            return titular

    if candidatos:
        return min(candidatos, key=lambda i: (horas_alocadas[i.id], i.id))
    return None


def _criar_sessao_alocada(escala, oc, escolhido, horas_alocadas, horas_semana, agenda):
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
        duracao = _duracao_horas(oc["hora_inicio"], oc["hora_fim"])
        ano, semana, _ = oc["data"].isocalendar()
        semana_chave = (ano, semana)

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
    return sessao


def gerar_escala(data_inicio, data_fim):
    if data_inicio > data_fim:
        raise ValueError("data_inicio deve ser anterior ou igual a data_fim")

    escala = Escala(data_inicio=data_inicio, data_fim=data_fim)
    db.session.add(escala)

    ocorrencias = _expandir_cursos_fixos(data_inicio, data_fim)
    ocorrencias.sort(key=lambda o: (o["data"], o["hora_inicio"]))

    instrutores = Instrutor.query.filter_by(ativo=True).all()
    qualificados_por_categoria = _qualificados_por_categoria(instrutores)
    horas_alocadas, horas_semana, agenda = _estado_inicial(instrutores)

    for oc in ocorrencias:
        escolhido = _escolher_instrutor(oc, qualificados_por_categoria, horas_alocadas, horas_semana, agenda)
        _criar_sessao_alocada(escala, oc, escolhido, horas_alocadas, horas_semana, agenda)

    db.session.commit()
    return escala


def anexar_curso_livre(escala, curso_livre):
    """Anexa um curso livre já cadastrado a uma escala existente, alocando
    instrutor com base no estado atual da escala (evita conflitos e mantém o
    balanceamento de carga considerando o que já está alocado nela)."""

    instrutores = Instrutor.query.filter_by(ativo=True).all()
    qualificados_por_categoria = _qualificados_por_categoria(instrutores)
    horas_alocadas, horas_semana, agenda = _estado_a_partir_da_escala(instrutores, escala)

    oc = _ocorrencia_curso_livre(curso_livre)
    escolhido = _escolher_instrutor(oc, qualificados_por_categoria, horas_alocadas, horas_semana, agenda)
    sessao = _criar_sessao_alocada(escala, oc, escolhido, horas_alocadas, horas_semana, agenda)

    db.session.commit()
    return sessao
