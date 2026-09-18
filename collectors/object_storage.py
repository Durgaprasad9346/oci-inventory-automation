import oci

from utils.compartments import get_compartments
from utils.regions import get_regions


def _get(obj, name, default=None):
    if obj is None:
        return default

    try:
        if isinstance(obj, dict):
            return obj.get(name, default)

        return getattr(obj, name, default)

    except Exception:
        return default


def _safe_value(value):
    if value is None:
        return ""

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, dict):
        return {
            str(key): _safe_value(val)
            for key, val in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            _safe_value(item)
            for item in value
        ]

    try:
        if hasattr(value, "to_dict"):
            return _safe_value(value.to_dict())
    except Exception:
        pass

    return str(value)


def collect_object_storage(config):
    """
    Collect OCI Object Storage Buckets.

    Collects:

      - Bucket OCID
      - Bucket Name
      - Namespace
      - Region
      - Compartment
      - Creation Date
      - Storage Tier
      - Versioning
      - Object Events
      - Public Access Type
      - Auto Tiering
      - Object Count
      - Stored Size
      - KMS Key
      - Defined Tags
      - Freeform Tags
    """

    resources = []

    # ============================================================
    # USE COMMON REGION / COMPARTMENT DISCOVERY
    # ============================================================

    regions = get_regions(config)
    compartments = get_compartments(config)

    if not regions:
        print(
            "  ERROR: No regions found for Object Storage."
        )
        return resources

    if not compartments:
        print(
            "  ERROR: No compartments found for Object Storage."
        )
        return resources

    # ============================================================
    # REGIONS
    # ============================================================

    for region in regions:

        print(
            f"  Processing Object Storage region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        # ========================================================
        # OBJECT STORAGE CLIENT
        # ========================================================

        try:

            object_storage_client = (
                oci.object_storage.ObjectStorageClient(
                    region_config
                )
            )

        except Exception as error:

            print(
                f"  ERROR initializing Object Storage "
                f"client for region {region}: {error}"
            )

            continue

        # ========================================================
        # NAMESPACE
        # ========================================================

        try:

            namespace_response = (
                object_storage_client.get_namespace()
            )

            namespace = namespace_response.data

            if not namespace:

                print(
                    f"    WARNING: Object Storage namespace "
                    f"is empty in region {region}"
                )

                continue

            print(
                f"    Object Storage namespace: {namespace}"
            )

        except Exception as error:

            print(
                f"    ERROR getting Object Storage namespace "
                f"in region {region}: {error}"
            )

            continue

        # ========================================================
        # COMPARTMENTS
        # ========================================================

        for compartment in compartments:

            compartment_id = _get(
                compartment,
                "id",
                compartment
                if isinstance(compartment, str)
                else None,
            )

            compartment_name = _get(
                compartment,
                "name",
                compartment_id,
            )

            if not compartment_id:
                continue

            print(
                f"    Processing Object Storage compartment: "
                f"{compartment_name}"
            )

            # ====================================================
            # LIST BUCKETS
            # ====================================================

            try:

                response = (
                    oci.pagination.list_call_get_all_results(
                        object_storage_client.list_buckets,
                        namespace_name=namespace,
                        compartment_id=compartment_id,
                        fields=["tags"],
                    )
                )

                buckets = response.data

            except Exception as error:

                print(
                    f"      ERROR collecting Object Storage "
                    f"buckets from compartment "
                    f"{compartment_name}: {error}"
                )

                continue

            if not buckets:

                continue

            print(
                f"      Found {len(buckets)} bucket(s)"
            )

            # ====================================================
            # PROCESS BUCKETS
            # ====================================================

            for bucket in buckets:

                try:

                    bucket_name = _get(
                        bucket,
                        "name",
                        "",
                    )

                    bucket_id = _get(
                        bucket,
                        "id",
                        "",
                    )

                    # =================================================
                    # GET BUCKET DETAILS
                    # =================================================

                    bucket_details = bucket

                    if bucket_name:

                        try:

                            detail_response = (
                                object_storage_client.get_bucket(
                                    namespace_name=namespace,
                                    bucket_name=bucket_name,
                                )
                            )

                            bucket_details = (
                                detail_response.data
                            )

                        except Exception as detail_error:

                            print(
                                f"        WARNING: Could not get "
                                f"details for bucket "
                                f"{bucket_name}: "
                                f"{detail_error}"
                            )

                    # =================================================
                    # BASIC DETAILS
                    # =================================================

                    time_created = _get(
                        bucket_details,
                        "time_created",
                        _get(
                            bucket,
                            "time_created",
                            None,
                        ),
                    )

                    storage_tier = _get(
                        bucket_details,
                        "storage_tier",
                        _get(
                            bucket,
                            "storage_tier",
                            "",
                        ),
                    )

                    versioning = _get(
                        bucket_details,
                        "versioning",
                        _get(
                            bucket,
                            "versioning",
                            "",
                        ),
                    )

                    object_events_enabled = _get(
                        bucket_details,
                        "object_events_enabled",
                        _get(
                            bucket,
                            "object_events_enabled",
                            False,
                        ),
                    )

                    public_access_type = _get(
                        bucket_details,
                        "public_access_type",
                        _get(
                            bucket,
                            "public_access_type",
                            "",
                        ),
                    )

                    auto_tiering = _get(
                        bucket_details,
                        "auto_tiering",
                        _get(
                            bucket,
                            "auto_tiering",
                            "",
                        ),
                    )

                    etag = _get(
                        bucket_details,
                        "etag",
                        _get(
                            bucket,
                            "etag",
                            "",
                        ),
                    )

                    kms_key_id = _get(
                        bucket_details,
                        "kms_key_id",
                        _get(
                            bucket,
                            "kms_key_id",
                            "",
                        ),
                    )

                    # =================================================
                    # OBJECT COUNT
                    # =================================================

                    approximate_count = _get(
                        bucket_details,
                        "approximate_count",
                        _get(
                            bucket,
                            "approximate_count",
                            None,
                        ),
                    )

                    # =================================================
                    # STORAGE SIZE
                    # =================================================

                    approximate_size = _get(
                        bucket_details,
                        "approximate_size",
                        _get(
                            bucket,
                            "approximate_size",
                            None,
                        ),
                    )

                    size_gb = ""

                    try:

                        if approximate_size is not None:

                            size_gb = (
                                float(approximate_size)
                                / (1024 ** 3)
                            )

                    except Exception:

                        size_gb = ""

                    # =================================================
                    # TAGS
                    # =================================================

                    defined_tags = _get(
                        bucket_details,
                        "defined_tags",
                        _get(
                            bucket,
                            "defined_tags",
                            {},
                        ),
                    ) or {}

                    freeform_tags = _get(
                        bucket_details,
                        "freeform_tags",
                        _get(
                            bucket,
                            "freeform_tags",
                            {},
                        ),
                    ) or {}

                    # =================================================
                    # RESOURCE
                    # =================================================

                    resource = {

                        "service":
                            "Object Storage",

                        "resource_type":
                            "Bucket",

                        "id":
                            bucket_id or bucket_name,

                        "ocid":
                            bucket_id or bucket_name,

                        "name":
                            bucket_name,

                        "display_name":
                            bucket_name,

                        "bucket_name":
                            bucket_name,

                        "namespace":
                            namespace,

                        "region":
                            region,

                        "compartment_id":
                            compartment_id,

                        "compartment_name":
                            compartment_name,

                        # -----------------------------------------
                        # TIME
                        # -----------------------------------------

                        "time_created":
                            time_created,

                        # -----------------------------------------
                        # STORAGE
                        # -----------------------------------------

                        "storage_tier":
                            storage_tier,

                        "versioning":
                            versioning,

                        "object_count":
                            approximate_count,

                        "objects_count":
                            approximate_count,

                        "stored_size_bytes":
                            approximate_size,

                        "size_bytes":
                            approximate_size,

                        "approximate_size_in_bytes":
                            approximate_size,

                        "size_gb":
                            size_gb,

                        # -----------------------------------------
                        # FEATURES
                        # -----------------------------------------

                        "object_events_enabled":
                            object_events_enabled,

                        "public_access_type":
                            public_access_type,

                        "auto_tiering":
                            auto_tiering,

                        "etag":
                            etag,

                        # -----------------------------------------
                        # ENCRYPTION
                        # -----------------------------------------

                        "kms_key_id":
                            kms_key_id,

                        "kms_key_ocid":
                            kms_key_id,

                        # -----------------------------------------
                        # TAGS
                        # -----------------------------------------

                        "defined_tags":
                            _safe_value(
                                defined_tags
                            ),

                        "freeform_tags":
                            _safe_value(
                                freeform_tags
                            ),
                    }

                    resources.append(
                        resource
                    )

                except Exception as error:

                    print(
                        f"      ERROR processing Object Storage "
                        f"bucket "
                        f"{_get(bucket, 'name', '')}: "
                        f"{error}"
                    )

    # ============================================================
    # SUMMARY
    # ============================================================

    print(
        f"Object Storage: {len(resources)} resources found"
    )

    return resources
