from dataclasses import dataclass, field
from typing import Dict, List, TypedDict, Optional, Union


class TestSuite(TypedDict):
    description: str
    settings: List[Dict[str, str]]


class JobState(TypedDict):
    state: str
    result: str
    settings: Optional[Dict[str, str]]


@dataclass
class Product:
    """A product/medium as received by from the openQA API."""

    distri: str
    version: str
    flavor: str
    arch: str = "x86_64"
    settings: List[Dict[str, str]] = field(default_factory=list)

    def equal_in_db(self, other_dict: Dict[str, str]) -> bool:
        """
        Check whether the dictionary in other_dict is the 'same' entry given
        the uniqueness constraints applied to products/mediums.
        """
        # products have a UNIQUE (distri, version, arch, flavor) constraint
        # applied in the DB
        return (
            other_dict.get("distri") == self.distri
            and other_dict.get("version") == self.version
            and other_dict.get("flavor") == self.flavor
            and other_dict.get("arch") == self.arch
        )


class JobScheduledWithoutErrorReply(TypedDict):
    count: int
    ids: List[int]
    scheduled_product_id: int


class JobScheduledWithErrorReply(JobScheduledWithoutErrorReply):
    error: str


JobScheduledReply = Union[
    JobScheduledWithoutErrorReply, JobScheduledWithErrorReply
]
