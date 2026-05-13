import re
import yaml


def extract_yaml_block(text: str) -> dict:
    match = re.search(r"```yaml\s*(.*?)```", text, re.DOTALL)
    if match:
        raw = match.group(1).strip()
        try:
            return yaml.safe_load(raw)
        except yaml.YAMLError:
            pass

    try:
        return yaml.safe_load(text)
    except yaml.YAMLError:
        pass

    return {
        "status": "parse_failed",
        "error": "Could not extract YAML from LLM response.",
        "raw_preview": text[:500],
    }
