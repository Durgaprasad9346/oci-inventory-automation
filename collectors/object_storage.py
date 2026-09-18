import oci


def _get(obj, name, default=None):
    if obj is None:
        return default
    try:
        if isinstance(obj, dict):
            return obj.get(name, default)
        return getattr(obj, name, default)
    except Exception:
        return default


def _safe_region_client(config, region):
    client = oci.object_storage.ObjectStorageClient(
        config,
        region=region,
    )
    return client


def collect_object_storage(config):
    """
    Collect OCI Object Storage buckets across configured regions
    and compartments.

    Collects:
      - Bucket OCID/name
      - Namespace
      - Region
      - Compartment
      - Creation date
      - Storage tier
      - Versioning
      - Object Events
      - Public access type
      - Auto Tiering
      - ETag
      - KMS key
      - Approximate object count
      - Approximate stored size
      - Defined/freeform tags

    Important:
      Object Storage namespace is tenancy-wide. The namespace is obtained
      once per region/client and then used with list_buckets().
    """

    resources = []

    regions = config.get("regions", [])
    compartments = config.get("compartments", [])

    for region in regions:
        print(f"  Processing Object Storage region: {region}")

        try:
            client = _safe_region_client(config, region)

            # Object Storage namespace is unique to the tenancy.
            namespace = client.get_namespace().data

            if not namespace:
                print(
                    f"    WARNING: Object Storage namespace is empty "
                    f"in region {region}"
                )
                continue

        except Exception as exc:
            print(
                f"  ERROR initializing Object Storage in region "
                f"{region}: {exc}"
            )
            continue

        for compartment in compartments:
            compartment_id = _get(
                compartment,
                "id",
                compartment if isinstance(compartment, str) else None,
            )

            compartment_name = _get(
                compartment,
                "name",
                "",
            )

            if not compartment_id:
                continue

            try:
                response = oci.pagination.list_call_get_all_results(
                    client.list_buckets,
                    namespace_name=namespace,
                    compartment_id=compartment_id,
                    fields=["tags"],
                )

                buckets = response.data

            except Exception as exc:
                print(
                    f"    ERROR collecting Object Storage buckets "
                    f"from compartment {compartment_name}: {exc}"
                )
                continue

            for bucket in buckets:
                try:
                    bucket_name = _get(bucket, "name", "")
                    bucket_id = _get(bucket, "id", "")

                    # BucketSummary normally does not expose all details.
                    # Get the full bucket when possible.
                    bucket_details = bucket

                    try:
                        detail_response = client.get_bucket(
                            namespace_name=namespace,
                            bucket_name=bucket_name,
                        )
                        bucket_details = detail_response.data
                    except Exception as exc:
                        print(
                            f"      WARNING: Could not get details for "
                            f"bucket {bucket_name}: {exc}"
                        )

                    approximate_count = _get(
                        bucket_details,
                        "approximate_count",
                        _get(bucket, "approximate_count", None),
                    )

                    approximate_size = _get(
                        bucket_details,
                        "approximate_size",
                        _get(bucket, "approximate_size", None),
                    )

                    defined_tags = _get(
                        bucket_details,
                        "defined_tags",
                        _get(bucket, "defined_tags", {}),
                    ) or {}

                    freeform_tags = _get(
                        bucket_details,
                        "freeform_tags",
                        _get(bucket, "freeform_tags", {}),
                    ) or {}

                    resource = {
                        "service": "Object Storage",
                        "resource_type": "Bucket",

                        "id": bucket_id or bucket_name,
                        "ocid": bucket_id or bucket_name,

                        "name": bucket_name,
                        "display_name": bucket_name,
                        "bucket_name": bucket_name,

                        "namespace": namespace,

                        "region": region,

                        "compartment_id": compartment_id,
                        "compartment_name": compartment_name,

                        "time_created": _get(
                            bucket_details,
                            "time_created",
                            _get(bucket, "time_created", None),
                        ),

                        "storage_tier": _get(
                            bucket_details,
                            "storage_tier",
                            _get(bucket, "storage_tier", ""),
                        ),

                        "versioning": _get(
                            bucket_details,
                            "versioning",
                            _get(bucket, "versioning", ""),
                        ),

                        "object_events_enabled": _get(
                            bucket_details,
                            "object_events_enabled",
                            _get(bucket, "object_events_enabled", False),
                        ),

                        "public_access_type": _get(
                            bucket_details,
                            "public_access_type",
                            _get(bucket, "public_access_type", ""),
                        ),

                        "auto_tiering": _get(
                            bucket_details,
                            "auto_tiering",
                            _get(bucket, "auto_tiering", ""),
                        ),

                        "etag": _get(
                            bucket_details,
                            "etag",
                            _get(bucket, "etag", ""),
                        ),

                        "kms_key_id": _get(
                            bucket_details,
                            "kms_key_id",
                            _get(bucket, "kms_key_id", ""),
                        ),

                        "object_count": approximate_count,
                        "objects_count": approximate_count,

                        "stored_size_bytes": approximate_size,
                        "size_bytes": approximate_size,
                        "approximate_size_in_bytes": approximate_size,

                        "defined_tags": defined_tags,
                        "freeform_tags": freeform_tags,
                    }

                    resources.append(resource)

                except Exception as exc:
                    print(
                        f"    ERROR processing Object Storage bucket "
                        f"{_get(bucket, 'name', '')}: {exc}"
                    )

    print(
        f"Object Storage: {len(resources)} resources found"
    )

    return resources
