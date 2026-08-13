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
