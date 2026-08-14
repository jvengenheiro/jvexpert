# Escala de Instrutores

Sistema web para gerar a escala de instrutores, considerando dois tipos de curso:

- **Cursos fixos**: grade curricular recorrente (mesmo dia da semana e horário, ao longo de um período).
- **Cursos livres**: turmas avulsas, com data específica, abertas sob demanda.

Ao gerar uma escala para um período, os **cursos fixos** são expandidos automaticamente (uma sessão para
cada ocorrência semanal dentro do período). Os **cursos livres** não entram automaticamente — como são
turmas avulsas abertas sob demanda, você os anexa manualmente à escala pelo botão **"Anexar curso livre"**
na tela da escala, escolhendo entre os que já estão cadastrados.

Em ambos os casos, o sistema aloca instrutor automaticamente respeitando:

- **Qualificação**: só recebe cursos das categorias em que está habilitado.
- **Disponibilidade**: janelas semanais recorrentes cadastradas (opcional — sem cadastro, considera-se disponível sempre) e bloqueios pontuais (férias, folgas, atestados).
- **Conflito de horário**: um instrutor nunca é escalado em dois cursos que se sobrepõem.
- **Balanceamento de carga**: prioriza sempre o instrutor elegível com menor carga horária já alocada na escala; respeita um limite máximo de horas/semana quando definido.
- **Instrutor titular**: um curso fixo pode ter um instrutor titular pré-definido, priorizado sempre que disponível.

Depois de gerada, a escala pode ser ajustada manualmente sessão a sessão e exportada em CSV.

## Rodando localmente

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Acesse http://localhost:5000. O banco (SQLite) é criado automaticamente em `instance/escala.db`.

## Fluxo de uso

1. Cadastre os **instrutores** (nome, qualificações, disponibilidade, bloqueios) — manualmente ou importando uma planilha.
2. Cadastre os **cursos fixos** e **cursos livres**.
3. No painel, escolha um período e clique em **Gerar escala** — os cursos fixos do período entram automaticamente.
4. Na tela da escala, use **Anexar curso livre** para incluir os cursos livres cadastrados que fazem parte dessa escala.
5. Revise a escala: sessões sem instrutor elegível ficam marcadas em vermelho e podem ser atribuídas manualmente.
6. Exporte a escala em CSV se necessário.

## Importação de dados (ex: a partir do SIGOP)

A tela **Importar** aceita planilhas CSV ou Excel para instrutores, cursos fixos e cursos livres. Os modelos
de coluna esperados estão em `data/exemplo_instrutores.csv`, `data/exemplo_cursos_fixos.csv` e
`data/exemplo_cursos_livres.csv` (também disponíveis para download na própria tela de importação).

Hoje a integração é via planilha porque não foi confirmada uma API pública para o SIGOP usado pela empresa
(`sigop.sestsenat.org.br`). Se uma API ou acesso ao banco de dados do SIGOP for viabilizado futuramente,
a importação pode ser adaptada para buscar os dados diretamente, sem mudar o restante do sistema — o motor
de geração de escala (`app/scheduler.py`) e os modelos (`app/models.py`) já são independentes da origem dos dados.

## Estrutura do projeto

```
app/
  models.py         modelos de dados (instrutor, curso fixo, curso livre, escala, sessão)
  scheduler.py       motor de geração de escala
  import_data.py    importação de planilhas CSV/Excel
  routes/            rotas Flask (dashboard, instrutores, cursos, escala, importar)
  templates/          páginas HTML
data/                 planilhas de exemplo para importação
run.py                ponto de entrada da aplicação
```
