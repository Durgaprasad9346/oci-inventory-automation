import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_alarms(config):
    """
    Collect all OCI Monitoring Alarms across:
        - All subscribed regions
        - All accessible compartments

    Collects:
        - Resource information
        - Creation date
        - OCI Defined Tags
        - Existing Alarm details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing Alarms region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        monitoring_client = oci.monitoring.MonitoringClient(
            region_config
        )

        for compartment in compartments:

            try:

                alarms = (
                    oci.pagination.list_call_get_all_results(
                        monitoring_client.list_alarms,
                        compartment_id=compartment["id"],
                    )
                )

                for alarm in alarms.data:

                    resources.append(
                        Resource(
                            service="Monitoring",
                            resource_type="Alarm",
                            name=getattr(
                                alarm,
                                "display_name",
                                "",
                            ),
                            ocid=getattr(
                                alarm,
                                "id",
                                "",
                            ),
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=getattr(
                                alarm,
                                "lifecycle_state",
                                "",
                            ),

                            # -----------------------------------------
                            # Creation Date
                            # -----------------------------------------

                            time_created=getattr(
                                alarm,
                                "time_created",
                                None,
                            ),

                            # -----------------------------------------
                            # OCI Defined Tags
                            # -----------------------------------------

                            defined_tags=getattr(
                                alarm,
                                "defined_tags",
                                None,
                            ),

                            # -----------------------------------------
                            # Existing Alarm details
                            # -----------------------------------------

                            details={
                                "namespace": getattr(
                                    alarm,
                                    "namespace",
                                    "",
                                ),
                                "query": getattr(
                                    alarm,
                                    "query",
                                    "",
                                ),
                                "severity": getattr(
                                    alarm,
                                    "severity",
                                    "",
                                ),
                                "is_enabled": getattr(
                                    alarm,
                                    "is_enabled",
                                    "",
                                ),
                                "pending_duration": getattr(
                                    alarm,
                                    "pending_duration",
                                    "",
                                ),
                                "repeat_notification_duration": getattr(
                                    alarm,
                                    "repeat_notification_duration",
                                    "",
                                ),
                                "metric_compartment_id": getattr(
                                    alarm,
                                    "metric_compartment_id",
                                    "",
                                ),
                                "destinations": getattr(
                                    alarm,
                                    "destinations",
                                    "",
                                ),
                            },
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR collecting Monitoring "
                    f"from compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
