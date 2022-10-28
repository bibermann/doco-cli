import dataclasses

from utils.doco_config import DocoConfig


@dataclasses.dataclass
class BbakContextObject:
    workdir: str
    project_id: str
    doco_config: DocoConfig
