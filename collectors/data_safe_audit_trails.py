import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_data_safe_audit_trails(config):
    """
    Collect OCI Data Safe Audit Trails across:
        - All subscribed regions
        - All accessible compartments

    Collects:
        - Audit Trail information
        - Creation date
        - OCI Defined Tags
        - Audit Trail details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing Data Safe Audit Trails region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        data_safe_client = oci.data_safe.DataSafeClient(
            region_config
        )

        for compartment in compartments:

            try:

                audit_trails = (
                    oci.pagination.list_call_get_all_results(
                        data_safe_client.list_audit_trails,
                        compartment_id=compartment["id"],
                    )
                )

                for audit_trail in audit_trails.data:

                    resources.append(
                        Resource(
                            service="Data Safe",
                            resource_type="Audit Trail",
                            name=getattr(
                                audit_trail,
                                "display_name",
                                getattr(
                                    audit_trail,
                                    "name",
                                    "",
                                ),
                            ),
                            ocid=getattr(
                                audit_trail,
                                "id",
                                "",
                            ),
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=getattr(
                                audit_trail,
                                "lifecycle_state",
                                "",
                            ),

                            # -----------------------------------------
                            # Creation Date
                            # -----------------------------------------

                            time_created=getattr(
                                audit_trail,
                                "time_created",
                                None,
                            ),

                            # -----------------------------------------
                            # OCI Defined Tags
                            # -----------------------------------------

                            defined_tags=getattr(
                                audit_trail,
                                "defined_tags",
                                None,
                            ),

                            # -----------------------------------------
                            # Audit Trail details
                            # -----------------------------------------

                            details={
                                "target_id": getattr(
                                    audit_trail,
                                    "target_id",
                                    "",
                                ),
                                "target_name": getattr(
                                    audit_trail,
                                    "target_name",
                                    "",
                                ),
                                "database_id": getattr(
                                    audit_trail,
                                    "database_id",
                                    "",
                                ),
                                "audit_trail_location": getattr(
                                    audit_trail,
                                    "audit_trail_location",
                                    "",
                                ),
                                "audit_collection_start_time": getattr(
                                    audit_trail,
                                    "audit_collection_start_time",
                                    "",
                                ),
                                "audit_collection_end_time": getattr(
                                    audit_trail,
                                    "audit_collection_end_time",
                                    "",
                                ),
                                "audit_profile_id": getattr(
                                    audit_trail,
                                    "audit_profile_id",
                                    "",
                                ),
                                "status": getattr(
                                    audit_trail,
                                    "status",
                                    "",
                                ),
                            },
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR collecting Data Safe "
                    f"Audit Trails from compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
