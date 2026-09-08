import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def _get(obj, name, default=None):
    """
    Safely get an attribute from an OCI SDK object or dictionary.
    """
    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(name, default)

    return getattr(obj, name, default)


def _safe_dict(obj):
    """
    Safely convert OCI SDK objects into dictionaries.
    """
    if obj is None:
        return {}

    if isinstance(obj, dict):
        return obj

    try:
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
    except Exception:
        pass

    return {}


def _safe_value(value):
    """
    Convert OCI SDK objects/lists/dicts into Excel-safe values.
    Prevents openpyxl errors caused by OCI SDK objects.
    """

    if value is None:
        return ""

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, dict):
        result = {}

        for key, val in value.items():
            result[str(key)] = _safe_value(val)

        return result

    if isinstance(value, (list, tuple)):
        return [
            _safe_value(item)
            for item in value
        ]

    try:
        if hasattr(value, "to_dict"):
            return _safe_value(
                value.to_dict()
            )
    except Exception:
        pass

    return str(value)


def collect_block_volume(config):
    """
    Collect OCI Block Volumes across:

        - All subscribed regions
        - All accessible compartments

    Important inventory details:

        - Display Name
        - OCID
        - Size in GB
        - Size in MB
        - Volume Type
        - VPUs per GB
        - Performance
        - Lifecycle State
        - Availability Domain
        - Compartment
        - Time Created
        - Encryption
        - KMS Key
        - Source Volume
        - Source Type
        - Backup Policy
        - Volume Group
        - Replica information
        - Read Only
        - Shareable
        - Hydrated
        - Auto Tune
        - Tags
    """

    resources = []

    compartments = get_compartments(config)
    regions = get_regions(config)

    for region in regions:

        print(
            f"  Processing Block Volume region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        try:

            blockstorage_client = (
                oci.core.BlockstorageClient(
                    region_config
                )
            )

        except Exception as error:

            print(
                f"    ERROR creating Block Storage client "
                f"for region {region}: {error}"
            )

            continue

        for compartment in compartments:

            compartment_id = _get(
                compartment,
                "id",
                ""
            )

            compartment_name = _get(
                compartment,
                "name",
                compartment_id
            )

            if not compartment_id:
                continue

            try:

                response = (
                    oci.pagination.list_call_get_all_results(
                        blockstorage_client.list_volumes,
                        compartment_id=compartment_id
                    )
                )

                volumes = response.data

            except Exception as error:

                print(
                    f"    ERROR collecting Block Volumes "
                    f"from compartment "
                    f"{compartment_name}: {error}"
                )

                continue

            for volume in volumes:

                try:

                    volume_id = _get(
                        volume,
                        "id",
                        ""
                    )

                    display_name = _get(
                        volume,
                        "display_name",
                        ""
                    )

                    lifecycle_state = _get(
                        volume,
                        "lifecycle_state",
                        ""
                    )

                    availability_domain = _get(
                        volume,
                        "availability_domain",
                        ""
                    )

                    size_in_gbs = _get(
                        volume,
                        "size_in_gbs",
                        ""
                    )

                    size_in_mbs = _get(
                        volume,
                        "size_in_mbs",
                        ""
                    )

                    vpus_per_gb = _get(
                        volume,
                        "vpus_per_gb",
                        ""
                    )

                    volume_type = _get(
                        volume,
                        "volume_type",
                        ""
                    )

                    time_created = _get(
                        volume,
                        "time_created",
                        None
                    )

                    is_hydrated = _get(
                        volume,
                        "is_hydrated",
                        ""
                    )

                    is_reservable = _get(
                        volume,
                        "is_reservable",
                        ""
                    )

                    is_read_only = _get(
                        volume,
                        "is_read_only",
                        ""
                    )

                    is_volume_group_clone = _get(
                        volume,
                        "is_volume_group_clone",
                        ""
                    )

                    is_auto_tune_enabled = _get(
                        volume,
                        "is_auto_tune_enabled",
                        ""
                    )

                    kms_key_id = _get(
                        volume,
                        "kms_key_id",
                        ""
                    )

                    volume_group_id = _get(
                        volume,
                        "volume_group_id",
                        ""
                    )

                    source_details = _get(
                        volume,
                        "source_details",
                        None
                    )

                    block_volume_replicas = _get(
                        volume,
                        "block_volume_replicas",
                        None
                    )

                    autotune_policies = _get(
                        volume,
                        "autotune_policies",
                        None
                    )

                    backup_policy_id = _get(
                        volume,
                        "backup_policy_id",
                        ""
                    )

                    freeform_tags = _get(
                        volume,
                        "freeform_tags",
                        {}
                    )

                    defined_tags = _get(
                        volume,
                        "defined_tags",
                        {}
                    )

                    # ------------------------------------------------
                    # Create common Resource object
                    # ------------------------------------------------

                    resource = Resource(

                        service="Block Storage",

                        resource_type="Block Volume",

                        name=display_name,

                        ocid=volume_id,

                        compartment_id=compartment_id,

                        compartment_name=compartment_name,

                        region=region,

                        state=lifecycle_state,

                        time_created=time_created,

                        defined_tags=_safe_value(
                            defined_tags
                        ),

                        details={

                            # ----------------------------------------
                            # Basic information
                            # ----------------------------------------

                            "display_name":
                                display_name,

                            "volume_id":
                                volume_id,

                            "availability_domain":
                                availability_domain,

                            "lifecycle_state":
                                lifecycle_state,

                            "size_in_gbs":
                                size_in_gbs,

                            "size_in_mbs":
                                size_in_mbs,

                            "volume_type":
                                volume_type,

                            "vpus_per_gb":
                                vpus_per_gb,

                            "performance_vpus_per_gb":
                                vpus_per_gb,

                            # ----------------------------------------
                            # Creation
                            # ----------------------------------------

                            "time_created":
                                time_created,

                            # ----------------------------------------
                            # Encryption
                            # ----------------------------------------

                            "kms_key_id":
                                kms_key_id,

                            # ----------------------------------------
                            # Volume Group
                            # ----------------------------------------

                            "volume_group_id":
                                volume_group_id,

                            "is_volume_group_clone":
                                is_volume_group_clone,

                            # ----------------------------------------
                            # Source
                            # ----------------------------------------

                            "source_details":
                                _safe_value(
                                    source_details
                                ),

                            # ----------------------------------------
                            # Backup
                            # ----------------------------------------

                            "backup_policy_id":
                                backup_policy_id,

                            # ----------------------------------------
                            # Replica
                            # ----------------------------------------

                            "block_volume_replicas":
                                _safe_value(
                                    block_volume_replicas
                                ),

                            # ----------------------------------------
                            # Performance / Auto Tune
                            # ----------------------------------------

                            "is_auto_tune_enabled":
                                is_auto_tune_enabled,

                            "autotune_policies":
                                _safe_value(
                                    autotune_policies
                                ),

                            # ----------------------------------------
                            # Volume properties
                            # ----------------------------------------

                            "is_hydrated":
                                is_hydrated,

                            "is_reservable":
                                is_reservable,

                            "is_read_only":
                                is_read_only,

                            # ----------------------------------------
                            # Tags
                            # ----------------------------------------

                            "freeform_tags":
                                _safe_value(
                                    freeform_tags
                                ),

                            "defined_tags":
                                _safe_value(
                                    defined_tags
                                ),
                        }
                    )

                    resources.append(
                        resource
                    )

                except Exception as error:

                    print(
                        f"    ERROR processing Block Volume "
                        f"{_get(volume, 'display_name', '')}: "
                        f"{error}"
                    )

    return resources
