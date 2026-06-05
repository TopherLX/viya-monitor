from dataclasses import dataclass, field


@dataclass
class CollectResult:
    table_name: str
    rows: list = field(default_factory=list)
