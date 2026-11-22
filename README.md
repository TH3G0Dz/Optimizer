# Optimizer

Aplicativo desktop para entender e recuperar armazenamento no Windows sem apagar arquivos às cegas.

## MVP atual

- Exibe discos, pastas e arquivos em uma árvore carregada sob demanda.
- Mostra tamanho, importância estimada e motivo da classificação.
- Continua navegando quando encontra pastas sem permissão.
- Revisa um arquivo selecionado antes de qualquer ação.
- Exclui arquivos aprovados após exigir o nome exato como confirmação.
- Bloqueia pastas, links e áreas críticas.
- Lista aplicativos registrados no Windows.
- Abre a tela oficial de desinstalação do Windows.
- Não remove pastas nem resíduos nesta versão.

## Classificação

- **Crítico:** Windows, programas instalados e componentes do sistema.
- **Alto:** documentos pessoais, mídia, instaladores e executáveis.
- **Médio:** configurações, bancos locais e dados com finalidade provável.
- **Baixo:** caches e temporários fora de áreas protegidas.
- **Revisar:** origem ou impacto não identificado.

Classificação é uma estimativa. `Baixo` não significa autorização automática para excluir. A exclusão é permanente.

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

1. Medir espaço recuperável sem excluir conteúdo.
2. Relacionar resíduos ao aplicativo proprietário com níveis de confiança.
3. Criar quarentena restaurável e diário de operações.
4. Desinstalar pelo mecanismo oficial antes de oferecer resíduos.
5. Adicionar assinatura de código e instalador do Windows.

Veja [ROADMAP.md](ROADMAP.md) para ideias de otimização priorizadas.

## Segurança e privacidade

O processamento ocorre localmente. O projeto não envia nomes ou conteúdo de arquivos para serviços externos.

