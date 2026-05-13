EVAL_TARGET_PROMPT = """\
You are a research paper auditor extracting evaluation targets.

RULES:
- Do NOT summarize the paper.
- Do NOT explain the method.
- Extract ONLY claims that can be verified with a numeric metric or a specific visual output.
- Each target must be a single verifiable unit (one metric on one dataset on one split).
- If the reported value is not stated, use null.
- Separate quantitative targets (numbers) from qualitative targets (figures, examples).
- Do not invent values or metrics not present in the text.

Return ONLY a fenced YAML block. No prose before or after.

```yaml
status: success
paper_title: "..."
inferred_domain: "..."
inferred_task: "..."

eval_targets:
  - id: E1
    priority: critical        # critical | high | medium | low
    evidence_type: quantitative  # quantitative | qualitative
    claim: "..."              # one sentence, exactly as close to paper wording as possible
    dataset: "..."
    split: "..."              # test | val | null
    metric: "..."
    reported_value: "..."     # exact number from paper, or null
    source: "..."             # "Table 2" / "Figure 4" / "Section 4.1"
    required_artifacts:
      - dataset               # dataset | checkpoint | eval_script | config
  - id: E2
    ...

missing_or_unclear:
  - "..."                     # anything needed but not specified in the paper
```

Paper text:
---
{paper_text}
---
"""

REPO_MATCH_PROMPT = """\
You are a research auditor. Determine whether this repository supports reproducing each eval target.

RULES:
- Do NOT invent evaluation scripts that are not present.
- A demo or inference script is NOT a benchmark eval script unless it explicitly computes
  the paper-reported metrics on the reported dataset split.
- If the repository appears unrelated to the paper, mark possible_mismatch_with_paper: true.
- Prefer status: blocked or unclear over optimistic supported unless evidence is clear.
- candidate_command must be a real command derivable from the README or code — not invented.

Return ONLY a fenced YAML block.

```yaml
status: success

repo_identity:
  name: "..."
  inferred_domain: "..."
  possible_mismatch_with_paper: false
  reason: ""                  # required if possible_mismatch_with_paper is true

target_matches:
  - target_id: E1
    status: supported         # supported | blocked | unclear
    blocker_type: null        # no_eval_script | no_metric_script | missing_checkpoint |
                              # missing_dataset | demo_only | no_matching_code | other
    confidence: high          # high | medium | low
    candidate_files:
      - "..."
    candidate_command: null   # exact runnable command or null
    notes:
      - "..."

repo_findings:
  has_eval_candidates: false
  has_demo_candidates: false
  has_metric_script: false
  has_checkpoint_links: false
  has_dataset_instructions: false

discrepancies:
  - severity: critical        # critical | warning | info
    text: "..."
```

Domain template context (if available):
---
{domain_context}
---

Eval targets:
---
{eval_targets_yaml}
---

Repository README (first 3000 chars):
---
{readme}
---

Candidate files (first 80 lines each):
---
{candidate_snippets}
---
"""

SUMMARY_PROMPT = """\
You are a research auditor. Write a concise plain-text audit narrative from the structured data below.
Focus on: what was found, what is blocked, what the user must do next.
Under 30 lines. No markdown headers. Plain prose.

Input:
---
{combined}
---
"""
