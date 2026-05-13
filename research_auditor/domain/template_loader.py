from __future__ import annotations
from pathlib import Path
import yaml

_TEMPLATES_DIR = Path(__file__).parent.parent / "configs" / "domain_templates"

_DOMAIN_ALIASES: dict[str, list[str]] = {
    "nerf_3dgs": [
        "nerf", "neural radiance", "3dgs", "gaussian splatting",
        "novel view synthesis", "radiance field", "nerfstudio", "instant-ngp",
        "psnr", "ssim", "lpips", "blender dataset", "mip-nerf",
    ],
    "6d_pose_bop": [
        "6d pose", "pose estimation", "bop", "6dof", "object pose",
        "vsd", "mssd", "mspd", "add-s", "bop toolkit", "t-less", "ycb-v", "lm-o",
    ],
    "llm_eval": [
        "language model", "llm", "large language model", "text generation",
        "perplexity", "bleu", "rouge", "exact match", "pass@k", "win rate",
        "lm-eval", "helm", "opencompass", "huggingface evaluate",
    ],
    "vision_detection": [
        "object detection", "yolo", "faster rcnn", "faster r-cnn", "detr",
        "map", "ap50", "coco detection", "bounding box", "instance segmentation",
    ],
}


def infer_domain(eval_targets: dict) -> str:
    text = str(eval_targets).lower()
    for domain_id, aliases in _DOMAIN_ALIASES.items():
        if any(alias in text for alias in aliases):
            return domain_id
    return "generic_ml"


def load_template(domain_id: str) -> dict | None:
    p = _TEMPLATES_DIR / f"{domain_id}.yaml"
    if p.exists():
        return yaml.safe_load(p.read_text(encoding="utf-8"))
    return None


def get_domain_context(eval_targets: dict) -> tuple[str, str]:
    """Returns (domain_id, template_as_yaml_string)."""
    domain_id = infer_domain(eval_targets)
    template = load_template(domain_id)
    if not template:
        return domain_id, ""
    return domain_id, yaml.dump(template, allow_unicode=True, default_flow_style=False)
