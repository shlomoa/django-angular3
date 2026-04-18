from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .config import ProjectConfig


@dataclass(frozen=True)
class BuildTask:
    name: str
    input: str
    output: str


@dataclass(frozen=True)
class BuildPlan:
    project_name: str
    config_path: str
    tasks: list[BuildTask]

    def to_dict(self) -> dict[str, object]:
        return {
            "projectName": self.project_name,
            "configPath": self.config_path,
            "tasks": [asdict(task) for task in self.tasks],
        }


def create_build_plan(config: ProjectConfig) -> BuildPlan:
    tasks = [
        BuildTask(
            name="validate-openapi",
            input=str(config.openapi_source),
            output="validated OpenAPI document",
        ),
        BuildTask(
            name="generate-openapi-clients",
            input=str(config.openapi_generator_config or config.openapi_source),
            output=str(config.angular_output / "generated"),
        ),
        BuildTask(
            name="validate-ui",
            input=str(config.ui_source),
            output="validated UI definition document",
        ),
        BuildTask(
            name="assemble-angular-application",
            input=str(config.ui_source),
            output=str(config.angular_output),
        ),
    ]
    return BuildPlan(
        project_name=config.project_name,
        config_path=str(config.config_path),
        tasks=tasks,
    )


def write_build_plan(plan: BuildPlan, output_dir: str | Path) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    plan_path = output_path / "plan.json"
    plan_path.write_text(json.dumps(plan.to_dict(), indent=2), encoding="utf-8")
    return plan_path
