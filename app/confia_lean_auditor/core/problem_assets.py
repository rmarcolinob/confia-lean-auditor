from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class ProblemAssetValidationError(ValueError):
    pass


class ProblemConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    title: str
    statement: str
    answer_type: str
    correct_answer: Any
    max_score: float
    source: Optional[Dict[str, Any]] = None


class RubricItemConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    description: str
    points: float = Field(ge=0)
    claim_type: Optional[str] = None
    required_microclaim_ids: List[str] = Field(default_factory=list)


class RubricConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    problem_id: str
    max_score: float = Field(ge=0)
    items: List[RubricItemConfig]


class MicroclaimConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    description: str
    theorem: str
    claim_types: List[str] = Field(default_factory=list)
    required_formal_step_types: List[str] = Field(default_factory=list)
    depends_on_microclaim_ids: List[str] = Field(default_factory=list)
    supports_rubric_items: List[str] = Field(default_factory=list)


class MicroclaimsConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    problem_id: str
    microclaims: List[MicroclaimConfig]


class ProblemAssets(BaseModel):
    model_config = ConfigDict(extra="allow")

    problem: ProblemConfig
    rubric: RubricConfig
    microclaims: MicroclaimsConfig


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise ProblemAssetValidationError(f"Arquivo obrigatório não encontrado: {path}")

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ProblemAssetValidationError(
            f"JSON inválido em {path}: {exc.msg} na linha {exc.lineno}, coluna {exc.colno}."
        ) from exc

    if not isinstance(data, dict):
        raise ProblemAssetValidationError(
            f"JSON inválido em {path}: esperado objeto JSON no nível raiz."
        )

    return data


def _format_pydantic_errors(path: Path, exc: ValidationError) -> str:
    pieces = []

    for error in exc.errors():
        loc = ".".join(str(part) for part in error.get("loc", []))
        msg = error.get("msg", "erro de validação")
        pieces.append(f"{loc}: {msg}")

    joined = "; ".join(pieces)
    return f"Schema inválido em {path}: {joined}"


def load_problem_config(problem_dir: Path) -> ProblemConfig:
    path = problem_dir / "problem.json"
    data = _load_json(path)

    try:
        return ProblemConfig.model_validate(data)
    except ValidationError as exc:
        raise ProblemAssetValidationError(
            _format_pydantic_errors(path, exc)
        ) from exc


def load_rubric_config(problem_dir: Path) -> RubricConfig:
    path = problem_dir / "rubric.json"
    data = _load_json(path)

    try:
        return RubricConfig.model_validate(data)
    except ValidationError as exc:
        raise ProblemAssetValidationError(
            _format_pydantic_errors(path, exc)
        ) from exc


def load_microclaims_config(problem_dir: Path) -> MicroclaimsConfig:
    path = problem_dir / "microclaims.json"
    data = _load_json(path)

    try:
        return MicroclaimsConfig.model_validate(data)
    except ValidationError as exc:
        raise ProblemAssetValidationError(
            _format_pydantic_errors(path, exc)
        ) from exc


def _assert_unique_ids(kind: str, ids: List[str]) -> None:
    seen = set()
    repeated = []

    for item_id in ids:
        if item_id in seen:
            repeated.append(item_id)
        seen.add(item_id)

    if repeated:
        raise ProblemAssetValidationError(
            f"IDs duplicados em {kind}: {sorted(set(repeated))}"
        )


def validate_problem_assets(problem_dir: Path, expected_problem_id: str) -> ProblemAssets:
    problem = load_problem_config(problem_dir)
    rubric = load_rubric_config(problem_dir)
    microclaims = load_microclaims_config(problem_dir)

    if problem.id != expected_problem_id:
        raise ProblemAssetValidationError(
            f"problem.json tem id={problem.id!r}, mas o esperado é {expected_problem_id!r}."
        )

    if rubric.problem_id != expected_problem_id:
        raise ProblemAssetValidationError(
            f"rubric.json tem problem_id={rubric.problem_id!r}, mas o esperado é {expected_problem_id!r}."
        )

    if microclaims.problem_id != expected_problem_id:
        raise ProblemAssetValidationError(
            f"microclaims.json tem problem_id={microclaims.problem_id!r}, mas o esperado é {expected_problem_id!r}."
        )

    rubric_item_ids = [item.id for item in rubric.items]
    microclaim_ids = [mc.id for mc in microclaims.microclaims]

    _assert_unique_ids("rubric.items", rubric_item_ids)
    _assert_unique_ids("microclaims.microclaims", microclaim_ids)

    microclaim_id_set = set(microclaim_ids)
    rubric_item_id_set = set(rubric_item_ids)

    for item in rubric.items:
        for microclaim_id in item.required_microclaim_ids:
            if microclaim_id not in microclaim_id_set:
                raise ProblemAssetValidationError(
                    f"rubric item {item.id!r} exige microclaim inexistente: {microclaim_id!r}."
                )

    for mc in microclaims.microclaims:
        for dep_id in mc.depends_on_microclaim_ids:
            if dep_id not in microclaim_id_set:
                raise ProblemAssetValidationError(
                    f"microclaim {mc.id!r} depende de microclaim inexistente: {dep_id!r}."
                )

        for rubric_item_id in mc.supports_rubric_items:
            if rubric_item_id not in rubric_item_id_set:
                raise ProblemAssetValidationError(
                    f"microclaim {mc.id!r} referencia item de rubrica inexistente: {rubric_item_id!r}."
                )

    total_points = sum(item.points for item in rubric.items)

    if abs(total_points - rubric.max_score) > 1e-9:
        raise ProblemAssetValidationError(
            f"Soma dos pontos da rubrica ({total_points}) difere de max_score ({rubric.max_score})."
        )

    if abs(problem.max_score - rubric.max_score) > 1e-9:
        raise ProblemAssetValidationError(
            f"problem.json max_score ({problem.max_score}) difere de rubric.json max_score ({rubric.max_score})."
        )

    return ProblemAssets(
        problem=problem,
        rubric=rubric,
        microclaims=microclaims,
    )
