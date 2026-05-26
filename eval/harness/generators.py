"""Pluggable generation backend. The harness orchestrator depends on the
Generator interface; subclasses implement actual generation.

Four backends exist:

  StubGenerator: returns a pre-saved output from disk. Errors if the file
  isn't there. Useful for validating the scoring pipeline against
  hand-written examples before any API call.

  AnthropicGenerator: calls the Anthropic Messages API. The system prompt
  is whatever the caller passes (so the harness can pass SKILL.md contents
  for treated runs and an empty system prompt for baseline). Lazy-imports
  the SDK so the harness runs without it installed.

  ClaudeCLIGenerator: shells out to `claude -p` (headless Claude Code).
  Uses the user's existing Claude Code auth (OAuth or API key) — no
  ANTHROPIC_API_KEY required if you're logged in via /login. Each call
  spawns a fresh process, so no cross-prompt context contamination.

  EchoGenerator: returns the prompt itself. Only useful for plumbing tests.

To add another backend (OpenAI, local server, etc.), subclass Generator
and register it in _BACKENDS.
"""

from __future__ import annotations
import os
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path


class Generator(ABC):
    """A generator takes a prompt + optional system prompt, returns text."""

    @abstractmethod
    def generate(self, prompt: str, system: str = "") -> str: ...

    @property
    def name(self) -> str:
        return self.__class__.__name__


class EchoGenerator(Generator):
    def generate(self, prompt: str, system: str = "") -> str:
        return prompt


class StubGenerator(Generator):
    """Reads outputs from a directory. Filename = {prompt_id}.txt.

    Errors if the file is missing — this is intentional, it forces the
    user to either hand-write a sample or wire up a real generator
    before they can run the harness.
    """

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self._current_id: str | None = None

    def set_current_id(self, prompt_id: str) -> None:
        """The harness calls this before generate(). Keeps the Generator
        interface uniform across stub and real backends."""
        self._current_id = prompt_id

    def generate(self, prompt: str, system: str = "") -> str:
        if self._current_id is None:
            raise RuntimeError("StubGenerator: set_current_id() must be called first")
        path = self.output_dir / f"{self._current_id}.txt"
        if not path.exists():
            raise FileNotFoundError(
                f"StubGenerator: no saved output at {path}. "
                f"Either hand-write one or use a real generator (--backend anthropic or claude_cli)."
            )
        return path.read_text()


class AnthropicGenerator(Generator):
    """Calls the Anthropic Messages API. Lazy-imports the SDK."""

    def __init__(
        self,
        model: str = "claude-opus-4-7",
        max_tokens: int = 4096,
        temperature: float = 1.0,
    ):
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from anthropic import Anthropic
            except ImportError as e:
                raise RuntimeError(
                    "AnthropicGenerator requires the `anthropic` package. "
                    "Install with: pip install anthropic"
                ) from e
            if not os.environ.get("ANTHROPIC_API_KEY"):
                raise RuntimeError(
                    "AnthropicGenerator requires ANTHROPIC_API_KEY in environment."
                )
            self._client = Anthropic()
        return self._client

    def generate(self, prompt: str, system: str = "") -> str:
        client = self._get_client()
        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        msg = client.messages.create(**kwargs)
        # Concatenate any text blocks in the response.
        parts = [b.text for b in msg.content if getattr(b, "type", None) == "text"]
        return "".join(parts)


class ClaudeCLIGenerator(Generator):
    """Shells out to the local `claude` CLI in headless mode (claude -p).

    Uses your existing Claude Code auth, so no ANTHROPIC_API_KEY is needed
    if you're logged in via `/login`. Each call is a fresh process; no
    cross-prompt context bleed.

    By default, passes the system prompt via --system-prompt (replace),
    which strips out Claude Code's default harness instructions and gives
    behavior close to a raw API call. Pass append=True to use
    --append-system-prompt instead, which keeps Claude Code's defaults and
    adds SKILL.md on top — closer to "deployed as a Claude Code skill".
    """

    def __init__(
        self,
        model: str | None = None,
        append: bool = False,
        timeout_s: int = 600,
        executable: str = "claude",
    ):
        self.model = model
        self.append = append
        self.timeout_s = timeout_s
        self.executable = executable

    def generate(self, prompt: str, system: str = "") -> str:
        cmd = [self.executable, "-p", "--output-format", "text"]
        if self.model:
            cmd.extend(["--model", self.model])
        flag = "--append-system-prompt" if self.append else "--system-prompt"
        cmd.extend([flag, system])
        cmd.append(prompt)
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"claude CLI timed out after {self.timeout_s}s") from e
        except FileNotFoundError as e:
            raise RuntimeError(
                f"`{self.executable}` not found on PATH. Install Claude Code, or set --claude-bin."
            ) from e
        if result.returncode != 0:
            stderr = result.stderr.strip()[:500]
            raise RuntimeError(f"claude CLI exited {result.returncode}: {stderr}")
        return result.stdout


_BACKENDS: dict[str, type[Generator]] = {
    "stub": StubGenerator,
    "echo": EchoGenerator,
    "anthropic": AnthropicGenerator,
    "claude_cli": ClaudeCLIGenerator,
}


def get_backend(name: str, **kwargs) -> Generator:
    if name not in _BACKENDS:
        raise ValueError(f"Unknown backend '{name}'. Known: {list(_BACKENDS)}")
    return _BACKENDS[name](**kwargs)
