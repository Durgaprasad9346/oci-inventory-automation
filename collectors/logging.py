import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_logging(config):
    """
    Collect OCI Logging log groups across all subscribed
    regions and accessible compartments.
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(f"  Processing Logging region: {region}")

        region_config = config.copy()
        region_config["region"] = region

        logging_client = oci.logging.LoggingManagementClient(
            region_config
        )

        for compartment in compartments:

            log_groups = oci.pagination.list_call_get_all_results(
                logging_client.list_log_groups,
                compartment_id=compartment["id"],
            )

            for log_group in log_groups.data:

                resources.append(
                    Resource(
                        service="Logging",
                        resource_type="Log Group",
                        name=log_group.display_name,
                        ocid=log_group.id,
                        compartment_id=compartment["id"],
                        compartment_name=compartment["name"],
                        region=region,
                        state=getattr(
                            log_group,
                            "lifecycle_state",
                            "",
                        ),
                        details={
                            "description": getattr(
                                log_group,
                                "description",
                                "",
                            ),
                            "time_created": getattr(
                                log_group,
                                "time_created",
                                "",
                            ),
                        },
                    )
                )

    return resources
