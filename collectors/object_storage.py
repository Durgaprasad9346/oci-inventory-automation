import oci


def collect_object_storage(config):
    """
    Collect OCI Object Storage buckets across all configured
    regions and compartments.

    Returns:
        list: Object Storage bucket inventory records.
    """

    resources = []

    try:
        regions = config.get("regions", [])
        compartments = config.get("compartments", [])

        for region in regions:

            print(
                f"  Processing Object Storage region: {region}"
            )

            try:

                object_storage_client = oci.object_storage.ObjectStorageClient(
                    config,
                    region=region
                )

                # Object Storage namespace is tenancy-level.
                namespace_response = (
                    object_storage_client.get_namespace()
                )

                namespace = namespace_response.data

                for compartment in compartments:

                    compartment_id = compartment.get("id")

                    compartment_name = compartment.get(
                        "name",
                        compartment_id
                    )

                    try:

                        response = (
                            object_storage_client.list_buckets(
                                namespace_name=namespace,
                                compartment_id=compartment_id
                            )
                        )

                        for bucket in response.data:

                            resources.append(
                                {
                                    "service": "Object Storage",
                                    "resource_type": "Bucket",

                                    "id": getattr(
                                        bucket,
                                        "id",
                                        ""
                                    ),

                                    "name": getattr(
                                        bucket,
                                        "name",
                                        ""
                                    ),

                                    "display_name": getattr(
                                        bucket,
                                        "name",
                                        ""
                                    ),

                                    "namespace": namespace,

                                    "compartment_id": getattr(
                                        bucket,
                                        "compartment_id",
                                        compartment_id
                                    ),

                                    "compartment_name": (
                                        compartment_name
                                    ),

                                    "bucket_name": getattr(
                                        bucket,
                                        "name",
                                        ""
                                    ),

                                    "storage_tier": getattr(
                                        bucket,
                                        "storage_tier",
                                        ""
                                    ),

                                    "access_type": getattr(
                                        bucket,
                                        "public_access_type",
                                        ""
                                    ),

                                    "public_access_type": getattr(
                                        bucket,
                                        "public_access_type",
                                        ""
                                    ),

                                    "versioning": getattr(
                                        bucket,
                                        "versioning",
                                        ""
                                    ),

                                    "auto_tiering": getattr(
                                        bucket,
                                        "auto_tiering",
                                        ""
                                    ),

                                    "object_events_enabled": getattr(
                                        bucket,
                                        "object_events_enabled",
                                        None
                                    ),

                                    "kms_key_id": getattr(
                                        bucket,
                                        "kms_key_id",
                                        ""
                                    ),

                                    "created_by": getattr(
                                        bucket,
                                        "created_by",
                                        ""
                                    ),

                                    "time_created": getattr(
                                        bucket,
                                        "time_created",
                                        None
                                    ),

                                    "etag": getattr(
                                        bucket,
                                        "etag",
                                        ""
                                    ),

                                    "freeform_tags": getattr(
                                        bucket,
                                        "freeform_tags",
                                        {}
                                    ),

                                    "defined_tags": getattr(
                                        bucket,
                                        "defined_tags",
                                        {}
                                    ),
                                }
                            )

                    except Exception as e:

                        print(
                            f"    ERROR collecting Object Storage "
                            f"from compartment "
                            f"{compartment_name}: {e}"
                        )

            except Exception as e:

                print(
                    f"  ERROR collecting Object Storage "
                    f"from region {region}: {e}"
                )

    except Exception as e:

        print(
            f"ERROR collecting Object Storage: {e}"
        )

    return resources
