# Escala de Instrutores — versão standalone

Versão do sistema em um único arquivo HTML (`index.html`), sem backend. Roda inteiramente no
navegador — não precisa instalar Python, Flask, nem rodar servidor nenhum.

## Como usar

1. Baixe o arquivo `index.html`.
2. Abra ele diretamente no navegador (duplo clique, ou arraste para uma aba).
3. Pronto — o sistema já está funcionando.

Na tela **Importar**, o botão **"Carregar dados de exemplo"** popula alguns instrutores e cursos de
exemplo para você já ver o sistema funcionando sem precisar cadastrar nada na mão.

## Onde ficam os dados

Tudo é salvo no `localStorage` do navegador, neste dispositivo. Isso significa:

- Os dados **não são compartilhados** entre computadores ou entre navegadores diferentes.
- Limpar o cache/dados do navegador apaga tudo (use **Exportar CSV** nas escalas geradas para guardar
  uma cópia externa).
- Não há problema em manter várias abas abertas com o mesmo arquivo — todas leem/escrevem o mesmo
  `localStorage`, desde que sejam abertas a partir do mesmo caminho de arquivo.

Se precisar de um sistema com banco de dados compartilhado entre a equipe, importação de CSV/Excel mais
robusta e histórico centralizado, use a **aplicação web (Flask)** na raiz do repositório.

## Funcionalidades

As mesmas da aplicação web, com a mesma lógica de alocação de instrutor (qualificação, disponibilidade,
bloqueios, conflito de horário, balanceamento de carga, instrutor titular em curso fixo):

- Cadastro de instrutores (qualificações, disponibilidade semanal, bloqueios)
- Cadastro de cursos fixos e cursos livres
- Geração de escala (cursos fixos entram automaticamente pelo período)
- Anexar cursos livres cadastrados a uma escala, pelo botão na tela da escala
- Reatribuição manual de instrutor por sessão
- Exportação da escala em CSV
- Importação de instrutores/cursos por arquivo CSV (mesmas colunas da app web — veja `data/exemplo_*.csv`
  na raiz do repositório, ou baixe os modelos direto na tela de Importar)

## Limitação conhecida

A importação aqui aceita apenas **CSV** (não Excel/.xlsx), diferente da app web que aceita os dois formatos.
