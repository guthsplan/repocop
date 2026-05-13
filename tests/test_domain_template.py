from research_auditor.domain.template_loader import infer_domain, load_template, get_domain_context


def test_nerf_domain_inferred():
    targets = {"eval_targets": [{"metric": "PSNR", "dataset": "NeRF Synthetic"}]}
    assert infer_domain(targets) == "nerf_3dgs"


def test_bop_domain_inferred():
    targets = {"eval_targets": [{"metric": "AR", "dataset": "T-LESS"}]}
    assert infer_domain(targets) == "6d_pose_bop"


def test_llm_domain_inferred():
    targets = {"eval_targets": [{"metric": "exact_match", "claim": "LLM evaluation with HELM"}]}
    assert infer_domain(targets) == "llm_eval"


def test_detection_domain_inferred():
    targets = {"eval_targets": [{"metric": "mAP", "dataset": "COCO detection"}]}
    assert infer_domain(targets) == "vision_detection"


def test_fallback_to_generic():
    targets = {"eval_targets": [{"metric": "loss", "dataset": "custom"}]}
    assert infer_domain(targets) == "generic_ml"


def test_load_template_nerf():
    template = load_template("nerf_3dgs")
    assert template is not None
    assert "PSNR" in template["common_metrics"]
    assert len(template["red_flags"]) > 0


def test_get_domain_context_returns_tuple():
    targets = {"eval_targets": [{"metric": "PSNR"}]}
    domain_id, ctx = get_domain_context(targets)
    assert domain_id == "nerf_3dgs"
    assert "PSNR" in ctx


def test_load_nonexistent_template():
    assert load_template("does_not_exist") is None
