import os
from pathlib import Path


def _get_openai_client():
    try:
        from openai import OpenAI
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        return OpenAI(api_key=api_key)
    except ImportError:
        raise ImportError("openai package is required: pip install openai")


def complete(prompt: str, model: str = "gpt-4o", max_tokens: int = 2000) -> str:
    client = _get_openai_client()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.0,
    )
    return response.choices[0].message.content or ""


def save_raw(text: str, raw_dir: Path, name: str) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / name).write_text(text, encoding="utf-8")
