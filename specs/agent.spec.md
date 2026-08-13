# Spec: Sistema Agêntico

## Comportamentos esperados

### Classificação de intenção
- DADO uma tarefa de listagem, expressa de formas variadas
      ("liste os documentos", "mostra os documentos que eu tenho",
      "quais arquivos estão indexados?", "list files")
  QUANDO submetida ao agente
  ENTÃO o agente classifica como `list` e usa a tool `list_docs`

- DADO uma tarefa de resumo, expressa de formas variadas
      ("resuma o contrato da Acme", "quero um resumo do sample.pdf",
      "extraia os pontos principais do documento de RH")
  QUANDO submetida ao agente
  ENTÃO o agente classifica como `summarize`, extrai o documento-alvo
        mencionado (quando houver) e usa `search_docs` + `summarize`

- DADO uma tarefa destrutiva, expressa de formas variadas
      ("apaga tudo", "delete os documentos", "remova o contrato X",
      "exclua os arquivos indexados")
  QUANDO submetida ao agente
  ENTÃO o agente classifica como `destructive` e recusa a execução

- DADO qualquer tarefa
  QUANDO submetida ao agente
  ENTÃO a classificação é feita de forma híbrida: primeiro uma chamada
        ao LLM local (`OllamaClient.chat`, `stream=False`) pedindo um JSON
        estruturado `{"category": ..., "target_hint": ...}`; se essa
        resposta não vier, não for um JSON válido, ou trouxer uma
        categoria fora do enum esperado (`destructive`, `list`,
        `summarize`, `ambiguous`), o agente cai automaticamente para a
        classificação determinística por palavra-chave já existente
        (mesmo comportamento testável e sem chamadas reais ao modelo
        local nos testes automatizados, que mockam `ollama_client.chat`)

### Extração de documento-alvo
- DADO uma tarefa que menciona um documento por nome ou apelido
      ("resuma o contrato da Acme")
  QUANDO o LLM extrai um `target_hint` ("contrato da Acme")
  ENTÃO o agente tenta resolver esse texto livre contra os `filename`s
        dos documentos indexados (substring nos dois sentidos,
        case-insensitive, mais tolerância a erro de digitação via
        correspondência aproximada)

- DADO um `target_hint` que corresponde a exatamente um documento indexado
  QUANDO a resolução ocorre
  ENTÃO a busca vetorial subsequente (`search_docs`) é filtrada para
        considerar apenas os chunks daquele documento

- DADO um `target_hint` que não corresponde a nenhum documento indexado
      (ou corresponde a mais de um, de forma ambígua)
  QUANDO a resolução falha
  ENTÃO o agente pede clarificação citando o hint informado e listando
        os documentos disponíveis, em vez de prosseguir com uma busca
        no corpus inteiro por engano

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
