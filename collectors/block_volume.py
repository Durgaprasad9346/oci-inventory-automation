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


def _safe_value(value):
    """
    Convert OCI SDK objects/lists/dicts into Excel-safe values.
    """

    if value is None:
        return ""

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, dict):
        return {
            str(k): _safe_value(v)
            for k, v in value.items()
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


def collect_block_volume(config):
    """
    Collect OCI Block Volumes across all regions and compartments.
    """

    resources = []

    compartments = get_compartments(config)
    regions = get_regions(config)

    for region in regions:

        print(f"  Processing Block Volume region: {region}")

        region_config = config.copy()
        region_config["region"] = region

        try:
            blockstorage_client = oci.core.BlockstorageClient(
                region_config
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
                response = oci.pagination.list_call_get_all_results(
                    blockstorage_client.list_volumes,
                    compartment_id=compartment_id
                )

                volumes = response.data

            except Exception as error:

                print(
                    f"    ERROR collecting Block Volumes "
                    f"from compartment {compartment_name}: {error}"
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

                    # ==================================================
                    # GET COMPLETE VOLUME DETAILS
                    # ==================================================

                    volume_details = volume

                    if volume_id:
                        try:
                            detail_response = blockstorage_client.get_volume(
                                volume_id
                            )
                            volume_details = detail_response.data
                        except Exception as detail_error:
                            print(
                                f"      WARNING getting details for "
                                f"{display_name}: {detail_error}"
                            )

                    # ==================================================
                    # BASIC
                    # ==================================================

                    lifecycle_state = _get(
                        volume_details,
                        "lifecycle_state",
                        _get(volume, "lifecycle_state", "")
                    )

                    availability_domain = _get(
                        volume_details,
                        "availability_domain",
                        _get(volume, "availability_domain", "")
                    )

                    size_in_gbs = _get(
                        volume_details,
                        "size_in_gbs",
                        _get(volume, "size_in_gbs", "")
                    )

                    size_in_mbs = _get(
                        volume_details,
                        "size_in_mbs",
                        _get(volume, "size_in_mbs", "")
                    )

                    volume_type = _get(
                        volume_details,
                        "volume_type",
                        _get(volume, "volume_type", "")
                    )

                    # ==================================================
                    # VPU FIX
                    # ==================================================

                    vpus_per_gb = _get(
                        volume_details,
                        "vpus_per_gb",
                        None
                    )

                    if vpus_per_gb is None:
                        vpus_per_gb = _get(
                            volume,
                            "vpus_per_gb",
                            ""
                        )

                    # ==================================================
                    # OTHER DETAILS
                    # ==================================================

                    time_created = _get(
                        volume_details,
                        "time_created",
                        _get(volume, "time_created", None)
                    )

                    is_hydrated = _get(
                        volume_details,
                        "is_hydrated",
                        _get(volume, "is_hydrated", "")
                    )

                    is_reservable = _get(
                        volume_details,
                        "is_reservable",
                        _get(volume, "is_reservable", "")
                    )

                    is_read_only = _get(
                        volume_details,
                        "is_read_only",
                        _get(volume, "is_read_only", "")
                    )

                    is_volume_group_clone = _get(
                        volume_details,
                        "is_volume_group_clone",
                        _get(volume, "is_volume_group_clone", "")
                    )

                    is_auto_tune_enabled = _get(
                        volume_details,
                        "is_auto_tune_enabled",
                        _get(volume, "is_auto_tune_enabled", "")
                    )

                    kms_key_id = _get(
                        volume_details,
                        "kms_key_id",
                        _get(volume, "kms_key_id", "")
                    )

                    volume_group_id = _get(
                        volume_details,
                        "volume_group_id",
                        _get(volume, "volume_group_id", "")
                    )

                    source_details = _get(
                        volume_details,
                        "source_details",
                        _get(volume, "source_details", None)
                    )

                    block_volume_replicas = _get(
                        volume_details,
                        "block_volume_replicas",
                        _get(volume, "block_volume_replicas", None)
                    )

                    autotune_policies = _get(
                        volume_details,
                        "autotune_policies",
                        _get(volume, "autotune_policies", None)
                    )

                    backup_policy_id = _get(
                        volume_details,
                        "backup_policy_id",
                        _get(volume, "backup_policy_id", "")
                    )

                    freeform_tags = _get(
                        volume_details,
                        "freeform_tags",
                        _get(volume, "freeform_tags", {})
                    ) or {}

                    defined_tags = _get(
                        volume_details,
                        "defined_tags",
                        _get(volume, "defined_tags", {})
                    ) or {}

                    # ==================================================
                    # RESOURCE
                    # ==================================================

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
                        defined_tags=_safe_value(defined_tags),
                        details={
                            "display_name": display_name,
                            "volume_id": volume_id,
                            "availability_domain": availability_domain,
                            "lifecycle_state": lifecycle_state,
                            "size_in_gbs": size_in_gbs,
                            "size_in_mbs": size_in_mbs,
                            "volume_type": volume_type,

                            "vpus_per_gb": vpus_per_gb,
                            "performance_vpus_per_gb": vpus_per_gb,

                            "time_created": time_created,
                            "kms_key_id": kms_key_id,
                            "volume_group_id": volume_group_id,
                            "is_volume_group_clone": is_volume_group_clone,

                            "source_details": _safe_value(source_details),
                            "backup_policy_id": backup_policy_id,
                            "block_volume_replicas": _safe_value(
                                block_volume_replicas
                            ),

                            "is_auto_tune_enabled": is_auto_tune_enabled,
                            "autotune_policies": _safe_value(
                                autotune_policies
                            ),

                            "is_hydrated": is_hydrated,
                            "is_reservable": is_reservable,
                            "is_read_only": is_read_only,

                            "freeform_tags": _safe_value(
                                freeform_tags
                            ),
                            "defined_tags": _safe_value(
                                defined_tags
                            ),
                        }
                    )

                    resources.append(resource)

                except Exception as error:

                    print(
                        f"    ERROR processing Block Volume "
                        f"{_get(volume, 'display_name', '')}: {error}"
                    )

    print(f"Block Volume: {len(resources)} resources found")

    return resources
