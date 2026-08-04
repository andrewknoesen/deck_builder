from typing import List

from app.models.goldfish import GoldfishNodePublic, GoldfishSessionPublic
from pydantic import BaseModel


class GoldfishSessionTree(BaseModel):
    session: GoldfishSessionPublic
    nodes: List[GoldfishNodePublic]
