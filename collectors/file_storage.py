import oci

from utils.compartments import get_compartments
from utils.regions import get_regions


def _get(obj, name, default=None):
    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(name, default)

    return getattr(obj, name, default)


def _safe_value(value):
    """
    Convert OCI SDK objects/lists/dicts into safe values.
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


def collect_file_storage(config):
    """
    Collect OCI File Storage file systems across:

      - All subscribed regions
      - All accessible compartments
      - All Availability Domains

    Collects:

      - File System OCID
      - Name
      - Size
      - Metered Bytes
      - Metered Size GB
      - Availability Domain
      - Lifecycle State
      - Mount Targets
      - Export Sets / Exports
      - KMS Key
      - Source Snapshot
      - Creation Date
      - Defined Tags
      - Freeform Tags
    """

    resources = []

    # ============================================================
    # USE SAME REGION / COMPARTMENT DISCOVERY AS WORKING COLLECTORS
    # ============================================================

    compartments = get_compartments(config)
    regions = get_regions(config)

    tenancy_id = (
        config.get("tenancy")
        or config.get("tenancy_id")
        or config.get("tenancy_ocid")
    )

    if not tenancy_id:
        print(
            "  ERROR: Tenancy OCID is missing from OCI config."
        )
        return resources

    # ============================================================
    # REGIONS
    # ============================================================

    for region in regions:

        print(
            f"  Processing File Storage region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        # ========================================================
        # FILE STORAGE CLIENT
        # ========================================================

        try:

            file_storage_client = (
                oci.file_storage.FileStorageClient(
                    region_config
                )
            )

        except Exception as error:

            print(
                f"    ERROR creating File Storage client "
                f"for region {region}: {error}"
            )

            continue

        # ========================================================
        # IDENTITY CLIENT
        # ========================================================

        try:

            identity_client = (
                oci.identity.IdentityClient(
                    region_config
                )
            )

            ad_response = (
                oci.pagination.list_call_get_all_results(
                    identity_client.list_availability_domains,
                    compartment_id=tenancy_id,
                )
            )

            availability_domains = ad_response.data

        except Exception as error:

            print(
                f"    ERROR getting Availability Domains "
                f"for region {region}: {error}"
            )

            continue

        if not availability_domains:

            print(
                f"    WARNING: No Availability Domains found "
                f"for region {region}"
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

            # ====================================================
            # AVAILABILITY DOMAINS
            # ====================================================

            for availability_domain in availability_domains:

                ad_name = _get(
                    availability_domain,
                    "name",
                    "",
                )

                if not ad_name:
                    continue

                print(
                    f"    Processing File Storage compartment: "
                    f"{compartment_name} | AD: {ad_name}"
                )

                # =================================================
                # FILE SYSTEMS
                # =================================================

                try:

                    response = (
                        oci.pagination.list_call_get_all_results(
                            file_storage_client.list_file_systems,
                            compartment_id=compartment_id,
                            availability_domain=ad_name,
                        )
                    )

                    file_systems = response.data

                except Exception as error:

                    print(
                        f"      ERROR collecting File Systems "
                        f"from compartment {compartment_name} "
                        f"AD {ad_name}: {error}"
                    )

                    continue

                if not file_systems:
                    continue

                # =================================================
                # MOUNT TARGETS
                #
                # Mount targets are AD scoped.
                # =================================================

                mount_targets = []

                try:

                    mt_response = (
                        oci.pagination.list_call_get_all_results(
                            file_storage_client.list_mount_targets,
                            compartment_id=compartment_id,
                            availability_domain=ad_name,
                        )
                    )

                    for mount_target in mt_response.data:

                        mount_targets.append(
                            {
                                "id": _get(
                                    mount_target,
                                    "id",
                                    "",
                                ),

                                "display_name": _get(
                                    mount_target,
                                    "display_name",
                                    "",
                                ),

                                "subnet_id": _get(
                                    mount_target,
                                    "subnet_id",
                                    "",
                                ),

                                "vcn_id": _get(
                                    mount_target,
                                    "vcn_id",
                                    "",
                                ),

                                "private_ip_ids": _get(
                                    mount_target,
                                    "private_ip_ids",
                                    [],
                                ) or [],

                                "file_system_ids": _get(
                                    mount_target,
                                    "file_system_ids",
                                    [],
                                ) or [],

                                "lifecycle_state": _get(
                                    mount_target,
                                    "lifecycle_state",
                                    "",
                                ),

                                "availability_domain": _get(
                                    mount_target,
                                    "availability_domain",
                                    ad_name,
                                ),

                                "time_created": _get(
                                    mount_target,
                                    "time_created",
                                    None,
                                ),
                            }
                        )

                except Exception as error:

                    print(
                        f"      WARNING: Could not collect "
                        f"Mount Targets from compartment "
                        f"{compartment_name} AD {ad_name}: "
                        f"{error}"
                    )

                # =================================================
                # EXPORT SETS
                # =================================================

                exports_by_file_system = {}

                try:

                    export_sets_response = (
                        oci.pagination.list_call_get_all_results(
                            file_storage_client.list_export_sets,
                            compartment_id=compartment_id,
                            availability_domain=ad_name,
                        )
                    )

                    for export_set in export_sets_response.data:

                        export_set_id = _get(
                            export_set,
                            "id",
                            "",
                        )

                        if not export_set_id:
                            continue

                        try:

                            export_response = (
                                oci.pagination.list_call_get_all_results(
                                    file_storage_client.list_exports,
                                    export_set_id=export_set_id,
                                )
                            )

                            for export in export_response.data:

                                export_file_system_id = _get(
                                    export,
                                    "file_system_id",
                                    "",
                                )

                                if not export_file_system_id:
                                    continue

                                export_data = {
                                    "id": _get(
                                        export,
                                        "id",
                                        "",
                                    ),

                                    "export_path": _get(
                                        export,
                                        "path",
                                        "",
                                    ),

                                    "file_system_id":
                                        export_file_system_id,

                                    "export_set_id":
                                        export_set_id,

                                    "time_created": _get(
                                        export,
                                        "time_created",
                                        None,
                                    ),
                                }

                                exports_by_file_system.setdefault(
                                    export_file_system_id,
                                    [],
                                ).append(
                                    export_data
                                )

                        except Exception as error:

                            print(
                                f"        WARNING: Could not collect "
                                f"exports for export set "
                                f"{export_set_id}: {error}"
                            )

                except Exception as error:

                    print(
                        f"      WARNING: Could not collect "
                        f"export sets for AD {ad_name}: "
                        f"{error}"
                    )

                # =================================================
                # PROCESS FILE SYSTEMS
                # =================================================

                for file_system in file_systems:

                    try:

                        file_system_id = _get(
                            file_system,
                            "id",
                            "",
                        )

                        display_name = _get(
                            file_system,
                            "display_name",
                            "",
                        )

                        lifecycle_state = _get(
                            file_system,
                            "lifecycle_state",
                            "",
                        )

                        availability_domain_value = _get(
                            file_system,
                            "availability_domain",
                            ad_name,
                        )

                        # =========================================
                        # GET DETAILED FILE SYSTEM
                        # =========================================

                        file_system_details = file_system

                        if file_system_id:

                            try:

                                detail_response = (
                                    file_storage_client.get_file_system(
                                        file_system_id
                                    )
                                )

                                file_system_details = (
                                    detail_response.data
                                )

                            except Exception as detail_error:

                                print(
                                    f"      WARNING: Could not get "
                                    f"details for File System "
                                    f"{display_name}: "
                                    f"{detail_error}"
                                )

                        # =========================================
                        # BASIC DETAILS
                        # =========================================

                        lifecycle_state = _get(
                            file_system_details,
                            "lifecycle_state",
                            lifecycle_state,
                        )

                        time_created = _get(
                            file_system_details,
                            "time_created",
                            None,
                        )

                        # =========================================
                        # SIZE
                        # =========================================

                        metered_bytes = _get(
                            file_system_details,
                            "metered_bytes",
                            None,
                        )

                        if metered_bytes is None:

                            metered_bytes = _get(
                                file_system_details,
                                "size_bytes",
                                None,
                            )

                        storage_capacity = _get(
                            file_system_details,
                            "storage_capacity",
                            None,
                        )

                        # Convert bytes → GB
                        metered_size_gb = ""

                        try:

                            if metered_bytes is not None:

                                metered_size_gb = (
                                    float(metered_bytes)
                                    / (1024 ** 3)
                                )

                        except Exception:

                            metered_size_gb = ""

                        provisioned_throughput = _get(
                            file_system_details,
                            "provisioned_throughput_in_mibps",
                            None,
                        )

                        # =========================================
                        # ENCRYPTION
                        # =========================================

                        kms_key_id = _get(
                            file_system_details,
                            "kms_key_id",
                            "",
                        )

                        # =========================================
                        # SOURCE
                        # =========================================

                        source_snapshot_id = _get(
                            file_system_details,
                            "source_snapshot_id",
                            "",
                        )

                        # =========================================
                        # MOUNT TARGETS FOR THIS FILE SYSTEM
                        # =========================================

                        fs_mount_targets = []

                        for mount_target in mount_targets:

                            mount_target_fs_ids = _get(
                                mount_target,
                                "file_system_ids",
                                [],
                            ) or []

                            # If the mount target explicitly reports
                            # its file systems, associate only the
                            # matching file system.

                            if (
                                mount_target_fs_ids
                                and file_system_id
                                not in mount_target_fs_ids
                            ):
                                continue

                            fs_mount_targets.append(
                                mount_target
                            )

                        # =========================================
                        # EXPORTS
                        # =========================================

                        exports = (
                            exports_by_file_system.get(
                                file_system_id,
                                [],
                            )
                        )

                        # =========================================
                        # TAGS
                        # =========================================

                        defined_tags = _get(
                            file_system_details,
                            "defined_tags",
                            {},
                        ) or {}

                        freeform_tags = _get(
                            file_system_details,
                            "freeform_tags",
                            {},
                        ) or {}

                        # =========================================
                        # RESOURCE
                        # =========================================

                        resource = {

                            "service":
                                "File Storage",

                            "resource_type":
                                "File System",

                            "id":
                                file_system_id,

                            "ocid":
                                file_system_id,

                            "name":
                                display_name,

                            "display_name":
                                display_name,

                            "region":
                                region,

                            "compartment_id":
                                compartment_id,

                            "compartment_name":
                                compartment_name,

                            "availability_domain":
                                availability_domain_value,

                            "lifecycle_state":
                                lifecycle_state,

                            "state":
                                lifecycle_state,

                            # -------------------------------
                            # SIZE
                            # -------------------------------

                            "metered_bytes":
                                metered_bytes,

                            "size_bytes":
                                metered_bytes,

                            "file_system_size_bytes":
                                metered_bytes,

                            "metered_size_gb":
                                metered_size_gb,

                            "size_gb":
                                metered_size_gb,

                            "storage_capacity":
                                storage_capacity,

                            "storage_capacity_bytes":
                                storage_capacity,

                            "provisioned_throughput_in_mibps":
                                provisioned_throughput,

                            # -------------------------------
                            # ENCRYPTION
                            # -------------------------------

                            "kms_key_id":
                                kms_key_id,

                            "kms_key_ocid":
                                kms_key_id,

                            # -------------------------------
                            # SOURCE
                            # -------------------------------

                            "source_snapshot_id":
                                source_snapshot_id,

                            # -------------------------------
                            # MOUNT TARGETS
                            # -------------------------------

                            "mount_targets":
                                _safe_value(
                                    fs_mount_targets
                                ),

                            "mount_target_count":
                                len(fs_mount_targets),

                            # -------------------------------
                            # EXPORTS
                            # -------------------------------

                            "exports":
                                _safe_value(
                                    exports
                                ),

                            "export_count":
                                len(exports),

                            # -------------------------------
                            # TIME
                            # -------------------------------

                            "time_created":
                                time_created,

                            # -------------------------------
                            # TAGS
                            # -------------------------------

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
                            f"      ERROR processing File System "
                            f"{_get(file_system, 'display_name', '')}: "
                            f"{error}"
                        )

    # ============================================================
    # SUMMARY
    # ============================================================

    print(
        f"File Systems: {len(resources)} resources found"
    )

    return resources
