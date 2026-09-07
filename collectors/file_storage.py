import oci


def _get(obj, name, default=None):
    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(name, default)

    return getattr(obj, name, default)


def collect_file_storage(config):
    """
    Collect OCI File Storage file systems.

    Important inventory details:
    - File System OCID
    - Name
    - Size / provisioned size
    - Metered bytes
    - Availability Domain
    - Lifecycle State
    - Mount Target information
    - KMS Key
    - Snapshot Policy
    - Encryption
    - Tags
    """

    resources = []

    regions = config.get(
        "regions",
        []
    )

    compartments = config.get(
        "compartments",
        []
    )

    for region in regions:

        print(
            f"  Processing File Storage region: {region}"
        )

        try:

            file_storage_client = (
                oci.file_storage.FileStorageClient(
                    config,
                    region=region
                )
            )

            for compartment in compartments:

                compartment_id = _get(
                    compartment,
                    "id",
                    compartment
                    if isinstance(compartment, str)
                    else None
                )

                compartment_name = _get(
                    compartment,
                    "name",
                    ""
                )

                if not compartment_id:
                    continue

                # =====================================================
                # FILE SYSTEMS
                # =====================================================

                try:

                    response = (
                        oci.pagination.list_call_get_all_results(
                            file_storage_client.list_file_systems,
                            compartment_id=compartment_id
                        )
                    )

                    file_systems = response.data

                except Exception as exc:

                    print(
                        f"    ERROR collecting File Systems "
                        f"from compartment "
                        f"{compartment_name}: {exc}"
                    )

                    continue

                for file_system in file_systems:

                    try:

                        file_system_id = _get(
                            file_system,
                            "id",
                            ""
                        )

                        display_name = _get(
                            file_system,
                            "display_name",
                            ""
                        )

                        lifecycle_state = _get(
                            file_system,
                            "lifecycle_state",
                            ""
                        )

                        availability_domain = _get(
                            file_system,
                            "availability_domain",
                            ""
                        )

                        # =================================================
                        # SIZE
                        # =================================================

                        # OCI FSS normally exposes metered/provisioned
                        # information depending on the SDK/API version.

                        metered_bytes = _get(
                            file_system,
                            "metered_bytes",
                            None
                        )

                        source_snapshot_id = _get(
                            file_system,
                            "source_snapshot_id",
                            ""
                        )

                        storage_capacity = _get(
                            file_system,
                            "storage_capacity",
                            None
                        )

                        # Some SDK versions expose:
                        # provisioned_throughput_in_mibps
                        # instead of a direct size property.

                        provisioned_throughput = _get(
                            file_system,
                            "provisioned_throughput_in_mibps",
                            None
                        )

                        # =================================================
                        # ENCRYPTION
                        # =================================================

                        kms_key_id = _get(
                            file_system,
                            "kms_key_id",
                            ""
                        )

                        # =================================================
                        # MOUNT TARGETS
                        # =================================================

                        mount_targets = []

                        try:

                            mt_response = (
                                oci.pagination.list_call_get_all_results(
                                    file_storage_client.list_mount_targets,
                                    compartment_id=compartment_id
                                )
                            )

                            for mount_target in mt_response.data:

                                mount_target_id = _get(
                                    mount_target,
                                    "id",
                                    ""
                                )

                                # Keep only mount targets belonging
                                # to this file system when possible.

                                mount_target_fs_ids = _get(
                                    mount_target,
                                    "file_system_ids",
                                    []
                                )

                                if (
                                    file_system_id
                                    and mount_target_fs_ids
                                    and file_system_id
                                    not in mount_target_fs_ids
                                ):
                                    continue

                                mount_targets.append(
                                    {
                                        "id": mount_target_id,

                                        "display_name": _get(
                                            mount_target,
                                            "display_name",
                                            ""
                                        ),

                                        "subnet_id": _get(
                                            mount_target,
                                            "subnet_id",
                                            ""
                                        ),

                                        "vcn_id": _get(
                                            mount_target,
                                            "vcn_id",
                                            ""
                                        ),

                                        "private_ip_ids": _get(
                                            mount_target,
                                            "private_ip_ids",
                                            []
                                        ),

                                        "lifecycle_state": _get(
                                            mount_target,
                                            "lifecycle_state",
                                            ""
                                        ),

                                        "availability_domain": _get(
                                            mount_target,
                                            "availability_domain",
                                            ""
                                        ),

                                        "time_created": _get(
                                            mount_target,
                                            "time_created",
                                            None
                                        ),
                                    }
                                )

                        except Exception as exc:

                            print(
                                f"      WARNING: Could not collect "
                                f"mount targets for "
                                f"{display_name}: {exc}"
                            )

                        # =================================================
                        # EXPORTS
                        # =================================================

                        exports = []

                        try:

                            export_sets = (
                                oci.pagination.list_call_get_all_results(
                                    file_storage_client.list_export_sets,
                                    compartment_id=compartment_id
                                )
                            )

                            for export_set in export_sets.data:

                                export_set_id = _get(
                                    export_set,
                                    "id",
                                    ""
                                )

                                try:

                                    export_response = (
                                        oci.pagination.list_call_get_all_results(
                                            file_storage_client.list_exports,
                                            export_set_id=export_set_id
                                        )
                                    )

                                    for export in export_response.data:

                                        export_file_system_id = _get(
                                            export,
                                            "file_system_id",
                                            ""
                                        )

                                        if (
                                            export_file_system_id
                                            and export_file_system_id
                                            != file_system_id
                                        ):
                                            continue

                                        exports.append(
                                            {
                                                "id": _get(
                                                    export,
                                                    "id",
                                                    ""
                                                ),

                                                "export_path": _get(
                                                    export,
                                                    "path",
                                                    ""
                                                ),

                                                "file_system_id":
                                                    export_file_system_id,

                                                "export_set_id":
                                                    export_set_id,

                                                "time_created": _get(
                                                    export,
                                                    "time_created",
                                                    None
                                                ),
                                            }
                                        )

                                except Exception:
                                    continue

                        except Exception:
                            pass

                        # =================================================
                        # TAGS
                        # =================================================

                        defined_tags = _get(
                            file_system,
                            "defined_tags",
                            {}
                        )

                        freeform_tags = _get(
                            file_system,
                            "freeform_tags",
                            {}
                        )

                        # =================================================
                        # RESOURCE
                        # =================================================

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
                                availability_domain,

                            "lifecycle_state":
                                lifecycle_state,

                            "state":
                                lifecycle_state,

                            # =============================================
                            # SIZE
                            # =============================================

                            "metered_bytes":
                                metered_bytes,

                            "size_bytes":
                                metered_bytes,

                            "file_system_size_bytes":
                                metered_bytes,

                            "storage_capacity":
                                storage_capacity,

                            "storage_capacity_bytes":
                                storage_capacity,

                            "provisioned_throughput_in_mibps":
                                provisioned_throughput,

                            # =============================================
                            # ENCRYPTION
                            # =============================================

                            "kms_key_id":
                                kms_key_id,

                            "kms_key_ocid":
                                kms_key_id,

                            # =============================================
                            # SOURCE
                            # =============================================

                            "source_snapshot_id":
                                source_snapshot_id,

                            # =============================================
                            # MOUNT TARGETS
                            # =============================================

                            "mount_targets":
                                mount_targets,

                            "mount_target_count":
                                len(mount_targets),

                            # =============================================
                            # EXPORTS
                            # =============================================

                            "exports":
                                exports,

                            "export_count":
                                len(exports),

                            # =============================================
                            # TIME
                            # =============================================

                            "time_created":
                                _get(
                                    file_system,
                                    "time_created",
                                    None
                                ),

                            # =============================================
                            # TAGS
                            # =============================================

                            "defined_tags":
                                defined_tags,

                            "freeform_tags":
                                freeform_tags,
                        }

                        resources.append(
                            resource
                        )

                    except Exception as exc:

                        print(
                            f"    ERROR processing File System "
                            f"{display_name}: {exc}"
                        )

        except Exception as exc:

            print(
                f"  ERROR collecting File Storage "
                f"region {region}: {exc}"
            )

    print(
        f"File Systems: {len(resources)} resources found"
    )

    return resources
