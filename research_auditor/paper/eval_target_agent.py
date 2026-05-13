from pathlib import Path
from ..llm import client as llm
from ..llm.parse import extract_yaml_block
from ..llm.prompts import EVAL_TARGET_PROMPT


def extract_eval_targets(paper_text: str, run_dir: Path) -> dict:
    prompt = EVAL_TARGET_PROMPT.format(paper_text=paper_text)

    try:
        raw = llm.complete(prompt, max_tokens=2000)
    except Exception as e:
        raw = f"[LLM call failed: {e}]"

    llm.save_raw(raw, run_dir / "raw_llm", "03_eval_targets_raw.md")

    result = extract_yaml_block(raw)
    if result.get("status") == "parse_failed":
        result["step"] = "eval_target_extraction"
    return result
