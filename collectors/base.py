from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class Resource:
    """
    Standard representation of an OCI resource.
    """

    service: str
    resource_type: str
    name: str
    ocid: str
    compartment_id: str
    region: str
    state: str = ""
    details: Dict[str, Any] | None = None
