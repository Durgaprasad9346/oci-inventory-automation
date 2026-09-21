import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def _get(obj, name, default=""):
    """
    Safely get an attribute from an OCI SDK object.
    """

    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(name, default)

    return getattr(obj, name, default)


def _to_dict(obj):
    """
    Safely convert OCI SDK model to dictionary.
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

    try:
        if hasattr(obj, "__dict__"):
            return obj.__dict__
    except Exception:
        pass

    return {}


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


def _get_backup_policy_details(blockstorage_client, asset_id):
    """
    Get the backup policy assigned to a boot volume or volume group.

    OCI backup policy assignment is queried separately from the boot
    volume object. The assignment returns the policy OCID, which is then
    used to fetch the full backup policy definition.
    """

    result = {
        "backup_policy_assignment_id": "",
        "backup_policy_asset_id": asset_id or "",
        "backup_policy_id": "",
        "backup_policy_display_name": "",
        "backup_policy_name": "",
        "backup_policy_destination_region": "",
        "backup_policy_time_created": None,
        "backup_policy_compartment_id": "",
        "backup_policy_schedules": [],
        "backup_policy_details": {},
        "backup_policy_source": "",
    }

    if not asset_id:
        return result

    try:
        response = blockstorage_client.get_volume_backup_policy_asset_assignment(
            asset_id=asset_id
        )
        assignments = _get(response, "data", []) or []

        if not isinstance(assignments, (list, tuple)):
            assignments = [assignments]

        if not assignments:
            return result

        assignment = assignments[0]

        result["backup_policy_assignment_id"] = _get(
            assignment, "id", ""
        )
        result["backup_policy_asset_id"] = _get(
            assignment, "asset_id", asset_id
        )
        result["backup_policy_id"] = _get(
            assignment, "policy_id", ""
        )

        policy_id = result["backup_policy_id"]
        if not policy_id:
            return result

        try:
            policy_response = blockstorage_client.get_volume_backup_policy(
                policy_id=policy_id
            )
            policy = _get(policy_response, "data", None)

            result["backup_policy_display_name"] = _get(
                policy, "display_name", ""
            )
            result["backup_policy_name"] = result[
                "backup_policy_display_name"
            ]
            result["backup_policy_destination_region"] = _get(
                policy, "destination_region", ""
            )
            result["backup_policy_time_created"] = _get(
                policy, "time_created", None
            )
            result["backup_policy_compartment_id"] = _get(
                policy, "compartment_id", ""
            )
            result["backup_policy_schedules"] = _safe_value(
                _get(policy, "schedules", []) or []
            )
            result["backup_policy_details"] = _safe_value(policy)

        except Exception as error:
            print(
                f"    WARNING getting backup policy details "
                f"for asset {asset_id}: {error}"
            )

    except Exception as error:
        print(
            f"    WARNING getting backup policy assignment "
            f"for asset {asset_id}: {error}"
        )

    return result


def collect_boot_volume(config):
    """
    Collect OCI Boot Volumes across:

        - All subscribed regions
        - All accessible compartments
        - All availability domains

    Collects important Boot Volume information including:

        Basic:
        - Name
        - OCID
        - Compartment
        - Region
        - Availability Domain
        - Lifecycle State
        - Creation Time

        Storage:
        - Size in GB
        - VPU per GB
        - Volume Performance
        - Volume Group

        Source:
        - Source Type
        - Source ID
        - Source Volume Backup ID

        Encryption:
        - KMS Key ID

        Configuration:
        - Hydrated
        - Autotune Policies
        - Policy

        Tags:
        - Defined Tags
        - Freeform Tags
    """

    resources = []

    compartments = get_compartments(config)
    regions = get_regions(config)

    # =============================================================
    # TENANCY OCID
    # =============================================================
    #
    # OCI config normally uses "tenancy", not "tenancy_id".
    #
    # =============================================================

    tenancy_id = config.get("tenancy")

    if not tenancy_id:

        print(
            "    ERROR collecting Boot Volumes: "
            "OCI tenancy OCID not found in config"
        )

        return resources

    # =============================================================
    # PROCESS REGIONS
    # =============================================================

    for region in regions:

        print(
            f"  Processing Boot Volume region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        # =========================================================
        # BLOCK STORAGE CLIENT
        # =========================================================

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

        # =========================================================
        # IDENTITY CLIENT
        # =========================================================

        try:

            identity_client = oci.identity.IdentityClient(
                region_config
            )

            availability_domains = (
                oci.pagination.list_call_get_all_results(
                    identity_client.list_availability_domains,
                    compartment_id=tenancy_id,
                )
            ).data

        except Exception as error:

            print(
                f"    ERROR getting Availability Domains "
                f"for region {region}: {error}"
            )

            continue

        # =========================================================
        # COMPARTMENTS
        # =========================================================

        for compartment in compartments:

            compartment_id = compartment["id"]

            compartment_name = compartment.get(
                "name",
                compartment_id,
            )

            # =====================================================
            # AVAILABILITY DOMAINS
            # =====================================================

            for availability_domain in availability_domains:

                ad_name = _get(
                    availability_domain,
                    "name",
                    "",
                )

                try:

                    # =================================================
                    # LIST BOOT VOLUMES
                    # =================================================

                    response = (
                        oci.pagination.list_call_get_all_results(
                            blockstorage_client.list_boot_volumes,
                            compartment_id=compartment_id,
                            availability_domain=ad_name,
                        )
                    )

                    boot_volumes = response.data

                except Exception as error:

                    print(
                        f"    ERROR collecting Boot Volumes "
                        f"from compartment "
                        f"{compartment_name}, "
                        f"AD {ad_name}: {error}"
                    )

                    continue

                # =====================================================
                # PROCESS BOOT VOLUMES
                # =====================================================

                for boot_volume in boot_volumes:

                    try:

                        # =================================================
                        # BASIC INFORMATION
                        # =================================================

                        boot_volume_id = _get(
                            boot_volume,
                            "id",
                            "",
                        )

                        display_name = _get(
                            boot_volume,
                            "display_name",
                            "",
                        )

                        lifecycle_state = _get(
                            boot_volume,
                            "lifecycle_state",
                            "",
                        )

                        lifecycle_details = _get(
                            boot_volume,
                            "lifecycle_details",
                            "",
                        )

                        time_created = _get(
                            boot_volume,
                            "time_created",
                            None,
                        )

                        # =================================================
                        # STORAGE INFORMATION
                        # =================================================

                        size_in_gbs = _get(
                            boot_volume,
                            "size_in_gbs",
                            None,
                        )

                        vpus_per_gb = _get(
                            boot_volume,
                            "vpus_per_gb",
                            None,
                        )

                        volume_group_id = _get(
                            boot_volume,
                            "volume_group_id",
                            "",
                        )

                        # =================================================
                        # SOURCE INFORMATION
                        # =================================================

                        source_type = _get(
                            boot_volume,
                            "source_type",
                            "",
                        )

                        source_id = _get(
                            boot_volume,
                            "source_id",
                            "",
                        )

                        source_volume_backup_id = _get(
                            boot_volume,
                            "source_volume_backup_id",
                            "",
                        )

                        # =================================================
                        # ENCRYPTION
                        # =================================================

                        kms_key_id = _get(
                            boot_volume,
                            "kms_key_id",
                            "",
                        )

                        # =================================================
                        # BACKUP POLICY
                        # =================================================

                        backup_policy_id = _get(
                            boot_volume,
                            "backup_policy_id",
                            "",
                        )

                        backup_policy = _get_backup_policy_details(
                            blockstorage_client,
                            boot_volume_id,
                        )

                        backup_policy_source = "BOOT_VOLUME" if backup_policy[
                            "backup_policy_id"
                        ] else ""

                        # A backup policy can also be managed through the
                        # volume group. Fall back to the volume group when
                        # the boot volume itself has no direct assignment.
                        if (
                            not backup_policy["backup_policy_id"]
                            and volume_group_id
                        ):
                            group_backup_policy = _get_backup_policy_details(
                                blockstorage_client,
                                volume_group_id,
                            )

                            if group_backup_policy["backup_policy_id"]:
                                backup_policy = group_backup_policy
                                backup_policy_source = "VOLUME_GROUP"

                        if not backup_policy_id:
                            backup_policy_id = backup_policy[
                                "backup_policy_id"
                            ]

                        # =================================================
                        # CONFIGURATION
                        # =================================================

                        is_hydrated = _get(
                            boot_volume,
                            "is_hydrated",
                            None,
                        )

                        autotune_policies = _get(
                            boot_volume,
                            "autotune_policies",
                            [],
                        )

                        policy = _get(
                            boot_volume,
                            "policy",
                            "",
                        )

                        # =================================================
                        # TAGS
                        # =================================================

                        defined_tags = _get(
                            boot_volume,
                            "defined_tags",
                            {},
                        )

                        freeform_tags = _get(
                            boot_volume,
                            "freeform_tags",
                            {},
                        )

                        # =================================================
                        # DETAILS
                        # =================================================

                        details = {

                            # ---------------------------------------------
                            # BASIC
                            # ---------------------------------------------

                            "availability_domain":
                                ad_name,

                            "lifecycle_state":
                                lifecycle_state,

                            "lifecycle_details":
                                lifecycle_details,

                            # ---------------------------------------------
                            # STORAGE
                            # ---------------------------------------------

                            "size_in_gbs":
                                size_in_gbs,

                            "size_gb":
                                size_in_gbs,

                            "volume_size_gb":
                                size_in_gbs,

                            "vpus_per_gb":
                                vpus_per_gb,

                            "volume_performance":
                                vpus_per_gb,

                            "volume_group_id":
                                volume_group_id,

                            # ---------------------------------------------
                            # SOURCE
                            # ---------------------------------------------

                            "source_type":
                                source_type,

                            "source_id":
                                source_id,

                            "source_volume_backup_id":
                                source_volume_backup_id,

                            # ---------------------------------------------
                            # ENCRYPTION
                            # ---------------------------------------------

                            "kms_key_id":
                                kms_key_id,

                            "is_encrypted":
                                bool(kms_key_id),

                            # ---------------------------------------------
                            # BACKUP POLICY
                            # ---------------------------------------------

                            "backup_policy_id":
                                backup_policy_id,

                            "backup_policy_assignment_id":
                                backup_policy[
                                    "backup_policy_assignment_id"
                                ],

                            "backup_policy_asset_id":
                                backup_policy[
                                    "backup_policy_asset_id"
                                ],

                            "backup_policy_display_name":
                                backup_policy[
                                    "backup_policy_display_name"
                                ],

                            "backup_policy_name":
                                backup_policy[
                                    "backup_policy_name"
                                ],

                            "backup_policy_destination_region":
                                backup_policy[
                                    "backup_policy_destination_region"
                                ],

                            "backup_policy_time_created":
                                backup_policy[
                                    "backup_policy_time_created"
                                ],

                            "backup_policy_compartment_id":
                                backup_policy[
                                    "backup_policy_compartment_id"
                                ],

                            "backup_policy_schedules":
                                backup_policy[
                                    "backup_policy_schedules"
                                ],

                            "backup_policy_details":
                                backup_policy[
                                    "backup_policy_details"
                                ],

                            "backup_policy_source":
                                backup_policy_source,

                            # ---------------------------------------------
                            # CONFIGURATION
                            # ---------------------------------------------

                            "is_hydrated":
                                is_hydrated,

                            "autotune_policies":
                                _to_dict(autotune_policies),

                            "policy":
                                policy,

                            # ---------------------------------------------
                            # TAGS
                            # ---------------------------------------------

                            "defined_tags":
                                defined_tags,

                            "freeform_tags":
                                freeform_tags,
                        }

                        # =================================================
                        # RESOURCE OBJECT
                        # =================================================

                        resource = Resource(

                            service="Boot Volume",

                            resource_type="Boot Volume",

                            name=display_name,

                            ocid=boot_volume_id,

                            compartment_id=(
                                _get(
                                    boot_volume,
                                    "compartment_id",
                                    compartment_id,
                                )
                            ),

                            compartment_name=(
                                compartment_name
                            ),

                            region=region,

                            state=lifecycle_state,

                            time_created=time_created,

                            defined_tags=defined_tags,

                            freeform_tags=freeform_tags,

                            details=details,
                        )

                        resources.append(
                            resource
                        )

                    except Exception as error:

                        print(
                            f"    ERROR processing Boot Volume "
                            f"{display_name}: {error}"
                        )

    # =============================================================
    # SUMMARY
    # =============================================================

    print(
        f"Boot Volumes: {len(resources)} resources found"
    )

    return resources
