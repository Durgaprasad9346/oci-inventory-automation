import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_notifications(config):
    """
    Collect all OCI Notification Topics across:
        - All subscribed regions
        - All accessible compartments

    Collects:
        - Resource information
        - Creation date
        - OCI Defined Tags
        - Existing Notification details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing Notifications region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        ons_client = oci.ons.NotificationControlPlaneClient(
            region_config
        )

        for compartment in compartments:

            try:

                topics = (
                    oci.pagination.list_call_get_all_results(
                        ons_client.list_topics,
                        compartment_id=compartment["id"],
                    )
                )

                for topic in topics.data:

                    resources.append(
                        Resource(
                            service="Notifications",
                            resource_type="Notification Topic",
                            name=getattr(
                                topic,
                                "name",
                                "",
                            ),
                            ocid=getattr(
                                topic,
                                "topic_id",
                                "",
                            ),
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=getattr(
                                topic,
                                "lifecycle_state",
                                "",
                            ),

                            # -----------------------------------------
                            # Creation Date
                            # -----------------------------------------

                            time_created=getattr(
                                topic,
                                "time_created",
                                None,
                            ),

                            # -----------------------------------------
                            # OCI Defined Tags
                            # -----------------------------------------

                            defined_tags=getattr(
                                topic,
                                "defined_tags",
                                None,
                            ),

                            # -----------------------------------------
                            # Existing Notification details
                            # -----------------------------------------

                            details={
                                "topic_id": getattr(
                                    topic,
                                    "topic_id",
                                    "",
                                ),
                                "description": getattr(
                                    topic,
                                    "description",
                                    "",
                                ),
                            },
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR collecting Notifications "
                    f"from compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
