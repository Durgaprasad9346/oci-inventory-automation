from dataclasses import dataclass
from typing import Any, Dict, Optional


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
    compartment_name: str
    region: str
    state: str = ""
    details: Optional[Dict[str, Any]] = None
