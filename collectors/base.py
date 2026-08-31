from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class Resource:
    """
    Common OCI resource model used by all collectors.

    Every OCI collector converts its service-specific
    resource into this standard Resource object.
    """

    # ---------------------------------------------------------
    # Basic resource information
    # ---------------------------------------------------------

    service: str
    resource_type: str
    name: str
    ocid: str

    # ---------------------------------------------------------
    # Compartment information
    # ---------------------------------------------------------

    compartment_id: str
    compartment_name: str

    # ---------------------------------------------------------
    # Location / lifecycle information
    # ---------------------------------------------------------

    region: str
    state: str = ""

    # ---------------------------------------------------------
    # Service-specific information
    # ---------------------------------------------------------

    details: Dict[str, Any] = field(
        default_factory=dict
    )

    # ---------------------------------------------------------
    # Resource creation date/time
    # ---------------------------------------------------------

    time_created: Any = None

    # ---------------------------------------------------------
    # OCI Defined Tags
    #
    # Example:
    #
    # {
    #     "maxlife": {
    #         "env": "nonprod",
    #         "project": "ing",
    #         "subenv": "nonprod",
    #         "subproject": "ing",
    #         "fy": "fy-24"
    #     },
    #     "Oracle-Tags": {
    #         "CreatedBy": "default/user@company.com"
    #     }
    # }
    #
    # ---------------------------------------------------------

    defined_tags: Dict[str, Any] = field(
        default_factory=dict
    )
