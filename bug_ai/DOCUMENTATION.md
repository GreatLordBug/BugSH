# BugAI documentation

This directory contains the local text-generation layer used by the shell. It is a lightweight, corpus-driven model built around a single text file, `source.txt`, and a small Python implementation in `model.py`.

## Purpose

The model is not a neural network in the modern ML sense. It is a small n-gram-style generator that:

- reads a source corpus from `source.txt`
- tokenizes the text into words and punctuation
- builds a simple lookup map of token transitions
- uses prompt similarity to pick a relevant seed sentence
- generates a short response by continuing that text

This is used by the shell commands `ai` and `aichat` in `main.py`.

## Files

### `source.txt`

This is the corpus for the model. It contains a long sequence of lyrical, depressive, and introspective prose fragments. It is intentionally stylized and highly repetitive in tone.

The text is used as a raw source of language patterns. The model does not parse or interpret it semantically; it only reads it as text and learns token-to-token transitions.

### `model.py`

This file defines the classes used to read, tokenize, and generate responses.

## Classes

### `BugAIModel`

The main model class.

#### Initialization

`__init__(self, source_path=None)`

- resolves the corpus file location
- defaults to `bug_ai/source.txt` when no explicit path is provided
- supports relative paths by checking the working directory and project-relative locations
- reads the corpus into memory and builds the internal lookup structures

State created during initialization:

- `self.source_path`: resolved path to the corpus
- `self.corpus`: raw text contents
- `self.sentences`: list of sentence-like chunks
- `self.tokens`: tokenized corpus
- `self.ngram_map`: transition map used for generation

#### Reading the corpus

`_read_corpus(self)`

- checks whether the source file exists
- returns the file contents as a UTF-8 string if found
- otherwise returns an empty string

#### Tokenization

`_tokenize(self, text)`

Uses a regex to split the text into:

- letter/digit/apostrophe sequences
- punctuation such as `.`, `,`, `!`, `?`, `;`, `:`

The output is lowercased, so generation is case-insensitive.

#### Sentence splitting

`_split_sentences(self, text)`

- splits on whitespace following terminal punctuation (`.`, `!`, `?`)
- strips surrounding spaces
- drops empty fragments

This creates a list of sentence chunks used to anchor responses.

#### Building the n-gram map

`_build_ngram_map(self)`

This builds a simple transition table from adjacent tokens.

The logic is effectively:

- look at pairs of tokens at a time
- store the last token of each pair as a possible continuation of the previous token(s)

In practice, it creates a dictionary where the key is a token tuple and the value is a list of tokens that often follow it.

This is a minimal statistical language model rather than a large transformer model.

## Response generation flow

### `_pick_relevant_sentence(prompt)`

This method measures overlap between the prompt tokens and each sentence in the corpus.

- tokenizes the incoming prompt
- computes common tokens between the prompt and each sentence
- selects the sentence with the strongest overlap
- falls back to a random sentence if no matches are found
- falls back to a static phrase if there is no corpus data

This lets the model choose a seed sentence that resembles the user’s input.

### `_next_token(tokens)`

Given a current generated token list, this tries to predict the next token.

Behavior:

- if there are at least two tokens, it checks a shortcut based on the last two tokens
- if that fails, it checks the last token by itself
- if no match is found, it returns `None`

This is a very small context-based prediction function.

### `_seed_tokens(prompt)`

This prepares the initial generation context.

- tokenizes the prompt
- keeps the first 8 tokens if available
- otherwise selects a relevant sentence and uses its first 8 tokens

These tokens become the starting point for generation.

## `ask()` method

`ask(self, prompt, max_tokens=30, history=None)`

This is the core generation function.

Execution steps:

1. If the corpus is empty, it returns: `No source data was found.`
2. Normalizes the prompt into a string
3. If a history list is supplied, it uses the last few entries to build context
4. Builds the seed from the prompt or a relevant sentence
5. Repeatedly appends predicted next tokens until:
   - `max_tokens` is reached
   - the model runs out of continuation options
   - a sentence-ending punctuation mark appears and the response is already long enough
6. Joins the generated tokens into a string
7. Removes duplicated prompt prefix if needed
8. Falls back to a relevant sentence if the generated text is empty
9. Truncates output to 240 characters

This means the model generates short, stylized continuations rather than long coherent prose.

## Conversation handling

### `BugAIConversation`

This wrapper maintains a conversation history list.

#### Initialization

`__init__(self, model)`

- stores a model instance
- creates an empty `self.history`

#### `ask(self, prompt)`

This method:

- trims and normalizes the incoming text
- rejects empty input with: `I am waiting for your next thought.`
- appends the prompt to `self.history`
- calls `self.model.ask(clean_prompt, history=self.history)`
- appends the assistant response to the history
- returns the generated reply

The conversation memory is shallow: it only looks at the last four history items when building context.

## How it behaves in the shell

The shell uses this model through the commands:

- `ai <prompt>`: asks the model a single prompt
- `aichat` or `chat`: starts a conversation loop with `BugAIConversation`

The prompt is sent to the model, and the model produces a short generated response based on the source corpus and recent chat history.

## Strengths and limitations

### Strengths

- very lightweight
- easy to understand and modify
- no external dependencies
- effective for short, stylized, repetitive text generation

### Limitations

- it is not a real semantic AI model
- it does not understand the meaning of the prompt deeply
- it relies on surface token overlap and local text patterns
- it can repeat phrases from the corpus and produce strongly stylized outputs
- it is sensitive to the exact words in `source.txt`

## Summary

`bug_ai/model.py` implements a compact n-gram-style text generator, and `bug_ai/source.txt` supplies the corpus from which it builds its output. The model is intentionally simple, deterministic in its structure, and strongly shaped by the repeated tone and wording of the source text. It behaves more like a local text engine than a modern conversational model.
