import yaml
from pathlib import Path
from ..llm import client as llm
from ..llm.parse import extract_yaml_block
from ..llm.prompts import REPO_MATCH_PROMPT
from .clone import read_readme
from .candidates import read_candidate_snippets


def match_repo_to_eval_targets(
    repo_path: Path,
    repo_scan: dict,
    eval_targets: dict,
    run_dir: Path,
    domain_context: str = "",
) -> dict:
    readme = read_readme(repo_path)

    all_candidates = (
        repo_scan.get("candidate_eval_files", []) +
        repo_scan.get("candidate_demo_files", [])
    )
    snippets = read_candidate_snippets(repo_path, all_candidates)

    eval_targets_yaml = yaml.dump(eval_targets, allow_unicode=True)

    prompt = REPO_MATCH_PROMPT.format(
        domain_context=domain_context[:1500] if domain_context else "(not detected)",
        eval_targets_yaml=eval_targets_yaml[:3000],
        readme=readme[:3000],
        candidate_snippets=snippets[:3000],
    )

    try:
        raw = llm.complete(prompt, max_tokens=2000)
    except Exception as e:
        raw = f"[LLM call failed: {e}]"

    llm.save_raw(raw, run_dir / "raw_llm", "04_repo_match_raw.md")

    result = extract_yaml_block(raw)
    if result.get("status") == "parse_failed":
        result["step"] = "repo_match"
    return result
