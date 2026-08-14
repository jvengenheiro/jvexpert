from datetime import date, time

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

DIAS_SEMANA = [
    (0, "Segunda-feira"),
    (1, "Terça-feira"),
    (2, "Quarta-feira"),
    (3, "Quinta-feira"),
    (4, "Sexta-feira"),
    (5, "Sábado"),
    (6, "Domingo"),
]


class Instrutor(db.Model):
    __tablename__ = "instrutor"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150))
    telefone = db.Column(db.String(30))
    carga_horaria_semanal_max = db.Column(db.Integer)  # horas/semana, opcional
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    sigop_id = db.Column(db.String(50))  # id externo, para futura integração

    qualificacoes = db.relationship(
        "Qualificacao", backref="instrutor", cascade="all, delete-orphan"
    )
    disponibilidades = db.relationship(
        "Disponibilidade", backref="instrutor", cascade="all, delete-orphan"
    )
    bloqueios = db.relationship(
        "Bloqueio", backref="instrutor", cascade="all, delete-orphan"
    )

    def categorias(self):
        return {q.categoria for q in self.qualificacoes}


class Qualificacao(db.Model):
    """Categoria/tipo de curso que o instrutor está habilitado a ministrar."""

    __tablename__ = "qualificacao"

    id = db.Column(db.Integer, primary_key=True)
    instrutor_id = db.Column(db.Integer, db.ForeignKey("instrutor.id"), nullable=False)
    categoria = db.Column(db.String(100), nullable=False)


class Disponibilidade(db.Model):
    """Janela semanal recorrente em que o instrutor pode dar aula (usada para cursos fixos)."""

    __tablename__ = "disponibilidade"

    id = db.Column(db.Integer, primary_key=True)
    instrutor_id = db.Column(db.Integer, db.ForeignKey("instrutor.id"), nullable=False)
    dia_semana = db.Column(db.Integer, nullable=False)  # 0=segunda ... 6=domingo
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fim = db.Column(db.Time, nullable=False)


class Bloqueio(db.Model):
    """Indisponibilidade pontual (férias, folga, atestado) numa data específica."""

    __tablename__ = "bloqueio"

    id = db.Column(db.Integer, primary_key=True)
    instrutor_id = db.Column(db.Integer, db.ForeignKey("instrutor.id"), nullable=False)
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=False)
    motivo = db.Column(db.String(200))


class CursoFixo(db.Model):
    """Curso de grade curricular fixa, com turma recorrente semanalmente."""

    __tablename__ = "curso_fixo"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    categoria = db.Column(db.String(100), nullable=False)
    carga_horaria = db.Column(db.Integer)  # horas totais do curso
    dia_semana = db.Column(db.Integer, nullable=False)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fim = db.Column(db.Time, nullable=False)
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=False)
    vagas = db.Column(db.Integer)
    instrutor_fixo_id = db.Column(db.Integer, db.ForeignKey("instrutor.id"))
    sigop_id = db.Column(db.String(50))

    instrutor_fixo = db.relationship("Instrutor")


class CursoLivre(db.Model):
    """Curso livre/avulso: turma pontual, aberta sob demanda, sem recorrência."""

    __tablename__ = "curso_livre"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    categoria = db.Column(db.String(100), nullable=False)
    carga_horaria = db.Column(db.Integer)
    data = db.Column(db.Date, nullable=False)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fim = db.Column(db.Time, nullable=False)
    vagas = db.Column(db.Integer)
    sigop_id = db.Column(db.String(50))


class Sessao(db.Model):
    """Ocorrência concreta de uma aula (gerada a partir de curso fixo ou livre) numa escala."""

    __tablename__ = "sessao"

    id = db.Column(db.Integer, primary_key=True)
    escala_id = db.Column(db.Integer, db.ForeignKey("escala.id"), nullable=False)
    origem = db.Column(db.String(10), nullable=False)  # 'fixo' | 'livre'
    curso_fixo_id = db.Column(db.Integer, db.ForeignKey("curso_fixo.id"))
    curso_livre_id = db.Column(db.Integer, db.ForeignKey("curso_livre.id"))
    nome_curso = db.Column(db.String(150), nullable=False)
    categoria = db.Column(db.String(100), nullable=False)
    data = db.Column(db.Date, nullable=False)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fim = db.Column(db.Time, nullable=False)
    instrutor_id = db.Column(db.Integer, db.ForeignKey("instrutor.id"))
    status = db.Column(db.String(20), nullable=False, default="pendente")
    # status: 'confirmado' | 'sem_instrutor'

    instrutor = db.relationship("Instrutor")


class Escala(db.Model):
    """Uma geração de escala para um período (data_inicio a data_fim)."""

    __tablename__ = "escala"

    id = db.Column(db.Integer, primary_key=True)
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=False)
    criada_em = db.Column(db.DateTime, server_default=db.func.now())

    sessoes = db.relationship(
        "Sessao", backref="escala", cascade="all, delete-orphan", order_by="Sessao.data, Sessao.hora_inicio"
    )
