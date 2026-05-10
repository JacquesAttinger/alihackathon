"""Module data model — a named weight vector created from a natural language prompt."""

from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class Module:
    name: str
    prompt: str
    weights: dict[str, float]        # { param_key: 0.0–1.0 }
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "prompt": self.prompt,
            "weights": self.weights,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Module":
        return cls(
            id=d["id"],
            name=d["name"],
            prompt=d["prompt"],
            weights=d["weights"],
            created_at=d["created_at"],
        )
