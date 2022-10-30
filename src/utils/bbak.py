import dataclasses

from src.utils.doco_config import DocoConfig


@dataclasses.dataclass
class BbakContextObject:
    workdir: str
    doco_config: DocoConfig
