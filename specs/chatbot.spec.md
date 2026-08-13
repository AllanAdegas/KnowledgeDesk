# Spec: Chatbot com histórico

## Comportamentos esperados

### Sessões
- DADO um novo usuário
  QUANDO inicia uma conversa
  ENTÃO uma session_id é gerada e retornada
  E o histórico começa vazio

- DADO uma session_id existente
  QUANDO o usuário envia uma mensagem
  ENTÃO o histórico dos últimos 10 turnos é incluído no contexto
  E a resposta leva em conta mensagens anteriores

- DADO uma session com mais de 10 turnos
  QUANDO nova mensagem é enviada
  ENTÃO apenas os 10 turnos mais recentes são enviados ao modelo
        (janela deslizante — evita estourar context window)

### Streaming
- DADO uma mensagem enviada
  QUANDO o modelo começa a responder
  ENTÃO os tokens chegam via SSE (text/event-stream) em tempo real
  E o evento final é { type: "done", session_id }

### Modo RAG + Chat
- DADO documentos indexados e RAG ativado na sessão
  QUANDO o usuário pergunta algo presente nos documentos
  ENTÃO a resposta usa os documentos como contexto
  E cita a fonte no final da resposta
