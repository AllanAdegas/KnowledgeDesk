# Spec: RAG (Retrieval-Augmented Generation)

## Comportamentos esperados

### Ingestão de documentos
- DADO um arquivo PDF válido
  QUANDO o usuário faz upload
  ENTÃO o sistema extrai o texto, divide em chunks de ~500 tokens com overlap de 50,
        gera embeddings com nomic-embed-text e salva no ChromaDB
  E retorna { id, filename, chunks_count, status: "indexed" }

- DADO um arquivo com formato não suportado (.exe, .jpg)
  QUANDO o usuário faz upload
  ENTÃO retorna erro 422 com mensagem clara

- DADO um PDF corrompido
  QUANDO o usuário faz upload
  ENTÃO retorna erro 400 com mensagem "Não foi possível extrair texto do documento"

### Resumo pós-indexação
- DADO um documento indexado com sucesso
  QUANDO a ingestão termina
  ENTÃO o sistema gera um resumo do texto completo extraído, em um único
        parágrafo de texto corrido (sem títulos/tópicos/marcadores — esse
        formato estruturado é reservado para a tool `summarize` do agente,
        não para este resumo de documento) e o inclui na resposta do
        upload como campo `summary`

- DADO um documento cujo texto extraído excede `rag_summary_max_chars`
      (6000 caracteres por padrão)
  QUANDO o resumo é gerado
  ENTÃO apenas os primeiros `rag_summary_max_chars` caracteres do texto
        extraído são enviados ao LLM, para não estourar a janela de
        contexto do modelo local

- DADO um documento já indexado, com resumo gerado na ingestão
  QUANDO o cliente consulta GET /api/documents
  ENTÃO o resumo aparece junto com `filename` e `chunks_count`, pois é
        persistido na metadata de cada chunk (mesmo padrão já usado para
        `filename`), não apenas devolvido na resposta do upload

### Query RAG
- DADO documentos indexados
  QUANDO o usuário envia uma pergunta
  ENTÃO o sistema busca os 5 chunks mais relevantes,
        injeta no prompt e retorna resposta do LLM com as fontes citadas

- DADO uma pergunta sobre assunto não presente nos documentos
  QUANDO o usuário pergunta
  ENTÃO o sistema responde "Não encontrei informações sobre isso nos documentos disponíveis"
        e NÃO inventa informações

- DADO uma pergunta
  QUANDO a busca vetorial retorna chunks com score < 0.3
  ENTÃO o sistema considera como "não encontrado"
