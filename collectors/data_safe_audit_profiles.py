import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_data_safe_audit_profiles(config):
    """
    Collect OCI Data Safe Audit Profiles across:
        - All subscribed regions
        - All accessible compartments

    Collects:
        - Audit Profile information
        - Creation date
        - OCI Defined Tags
        - Resource-specific details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing Data Safe Audit Profiles region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        data_safe_client = oci.data_safe.DataSafeClient(
            region_config
        )

        for compartment in compartments:

            try:

                profiles = (
                    oci.pagination.list_call_get_all_results(
                        data_safe_client.list_audit_profiles,
                        compartment_id=compartment["id"],
                    )
                )

                for profile in profiles.data:

                    resources.append(
                        Resource(
                            service="Data Safe",
                            resource_type="Audit Profile",
                            name=getattr(
                                profile,
                                "display_name",
                                getattr(
                                    profile,
                                    "name",
                                    "",
                                ),
                            ),
                            ocid=getattr(
                                profile,
                                "id",
                                "",
                            ),
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=getattr(
                                profile,
                                "lifecycle_state",
                                "",
                            ),

                            # -----------------------------------------
                            # Creation Date
                            # -----------------------------------------

                            time_created=getattr(
                                profile,
                                "time_created",
                                None,
                            ),

                            # -----------------------------------------
                            # OCI Defined Tags
                            # -----------------------------------------

                            defined_tags=getattr(
                                profile,
                                "defined_tags",
                                None,
                            ),

                            # -----------------------------------------
                            # Audit Profile details
                            # -----------------------------------------

                            details={
                                "target_id": getattr(
                                    profile,
                                    "target_id",
                                    "",
                                ),
                                "target_name": getattr(
                                    profile,
                                    "target_name",
                                    "",
                                ),
                                "database_id": getattr(
                                    profile,
                                    "database_id",
                                    "",
                                ),
                                "audit_profile_id": getattr(
                                    profile,
                                    "id",
                                    "",
                                ),
                                "description": getattr(
                                    profile,
                                    "description",
                                    "",
                                ),
                                "audit_trail_location": getattr(
                                    profile,
                                    "audit_trail_location",
                                    "",
                                ),
                                "audit_profile_type": getattr(
                                    profile,
                                    "audit_profile_type",
                                    "",
                                ),
                                "lifecycle_details": getattr(
                                    profile,
                                    "lifecycle_details",
                                    "",
                                ),
                            },
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR collecting Data Safe "
                    f"Audit Profiles from compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
