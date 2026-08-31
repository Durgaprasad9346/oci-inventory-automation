import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_logging(config):
    """
    Collect all OCI Logging resources across:
        - All subscribed regions
        - All accessible compartments

    Collects:
        - Resource information
        - Creation date
        - OCI Defined Tags
        - Existing Logging details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing Logging region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        logging_client = oci.logging.LoggingManagementClient(
            region_config
        )

        for compartment in compartments:

            try:

                logs = (
                    oci.pagination.list_call_get_all_results(
                        logging_client.list_logs,
                        log_group_id=None,
                        compartment_id=compartment["id"],
                    )
                )

                for log in logs.data:

                    resources.append(
                        Resource(
                            service="Logging",
                            resource_type="Log",
                            name=getattr(
                                log,
                                "display_name",
                                "",
                            ),
                            ocid=getattr(
                                log,
                                "id",
                                "",
                            ),
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=getattr(
                                log,
                                "lifecycle_state",
                                "",
                            ),

                            # -----------------------------------------
                            # Creation Date
                            # -----------------------------------------

                            time_created=getattr(
                                log,
                                "time_created",
                                None,
                            ),

                            # -----------------------------------------
                            # OCI Defined Tags
                            # -----------------------------------------

                            defined_tags=getattr(
                                log,
                                "defined_tags",
                                None,
                            ),

                            # -----------------------------------------
                            # Existing Logging details
                            # -----------------------------------------

                            details={
                                "log_group_id": getattr(
                                    log,
                                    "log_group_id",
                                    "",
                                ),
                                "log_type": getattr(
                                    log,
                                    "log_type",
                                    "",
                                ),
                                "source": getattr(
                                    log,
                                    "source",
                                    "",
                                ),
                                "retention_duration": getattr(
                                    log,
                                    "retention_duration",
                                    "",
                                ),
                                "is_enabled": getattr(
                                    log,
                                    "is_enabled",
                                    "",
                                ),
                            },
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR collecting Logging "
                    f"from compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
