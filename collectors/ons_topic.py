import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_ons_topics(config):
    """
    Collect all OCI Notifications Service (ONS) Topics across:
        - All subscribed regions
        - All accessible compartments

    Collects:
        - Topic information
        - Creation date
        - OCI Defined Tags
        - Topic details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing ONS Topics region: {region}"
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
                            resource_type="ONS Topic",
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
                            # Topic details
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
                                "api_endpoint": getattr(
                                    topic,
                                    "api_endpoint",
                                    "",
                                ),
                            },
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR collecting ONS Topics "
                    f"from compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
