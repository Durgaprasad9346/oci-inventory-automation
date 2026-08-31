import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_streaming(config):
    """
    Collect all OCI Streaming Streams across:
        - All subscribed regions
        - All accessible compartments

    Collects:
        - Resource information
        - Creation date
        - OCI Defined Tags
        - Existing Streaming details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing Streaming region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        stream_client = oci.streaming.StreamAdminClient(
            region_config
        )

        for compartment in compartments:

            try:

                streams = (
                    oci.pagination.list_call_get_all_results(
                        stream_client.list_streams,
                        compartment_id=compartment["id"],
                    )
                )

                for stream in streams.data:

                    resources.append(
                        Resource(
                            service="Streaming",
                            resource_type="Stream",
                            name=getattr(
                                stream,
                                "name",
                                "",
                            ),
                            ocid=getattr(
                                stream,
                                "id",
                                "",
                            ),
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=getattr(
                                stream,
                                "lifecycle_state",
                                "",
                            ),

                            # -----------------------------------------
                            # Creation Date
                            # -----------------------------------------

                            time_created=getattr(
                                stream,
                                "time_created",
                                None,
                            ),

                            # -----------------------------------------
                            # OCI Defined Tags
                            # -----------------------------------------

                            defined_tags=getattr(
                                stream,
                                "defined_tags",
                                None,
                            ),

                            # -----------------------------------------
                            # Existing Streaming details
                            # -----------------------------------------

                            details={
                                "partitions": getattr(
                                    stream,
                                    "partitions",
                                    "",
                                ),
                                "retention_in_hours": getattr(
                                    stream,
                                    "retention_in_hours",
                                    "",
                                ),
                                "messages_endpoint": getattr(
                                    stream,
                                    "messages_endpoint",
                                    "",
                                ),
                                "stream_pool_id": getattr(
                                    stream,
                                    "stream_pool_id",
                                    "",
                                ),
                                "compartment_id": getattr(
                                    stream,
                                    "compartment_id",
                                    compartment["id"],
                                ),
                            },
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR collecting Streaming "
                    f"from compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
