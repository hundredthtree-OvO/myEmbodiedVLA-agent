from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

from .models import AgentConfig


class CodexUnavailable(RuntimeError):
    pass


def assert_codex_ready(config: AgentConfig) -> None:
    if not config.auth_path.exists():
        raise CodexUnavailable(f"Codex auth file not found: {config.auth_path}")
    auth = _load_auth(config)
    if not auth.get("access_token"):
        raise CodexUnavailable("Codex auth file does not contain an access token. Run `codex login` again.")


def run_codex(prompt: str, config: AgentConfig, cwd: Path, output_path: Path | None = None) -> str:
    assert_codex_ready(config)
    output_path = output_path or (Path(".study-agent") / "last-codex-output.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        output = _run_codex_responses(prompt, config)
        output_path.write_text(output, encoding="utf-8")
        return output
    except CodexUnavailable:
        raise

    # Kept for future CLI fallback experiments; the direct endpoint is the main path.
    command = [
        "codex",
        "exec",
        "--skip-git-repo-check",
        "--ephemeral",
        "--sandbox",
        "read-only",
        "-m",
        config.model,
        "-C",
        str(cwd),
        "-o",
        str(output_path),
        "-",
    ]
    completed = subprocess.run(
        command,
        input=prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=config.timeout_seconds,
    )
    if completed.returncode != 0:
        stderr = _sanitize(completed.stderr)
        raise CodexUnavailable(f"Codex request failed with exit code {completed.returncode}: {stderr}")
    if output_path.exists():
        return output_path.read_text(encoding="utf-8", errors="replace")
    return completed.stdout


def _load_auth(config: AgentConfig) -> dict:
    try:
        data = json.loads(config.auth_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise CodexUnavailable(f"Could not read Codex auth file: {config.auth_path}") from exc
    tokens = data.get("tokens") or {}
    return {"access_token": tokens.get("access_token")}


def _run_codex_responses(prompt: str, config: AgentConfig) -> str:
    auth = _load_auth(config)
    payload = {
        "model": config.model,
        "instructions": "You are a Codex-powered study assistant. Follow the user prompt exactly.",
        "store": False,
        "stream": True,
        "input": [
            {
                "role": "user",
                "content": [{"type": "input_text", "text": prompt}],
            }
        ],
    }
    request = urllib.request.Request(
        config.api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {auth['access_token']}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=config.timeout_seconds) as response:
            body = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[-1000:]
        raise CodexUnavailable(f"Codex Responses HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise CodexUnavailable(f"Codex Responses request failed: {exc.reason}") from exc

    if body.lstrip().startswith("data:") or "\ndata:" in body:
        return _extract_sse_output_text(body)
    return _extract_output_text(json.loads(body))


def _extract_output_text(data: dict) -> str:
    if isinstance(data.get("output_text"), str):
        return data["output_text"]
    chunks: list[str] = []
    for item in data.get("output", []) or []:
        if isinstance(item, dict):
            for content in item.get("content", []) or []:
                if isinstance(content, dict):
                    text = content.get("text") or content.get("value")
                    if isinstance(text, str):
                        chunks.append(text)
    if chunks:
        return "\n".join(chunks)
    if isinstance(data.get("message"), str):
        return data["message"]
    raise CodexUnavailable("Codex response did not contain text output.")


def _extract_sse_output_text(body: str) -> str:
    chunks: list[str] = []
    fallback: list[str] = []
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line.startswith("data:"):
            continue
        payload = line.removeprefix("data:").strip()
        if not payload or payload == "[DONE]":
            continue
        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            continue
        event_type = event.get("type", "")
        delta = event.get("delta")
        if isinstance(delta, str):
            chunks.append(delta)
        text = event.get("text")
        if isinstance(text, str):
            chunks.append(text)
        if event_type.endswith(".done") or event_type == "response.completed":
            try:
                fallback.append(_extract_output_text(event.get("response") or event))
            except CodexUnavailable:
                pass
    if chunks:
        return _dedupe_stream_text("".join(chunks))
    if fallback:
        return "\n".join(fallback)
    raise CodexUnavailable("Codex streaming response did not contain text output.")


def _dedupe_stream_text(text: str) -> str:
    if len(text) % 2 == 0:
        half = len(text) // 2
        if text[:half] == text[half:]:
            return text[:half]
    return text


def _sanitize(text: str) -> str:
    redacted = text.replace("\\", "/")
    return redacted[-3000:]
