import random
import re
from pathlib import Path


class BugAIModel:
    def __init__(self, source_path=None):
        base_dir = Path(__file__).resolve().parent
        if source_path is None:
            source_path = base_dir / "source.txt"
        else:
            source_path = Path(source_path)
            if not source_path.is_absolute():
                candidates = [Path.cwd() / source_path, base_dir / source_path, base_dir.parent / source_path]
                for candidate in candidates:
                    if candidate.exists():
                        source_path = candidate
                        break
                else:
                    source_path = candidates[0]
        self.source_path = source_path.resolve()
        self.corpus = self._read_corpus()
        self.sentences = self._split_sentences(self.corpus)
        self.tokens = self._tokenize(self.corpus)
        self.ngram_map = self._build_ngram_map()

    def _read_corpus(self):
        if not self.source_path.exists():
            return ""
        return self.source_path.read_text(encoding="utf-8", errors="ignore")

    def _tokenize(self, text):
        if not text:
            return []
        return re.findall(r"[A-Za-z0-9']+|[.,!?;:]", text.lower())

    def _split_sentences(self, text):
        if not text:
            return []
        parts = re.split(r"(?<=[.!?])\s+", text.strip())
        return [piece.strip() for piece in parts if piece.strip()]

    def _build_ngram_map(self):
        mapping = {}
        for index in range(len(self.tokens) - 1):
            key = tuple(self.tokens[index:index + 2])
            mapping.setdefault(key[0:-1], []).append(key[-1])
        return mapping

    def _pick_relevant_sentence(self, prompt):
        prompt_tokens = set(self._tokenize(prompt))
        if not prompt_tokens:
            return random.choice(self.sentences) if self.sentences else "The room is quiet and waiting."
        scored = []
        for sentence in self.sentences:
            score = len(set(self._tokenize(sentence)) & prompt_tokens)
            if score:
                scored.append((score, sentence))
        if scored:
            return max(scored, key=lambda item: item[0])[1]
        return random.choice(self.sentences) if self.sentences else "The room is quiet and waiting."

    def _next_token(self, tokens):
        if len(tokens) >= 2:
            key = tuple(tokens[-2:])
            options = self.ngram_map.get(key[:-1], [])
            if options:
                return random.choice(options)
        if tokens:
            key = (tokens[-1],)
            options = self.ngram_map.get(key, [])
            if options:
                return random.choice(options)
        return None

    def _seed_tokens(self, prompt):
        prompt_tokens = self._tokenize(prompt)
        if prompt_tokens:
            return prompt_tokens[:8]
        sentence = self._pick_relevant_sentence(prompt)
        return self._tokenize(sentence)[:8]

    def ask(self, prompt, max_tokens=30, history=None):
        if not self.corpus:
            return "No source data was found."
        context = prompt.strip() if prompt and prompt.strip() else ""
        if history:
            recent = history[-4:]
            context = " ".join(item["content"] for item in recent if item.get("content"))
        if not context:
            context = self._pick_relevant_sentence("")
        seed = self._seed_tokens(context)
        output = list(seed)
        for _ in range(max_tokens):
            next_token = self._next_token(output)
            if next_token is None:
                break
            output.append(next_token)
            if next_token in {".", "!", "?"} and len(output) > 6:
                break
        generated = " ".join(output).strip()
        if generated.lower().startswith(context.lower()):
            generated = generated[len(context):].strip()
        if not generated:
            generated = self._pick_relevant_sentence(context)
        return generated[:240]


class BugAIConversation:
    def __init__(self, model):
        self.model = model
        self.history = []

    def ask(self, prompt):
        clean_prompt = " ".join(str(prompt).strip().split())
        if not clean_prompt:
            return "I am waiting for your next thought."
        self.history.append({"role": "user", "content": clean_prompt})
        response = self.model.ask(clean_prompt, history=self.history)
        self.history.append({"role": "assistant", "content": response})
        return response
