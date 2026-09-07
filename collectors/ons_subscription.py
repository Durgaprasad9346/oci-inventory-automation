import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_ons_subscriptions(config):
    """
    Collect OCI Notifications Service subscriptions.

    Topics are collected using:
        NotificationControlPlaneClient

    Subscriptions are collected using:
        NotificationDataPlaneClient
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

        # -------------------------------------------------------------
        # IMPORTANT:
        # Topics -> Control Plane
        # Subscriptions -> Data Plane
        # -------------------------------------------------------------

        control_client = oci.ons.NotificationControlPlaneClient(
            region_config
        )

        data_client = oci.ons.NotificationDataPlaneClient(
            region_config
        )

        for compartment in compartments:

            compartment_id = compartment["id"]
            compartment_name = compartment["name"]

            # ---------------------------------------------------------
            # TOPICS
            # ---------------------------------------------------------

            try:

                topics = oci.pagination.list_call_get_all_results(
                    control_client.list_topics,
                    compartment_id=compartment_id,
                )

            except Exception as error:

                print(
                    f"    ERROR collecting ONS Topics from compartment "
                    f"{compartment_name}: {error}"
                )

                continue

            # ---------------------------------------------------------
            # EACH TOPIC
            # ---------------------------------------------------------

            for topic in topics.data:

                topic_id = getattr(
                    topic,
                    "topic_id",
                    None,
                )

                if not topic_id:
                    topic_id = getattr(
                        topic,
                        "id",
                        "",
                    )

                topic_name = getattr(
                    topic,
                    "name",
                    "",
                )

                if not topic_id:
                    continue

                # -----------------------------------------------------
                # SUBSCRIPTIONS
                # -----------------------------------------------------

                try:

                    subscriptions = (
                        oci.pagination.list_call_get_all_results(
                            data_client.list_subscriptions,
                            compartment_id=compartment_id,
                            topic_id=topic_id,
                        )
                    )

                except Exception as error:

                    print(
                        f"    ERROR collecting subscriptions for topic "
                        f"{topic_name}: {error}"
                    )

                    continue

                # -----------------------------------------------------
                # EACH SUBSCRIPTION
                # -----------------------------------------------------

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
                            compartment_id=compartment_id,
                            compartment_name=compartment_name,
                            region=region,
                            state=getattr(
                                subscription,
                                "lifecycle_state",
                                "",
                            ),
                            time_created=getattr(
                                subscription,
                                "time_created",
                                None,
                            ),
                            defined_tags=getattr(
                                subscription,
                                "defined_tags",
                                None,
                            ),
                            freeform_tags=getattr(
                                subscription,
                                "freeform_tags",
                                None,
                            ),
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
PY
