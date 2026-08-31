import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_data_safe_sensitive_data_models(config):
    """
    Collect OCI Data Safe Sensitive Data Models across:
        - All subscribed regions
        - All accessible compartments

    Collects:
        - Sensitive Data Model information
        - Creation date
        - OCI Defined Tags
        - Resource-specific details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing Data Safe Sensitive Data Models region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        data_safe_client = oci.data_safe.DataSafeClient(
            region_config
        )

        for compartment in compartments:

            try:

                models = (
                    oci.pagination.list_call_get_all_results(
                        data_safe_client.list_sensitive_data_models,
                        compartment_id=compartment["id"],
                    )
                )

                for model in models.data:

                    resources.append(
                        Resource(
                            service="Data Safe",
                            resource_type="Sensitive Data Model",
                            name=getattr(
                                model,
                                "display_name",
                                getattr(
                                    model,
                                    "name",
                                    "",
                                ),
                            ),
                            ocid=getattr(
                                model,
                                "id",
                                "",
                            ),
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=getattr(
                                model,
                                "lifecycle_state",
                                "",
                            ),

                            # -----------------------------------------
                            # Creation Date
                            # -----------------------------------------

                            time_created=getattr(
                                model,
                                "time_created",
                                None,
                            ),

                            # -----------------------------------------
                            # OCI Defined Tags
                            # -----------------------------------------

                            defined_tags=getattr(
                                model,
                                "defined_tags",
                                None,
                            ),

                            # -----------------------------------------
                            # Resource-specific details
                            # -----------------------------------------

                            details={
                                "target_id": getattr(
                                    model,
                                    "target_id",
                                    "",
                                ),
                                "target_name": getattr(
                                    model,
                                    "target_name",
                                    "",
                                ),
                                "database_id": getattr(
                                    model,
                                    "database_id",
                                    "",
                                ),
                                "sensitive_data_model_id": getattr(
                                    model,
                                    "id",
                                    "",
                                ),
                                "description": getattr(
                                    model,
                                    "description",
                                    "",
                                ),
                                "time_of_deletion": getattr(
                                    model,
                                    "time_of_deletion",
                                    None,
                                ),
                                "lifecycle_details": getattr(
                                    model,
                                    "lifecycle_details",
                                    "",
                                ),
                            },
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR collecting Data Safe "
                    f"Sensitive Data Models from compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
