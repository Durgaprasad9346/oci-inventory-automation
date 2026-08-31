import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_data_safe_audit_policies(config):
    """
    Collect OCI Data Safe Audit Policies across:
        - All subscribed regions
        - All accessible compartments

    Collects:
        - Audit Policy information
        - Creation date
        - OCI Defined Tags
        - Resource-specific details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing Data Safe Audit Policies region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        data_safe_client = oci.data_safe.DataSafeClient(
            region_config
        )

        for compartment in compartments:

            try:

                policies = (
                    oci.pagination.list_call_get_all_results(
                        data_safe_client.list_audit_policies,
                        compartment_id=compartment["id"],
                    )
                )

                for policy in policies.data:

                    resources.append(
                        Resource(
                            service="Data Safe",
                            resource_type="Audit Policy",
                            name=getattr(
                                policy,
                                "display_name",
                                getattr(
                                    policy,
                                    "name",
                                    "",
                                ),
                            ),
                            ocid=getattr(
                                policy,
                                "id",
                                "",
                            ),
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=getattr(
                                policy,
                                "lifecycle_state",
                                "",
                            ),

                            # -----------------------------------------
                            # Creation Date
                            # -----------------------------------------

                            time_created=getattr(
                                policy,
                                "time_created",
                                None,
                            ),

                            # -----------------------------------------
                            # OCI Defined Tags
                            # -----------------------------------------

                            defined_tags=getattr(
                                policy,
                                "defined_tags",
                                None,
                            ),

                            # -----------------------------------------
                            # Audit Policy details
                            # -----------------------------------------

                            details={
                                "target_id": getattr(
                                    policy,
                                    "target_id",
                                    "",
                                ),
                                "target_name": getattr(
                                    policy,
                                    "target_name",
                                    "",
                                ),
                                "database_id": getattr(
                                    policy,
                                    "database_id",
                                    "",
                                ),
                                "audit_policy_id": getattr(
                                    policy,
                                    "id",
                                    "",
                                ),
                                "description": getattr(
                                    policy,
                                    "description",
                                    "",
                                ),
                                "policy_type": getattr(
                                    policy,
                                    "policy_type",
                                    "",
                                ),
                                "lifecycle_details": getattr(
                                    policy,
                                    "lifecycle_details",
                                    "",
                                ),
                            },
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR collecting Data Safe "
                    f"Audit Policies from compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
