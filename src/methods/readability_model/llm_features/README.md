# Local language-model features

This module measures predictability of source text and AST-tagged spans using a
local causal language model. It produces the `llm__` feature family and is
independent of direct API prompting. Generation is run through the method's
LLM feature runner; fitted readability models consume saved feature tables.
