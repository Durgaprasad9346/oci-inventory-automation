import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_alarms(config):
    """
    Collect all OCI Monitoring alarms across all subscribed
    regions and accessible compartments.
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(f"  Processing Alarms region: {region}")

        region_config = config.copy()
        region_config["region"] = region

        monitoring_client = oci.monitoring.MonitoringClient(
            region_config
        )

        for compartment in compartments:

            alarms = oci.pagination.list_call_get_all_results(
                monitoring_client.list_alarms,
                compartment_id=compartment["id"],
            )

            for alarm in alarms.data:

                resources.append(
                    Resource(
                        service="Monitoring",
                        resource_type="Alarm",
                        name=alarm.display_name,
                        ocid=alarm.id,
                        compartment_id=compartment["id"],
                        compartment_name=compartment["name"],
                        region=region,
                        state=getattr(
                            alarm,
                            "lifecycle_state",
                            "",
                        ),
                        details={
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
                            "metric_compartment_id": getattr(
                                alarm,
                                "metric_compartment_id",
                                "",
                            ),
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
                            "pending_duration": getattr(
                                alarm,
                                "pending_duration",
                                "",
                            ),
                            "notification_topic_id": getattr(
                                alarm,
                                "destinations",
                                [],
                            ),
                        },
                    )
                )

    return resources
