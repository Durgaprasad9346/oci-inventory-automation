import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_object_storage(config):
    """
    Collect all OCI Object Storage buckets across
    all subscribed regions and accessible compartments.
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(f"  Processing Object Storage region: {region}")

        region_config = config.copy()
        region_config["region"] = region

        object_storage_client = oci.object_storage.ObjectStorageClient(
            region_config
        )

        # Object Storage namespace is tenancy-wide.
        namespace = object_storage_client.get_namespace().data

        for compartment in compartments:

            buckets = oci.pagination.list_call_get_all_results(
                object_storage_client.list_buckets,
                namespace_name=namespace,
                compartment_id=compartment["id"],
            )

            for bucket in buckets.data:

                resources.append(
                    Resource(
                        service="Object Storage",
                        resource_type="Bucket",
                        name=bucket.name,
                        ocid=getattr(bucket, "id", ""),
                        compartment_id=compartment["id"],
                        compartment_name=compartment["name"],
                        region=region,
                        state="ACTIVE",
                        details={
                            "namespace": namespace,
                            "storage_tier": getattr(
                                bucket,
                                "storage_tier",
                                "",
                            ),
                            "versioning": getattr(
                                bucket,
                                "versioning",
                                "",
                            ),
                            "object_events_enabled": getattr(
                                bucket,
                                "object_events_enabled",
                                "",
                            ),
                            "auto_tiering": getattr(
                                bucket,
                                "auto_tiering",
                                "",
                            ),
                            "kms_key_id": getattr(
                                bucket,
                                "kms_key_id",
                                "",
                            ),
                        },
                    )
                )

    return resources
