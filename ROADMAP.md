# Roadmap de otimização

## Incluído na versão 0.5

- Seleção múltipla, revisão em lote e uma confirmação de exclusão.
- Resumo de espaço total, usado e livre por unidade.
- Acesso às ferramentas oficiais de armazenamento, inicialização, processos e otimização de unidades do Windows.
- Desinstalação pelo mecanismo oficial de aplicativos desktop.
- Remoção de pacotes Windows removíveis para o usuário atual.
- Proteção de pacotes de sistema, frameworks, recursos e Microsoft Store.
- Revisão separada de pastas residuais, bloqueada enquanto o app ainda estiver registrado.
- Aba de funções com atalhos oficiais e indicação de benefício e risco.
- Interface escura nativa com métricas, estados visuais e rolagem completa.
- Busca e filtros no inventário de aplicativos.
- Aviso explícito quando a lista de apps Windows fica parcial.
- Proteção contra caminhos que chegam a áreas críticas por junções.
- Exclusão de arquivos em segundo plano para manter a janela responsiva.
- Atalhos `Ctrl+F` e `F5`.

## Próxima versão

1. Localizar arquivos grandes e antigos com filtros claros.
2. Detectar duplicados primeiro por tamanho e depois por hash.
3. Medir espaço recuperável por categoria antes de qualquer ação.
4. Criar diário de operações para auditoria e desfazer ações compatíveis.
5. Detectar resíduos adicionais fora da pasta oficial com confiança verificável.
6. Paginar pastas com centenas de milhares de entradas.

## Novas ideias priorizadas

- **Mapa de espaço:** treemap local para localizar áreas grandes sem abrir pasta por pasta.
- **Receitas seguras:** caches conhecidos, miniaturas, relatórios de falha e instaladores antigos.
- **Duplicados em duas etapas:** tamanho primeiro; hash somente nos candidatos.
- **Impacto de inicialização:** combinar estado, publicador e impacto medido pelo Windows.
- **Histórico de limpeza:** data, caminho, tamanho, resultado e motivo da classificação.
- **Ponto de restauração:** oferecer antes de mudanças de alto impacto suportadas pelo Windows.
- **Saúde de discos:** SMART, TRIM, temperatura e alerta de pouco espaço.
- **Modo jogo ou trabalho:** apenas recomendações reversíveis de energia, captura e inicialização.
- **Comparação temporal:** mostrar quais pastas cresceram desde a última análise.
- **Exportar relatório:** resumo local em JSON ou CSV, sem enviar nomes para serviços externos.

## Armazenamento

- Limpar caches conhecidos por aplicativo, com impacto e custo de regeneração.
- Revisar Downloads, instaladores antigos, relatórios de falha e miniaturas.
- Integrar a limpeza suportada pelo Windows para atualizações e componentes.
- Mostrar crescimento de pastas ao longo do tempo, não apenas tamanho atual.
- Identificar projetos abandonados, ambientes virtuais e artefatos de compilação.
- Detectar arquivos sincronizados que podem voltar ao modo somente online.

## Desempenho

- Revisar programas de inicialização e medir o impacto informado pelo Windows.
- Mostrar processos com uso persistente de CPU, memória, disco e rede.
- Revisar serviços e tarefas agendadas de terceiros sem desativação automática.
- Verificar saúde, temperatura, espaço livre e suporte a TRIM dos discos.
- Sugerir ajustes de energia conforme desktop, notebook ou jogo.
- Relacionar lentidão com pressão de memória, paginação e disco cheio.

## Regras do produto

- Medir antes e depois de cada otimização.
- Usar mecanismos oficiais do Windows sempre que existirem.
- Explicar impacto, risco e reversibilidade antes de executar.
- Nunca oferecer limpeza de Registro, limpador de RAM ou desativação automática de serviços.
- Nunca desfragmentar SSD como recomendação genérica.

## Avaliação de necessidade

- **Necessário depois:** arquivos grandes, duplicados, espaço recuperável e resíduos de aplicativos.
- **Útil depois:** crescimento de pastas, monitoramento persistente e histórico de operações.
- **Adiado por risco:** limpeza automática de Registro e desativação automática de serviços.
- **Dispensável agora:** quarentena, porque mantém o espaço ocupado e conflita com a limpeza imediata.
