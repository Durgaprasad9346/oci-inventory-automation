import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_object_storage(config):
    """
    Collect all OCI Object Storage buckets across:
        - All subscribed regions
        - All accessible compartments

    Collects:
        - Resource information
        - Creation date
        - OCI Defined Tags
        - Existing Object Storage details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing Object Storage region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        object_storage_client = oci.object_storage.ObjectStorageClient(
            region_config
        )

        # -----------------------------------------------------
        # Get Object Storage namespace
        # -----------------------------------------------------

        try:

            namespace = (
                object_storage_client.get_namespace().data
            )

        except Exception as error:

            print(
                f"    ERROR getting Object Storage namespace "
                f"for region {region}: {error}"
            )

            continue

        for compartment in compartments:

            try:

                buckets = (
                    oci.pagination.list_call_get_all_results(
                        object_storage_client.list_buckets,
                        namespace_name=namespace,
                        compartment_id=compartment["id"],
                    )
                )

                for bucket in buckets.data:

                    resources.append(
                        Resource(
                            service="Object Storage",
                            resource_type="Bucket",
                            name=bucket.name,
                            ocid=getattr(
                                bucket,
                                "id",
                                "",
                            ),
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=getattr(
                                bucket,
                                "time_created",
                                "",
                            ),

                            # -----------------------------------------
                            # Creation Date
                            # -----------------------------------------

                            time_created=getattr(
                                bucket,
                                "time_created",
                                None,
                            ),

                            # -----------------------------------------
                            # OCI Defined Tags
                            # -----------------------------------------

                            defined_tags=getattr(
                                bucket,
                                "defined_tags",
                                None,
                            ),

                            # -----------------------------------------
                            # Existing Object Storage details
                            # -----------------------------------------

                            details={
                                "namespace": namespace,
                                "compartment_id": getattr(
                                    bucket,
                                    "compartment_id",
                                    compartment["id"],
                                ),
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
                                "public_access_type": getattr(
                                    bucket,
                                    "public_access_type",
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

            except Exception as error:

                print(
                    f"    ERROR collecting Object Storage "
                    f"from compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
