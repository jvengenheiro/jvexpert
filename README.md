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

Existem duas formas de usar o sistema — escolha a que fizer mais sentido para você:

- **App web (Flask + SQLite)**: pensada para uso contínuo pela equipe, com importação de CSV/Excel e um
  banco de dados compartilhável. Requer instalar Python e rodar um servidor (veja abaixo).
- **Versão standalone (`standalone/index.html`)**: um único arquivo HTML que roda 100% no navegador, sem
  instalar nada — basta abrir o arquivo. Os dados ficam salvos localmente no navegador (localStorage). Ótima
  para testar rapidamente ou usar em uma máquina sem Python. Veja `standalone/README.md`.

## Rodando localmente (app web)

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

A tela **Importar** aceita arquivos **CSV, Excel (.xlsx/.xls), Word (.docx) ou PDF** para instrutores,
cursos fixos e cursos livres — pensada para receber qualquer exportação que você conseguir tirar do SIGOP,
sem precisar bater exatamente as colunas:

- **Cabeçalhos não precisam ser exatos**: o sistema reconhece variações comuns de nome de coluna (ex:
  "Nome do Curso", "Curso" e "Descrição" mapeiam todos para o campo `nome`; veja a lista de sinônimos em
  `CAMPO_SINONIMOS`, em `app/import_data.py`).
- **Detecção automática do tipo**: por padrão, a tela tenta identificar sozinha se o arquivo é uma lista de
  instrutores, cursos fixos ou cursos livres, com base em quais colunas foram reconhecidas. Se não conseguir
  (colunas ambíguas ou não reconhecidas), pede para você escolher manualmente.
- **PDF e Word**: só são lidos quando o arquivo tem uma **tabela de verdade** (células, não texto corrido) —
  funciona bem com relatórios/exportações tabulares, não com documentos escaneados ou em prosa.

Os modelos de coluna (em CSV) estão em `data/exemplo_instrutores.csv`, `data/exemplo_cursos_fixos.csv` e
`data/exemplo_cursos_livres.csv` (também disponíveis para download na própria tela de importação) — as mesmas
colunas (com nomes parecidos) funcionam nos outros formatos.

Essa importação por arquivo existe porque não foi confirmada uma API pública para o SIGOP usado pela empresa
(`sigop.sestsenat.org.br`). Se uma API ou acesso ao banco de dados do SIGOP for viabilizado futuramente, dá
para adaptar para buscar os dados diretamente, sem mudar o restante do sistema — o motor de geração de escala
(`app/scheduler.py`) e os modelos (`app/models.py`) já são independentes da origem dos dados.

> A versão standalone (`standalone/index.html`) só aceita **CSV** na importação — processar Excel/Word/PDF
> direto no navegador, sem backend, exigiria embutir bibliotecas pesadas no arquivo único.

## Estrutura do projeto

```
app/
  models.py         modelos de dados (instrutor, curso fixo, curso livre, escala, sessão)
  scheduler.py       motor de geração de escala
  import_data.py    importação de CSV/Excel/Word/PDF (mapeamento de colunas + detecção automática de tipo)
  routes/            rotas Flask (dashboard, instrutores, cursos, escala, importar)
  templates/          páginas HTML
data/                 planilhas de exemplo para importação
run.py                ponto de entrada da aplicação
standalone/           versão em arquivo HTML único (sem servidor, dados no navegador)
```
