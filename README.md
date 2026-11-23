# Optimizer

Aplicativo desktop para entender e recuperar armazenamento no Windows sem apagar arquivos às cegas.

## MVP atual

- Interface nativa redesenhada, com tema escuro, hierarquia clara e tabelas responsivas.
- Exibe discos, pastas e arquivos em uma árvore carregada sob demanda.
- Mostra tamanho, importância estimada e motivo da classificação.
- Continua navegando quando encontra pastas sem permissão.
- Permite selecionar e revisar vários arquivos antes de qualquer ação.
- Exclui o lote após uma única confirmação `Sim/Não`.
- Bloqueia pastas, links e áreas críticas.
- Lista aplicativos desktop e pacotes do Windows para o usuário atual.
- Busca aplicativos por nome, publicador, versão ou pasta.
- Filtra aplicativos removíveis, protegidos, desktop, Windows e resíduos.
- Informa quando o inventário do Windows ficou parcial por erro do sistema.
- Executa o desinstalador oficial dos aplicativos desktop após uma confirmação.
- Remove pacotes Windows somente quando o sistema os marca como removíveis.
- Exibe componentes protegidos, mas mantém a ação de remoção bloqueada.
- Revisa e exclui a pasta residual de um app desktop somente depois que ele deixa de estar registrado.
- Mostra espaço total, usado e livre por unidade.
- Abre armazenamento, inicialização, Gerenciador de Tarefas e otimização de unidades do Windows.
- Oferece uma aba de funções com ajustes oficiais de inicialização, jogos, efeitos visuais, diagnóstico, notificações e recursos opcionais.
- Mostra capacidade, uso e espaço livre consolidados.
- Atalhos: `Ctrl+F` abre a busca de aplicativos; `F5` atualiza a aba atual.

## Classificação

- **Crítico:** Windows, programas instalados e componentes do sistema.
- **Alto:** documentos pessoais, mídia, instaladores e executáveis.
- **Médio:** configurações, bancos locais e dados com finalidade provável.
- **Baixo:** caches e temporários fora de áreas protegidas.
- **Revisar:** origem ou impacto não identificado.

Classificação é uma estimativa. `Baixo` não significa autorização automática para excluir. A exclusão em lote é permanente.
O destino real do arquivo é resolvido antes da classificação, inclusive quando o caminho passa por uma junção.

## Executar pelo código

Requer Windows e Python 3.12 ou superior.

```powershell
python -m optimizer
```

## Testar

```powershell
python -m unittest discover -s tests -v
```

## Gerar executável

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --name Optimizer main.py
```

O executável será criado em `dist\Optimizer.exe`.

## Próximas etapas

1. Localizar arquivos grandes e antigos com filtros.
2. Detectar duplicados por hash em duas etapas.
3. Relacionar resíduos fora da pasta de instalação ao aplicativo proprietário.
4. Criar diário de operações e pontos de restauração quando suportados.
5. Adicionar assinatura de código e instalador do Windows.

Veja [ROADMAP.md](ROADMAP.md) para ideias de otimização priorizadas.

## Segurança e privacidade

O processamento ocorre localmente. O projeto não envia nomes ou conteúdo de arquivos para serviços externos. Pastas de pacotes em `WindowsApps` nunca são excluídas diretamente. O Optimizer não desativa serviços críticos, não limpa o Registro e não remove componentes protegidos.

