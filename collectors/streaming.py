import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_streaming(config):
    """
    Collect all OCI Streaming streams across all subscribed
    regions and accessible compartments.
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(f"  Processing Streaming region: {region}")

        region_config = config.copy()
        region_config["region"] = region

        streaming_client = oci.streaming.StreamAdminClient(
            region_config
        )

        for compartment in compartments:

            streams = oci.pagination.list_call_get_all_results(
                streaming_client.list_streams,
                compartment_id=compartment["id"],
            )

            for stream in streams.data:

                resources.append(
                    Resource(
                        service="Streaming",
                        resource_type="Stream",
                        name=stream.name,
                        ocid=stream.id,
                        compartment_id=compartment["id"],
                        compartment_name=compartment["name"],
                        region=region,
                        state=getattr(
                            stream,
                            "lifecycle_state",
                            "",
                        ),
                        details={
                            "partitions": getattr(
                                stream,
                                "partitions",
                                "",
                            ),
                            "messages_endpoint": getattr(
                                stream,
                                "messages_endpoint",
                                "",
                            ),
                            "retention_in_hours": getattr(
                                stream,
                                "retention_in_hours",
                                "",
                            ),
                            "stream_pool_id": getattr(
                                stream,
                                "stream_pool_id",
                                "",
                            ),
                            "time_created": getattr(
                                stream,
                                "time_created",
                                "",
                            ),
                        },
                    )
                )

    return resources
