"""
Parameter registry — the contract between the routing algorithm and the LLM/UI.
Currently only scenic_quality is active. More parameters will be added here as
they are validated and enabled.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ParameterDef:
    key: str
    name: str
    description: str
    category: str
    direction: str   # "prefer" = higher score is better; "avoid" = higher score is worse


PARAMETER_REGISTRY: dict[str, ParameterDef] = {p.key: p for p in [

    ParameterDef(
        key="scenic_quality",
        name="Scenic Quality",
        description="Parks, green space, trees, and lakefront access along the route",
        category="aesthetics",
        direction="prefer",
    ),

    # Future parameters will be added here as they are implemented and tested.

]}
