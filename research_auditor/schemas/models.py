from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, Field


class PaperConfig(BaseModel):
    url: Optional[str] = None
    pdf_path: Optional[str] = None


class RepoConfig(BaseModel):
    url: Optional[str] = None
    local_path: Optional[str] = None


class ExecutionConfig(BaseModel):
    mode: str = "local"
    workdir: str
    execute: bool = False


class SafetyConfig(BaseModel):
    allow_sudo: bool = False
    restrict_to_workdir: bool = True
    allow_network: bool = True


class ResourceConfig(BaseModel):
    conda_path: Optional[str] = None
    dataset_path: Optional[str] = None
    checkpoint_path: Optional[str] = None


class AuditConfig(BaseModel):
    run_name: Optional[str] = None
    paper: PaperConfig = Field(default_factory=PaperConfig)
    repo: RepoConfig = Field(default_factory=RepoConfig)
    execution: ExecutionConfig
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    resources: ResourceConfig = Field(default_factory=ResourceConfig)
