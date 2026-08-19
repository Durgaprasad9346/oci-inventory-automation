import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_notifications(config):
    """
    Collect all OCI Notification Topics across all subscribed
    regions and accessible compartments.
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(f"  Processing Notifications region: {region}")

        region_config = config.copy()
        region_config["region"] = region

        ons_client = oci.ons.NotificationControlPlaneClient(
            region_config
        )

        for compartment in compartments:

            topics = oci.pagination.list_call_get_all_results(
                ons_client.list_topics,
                compartment_id=compartment["id"],
            )

            for topic in topics.data:

                resources.append(
                    Resource(
                        service="Notifications",
                        resource_type="Topic",
                        name=topic.name,
                        ocid=topic.topic_id,
                        compartment_id=compartment["id"],
                        compartment_name=compartment["name"],
                        region=region,
                        state=getattr(
                            topic,
                            "lifecycle_state",
                            "",
                        ),
                        details={
                            "description": getattr(
                                topic,
                                "description",
                                "",
                            ),
                            "time_created": getattr(
                                topic,
                                "time_created",
                                "",
                            ),
                        },
                    )
                )

    return resources
