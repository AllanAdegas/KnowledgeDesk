# Spec: Fine-tuning (V2 — NÃO IMPLEMENTADO NESTA RODADA)

> Este módulo está documentado para referência futura. A implementação foi adiada
> para uma V2 porque o treino LoRA via Unsloth exige GPU NVIDIA/CUDA, indisponível
> no ambiente de desenvolvimento atual (Mac). Nenhum código em backend/finetune/
> foi criado nesta rodada.

## Comportamentos esperados

### Preparação de dataset
- DADO um conjunto de pares pergunta/resposta em CSV
  QUANDO prepare_dataset.py é executado
  ENTÃO gera arquivo JSONL no formato instruction/input/output
  E valida que nenhum exemplo tem output vazio

### Treino
- DADO dataset JSONL válido e modelo base definido
  QUANDO train.py é executado
  ENTÃO treina com LoRA (r=16, alpha=32)
  E salva checkpoints a cada 100 steps
  E loga loss no terminal em tempo real

### Exportação
- DADO modelo treinado
  QUANDO export.py é executado
  ENTÃO gera arquivo .gguf quantizado em Q4_K_M
  E gera Modelfile compatível com `ollama create`
  E imprime comando exato para registrar no Ollama
