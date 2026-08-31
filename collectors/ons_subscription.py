import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_ons_subscriptions(config):
    """
    Collect all OCI Notifications Service (ONS) Subscriptions across:
        - All subscribed regions
        - All accessible compartments
        - All notification topics

    Collects:
        - Subscription information
        - Creation date
        - OCI Defined Tags
        - Subscription details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing ONS Subscriptions region: {region}"
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

            except Exception as error:

                print(
                    f"    ERROR collecting ONS Topics from "
                    f"compartment {compartment['name']}: {error}"
                )

                continue

            for topic in topics.data:

                topic_id = getattr(
                    topic,
                    "topic_id",
                    "",
                )

                topic_name = getattr(
                    topic,
                    "name",
                    "",
                )

                if not topic_id:
                    continue

                try:

                    subscriptions = (
                        oci.pagination.list_call_get_all_results(
                            ons_client.list_subscriptions,
                            compartment_id=compartment["id"],
                            topic_id=topic_id,
                        )
                    )

                except Exception as error:

                    print(
                        f"    ERROR collecting subscriptions "
                        f"for topic {topic_name}: {error}"
                    )

                    continue

                for subscription in subscriptions.data:

                    resources.append(
                        Resource(
                            service="Notifications",
                            resource_type="ONS Subscription",
                            name=getattr(
                                subscription,
                                "endpoint",
                                "",
                            ),
                            ocid=getattr(
                                subscription,
                                "id",
                                "",
                            ),
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=getattr(
                                subscription,
                                "lifecycle_state",
                                "",
                            ),

                            # -----------------------------------------
                            # Creation Date
                            # -----------------------------------------

                            time_created=getattr(
                                subscription,
                                "time_created",
                                None,
                            ),

                            # -----------------------------------------
                            # OCI Defined Tags
                            # -----------------------------------------

                            defined_tags=getattr(
                                subscription,
                                "defined_tags",
                                None,
                            ),

                            # -----------------------------------------
                            # Subscription details
                            # -----------------------------------------

                            details={
                                "subscription_id": getattr(
                                    subscription,
                                    "id",
                                    "",
                                ),
                                "topic_id": topic_id,
                                "topic_name": topic_name,
                                "endpoint": getattr(
                                    subscription,
                                    "endpoint",
                                    "",
                                ),
                                "protocol": getattr(
                                    subscription,
                                    "protocol",
                                    "",
                                ),
                                "delivery_policy": getattr(
                                    subscription,
                                    "delivery_policy",
                                    "",
                                ),
                                "filter_rule": getattr(
                                    subscription,
                                    "filter_rule",
                                    "",
                                ),
                            },
                        )
                    )

    return resources
