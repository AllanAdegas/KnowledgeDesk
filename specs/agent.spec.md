# Spec: Sistema Agêntico

## Comportamentos esperados

### Execução de tarefas
- DADO uma tarefa ambígua ("analise os contratos")
  QUANDO submetida ao agente
  ENTÃO o agente pede clarificação antes de executar

- DADO a tarefa "liste todos os documentos sobre RH"
  QUANDO executada
  ENTÃO o agente usa a tool list_docs, filtra por relevância
        e retorna lista formatada com nome e resumo de cada documento

- DADO a tarefa "resuma o documento X e extraia os pontos principais"
  QUANDO executada
  ENTÃO o agente usa search_docs para recuperar o conteúdo,
        usa summarize para gerar o resumo
        e retorna estruturado em tópicos

### Limites do agente
- DADO qualquer tarefa
  QUANDO o agente não consegue completar em 5 iterações
  ENTÃO para e retorna o progresso parcial com explicação

- DADO uma tarefa que pede ação destrutiva ("delete os documentos")
  QUANDO submetida
  ENTÃO o agente recusa e explica que só tem permissão de leitura
