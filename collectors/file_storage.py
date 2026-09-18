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

    File Storage file systems are Availability-Domain scoped, so
    list_file_systems() is called once for every Availability Domain
    and compartment combination.

    Inventory details:
      - File System OCID
      - Name
      - Metered size / size in GB
      - Availability Domain
      - Lifecycle State
      - Mount Target information
      - Export information
      - KMS Key
      - Source Snapshot
      - Tags
    """

    resources = []

    regions = config.get("regions", [])
    compartments = config.get("compartments", [])

    tenancy_id = (
        config.get("tenancy")
        or config.get("tenancy_id")
        or config.get("tenancy_ocid")
    )

    if not tenancy_id:
        print("  ERROR: Tenancy OCID is missing from OCI config.")
        return resources

    for region in regions:

        print(f"  Processing File Storage region: {region}")

        try:
            file_storage_client = oci.file_storage.FileStorageClient(
                config,
                region=region,
            )

            identity_client = oci.identity.IdentityClient(
                config,
                region=region,
            )

            # File Storage file systems are AD-scoped.
            ad_response = oci.pagination.list_call_get_all_results(
                identity_client.list_availability_domains,
                compartment_id=tenancy_id,
            )

            availability_domains = ad_response.data

            if not availability_domains:
                print(
                    f"    WARNING: No Availability Domains found "
                    f"for region {region}"
                )
                continue

            # ---------------------------------------------------------
            # Process each compartment
            # ---------------------------------------------------------
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

                # -----------------------------------------------------
                # Mount targets are compartment scoped, so collect them
                # once per compartment rather than once per AD.
                # -----------------------------------------------------
                mount_targets = []

                try:
                    mt_response = (
                        oci.pagination.list_call_get_all_results(
                            file_storage_client.list_mount_targets,
                            compartment_id=compartment_id,
                        )
                    )

                    for mount_target in mt_response.data:

                        mount_target_id = _get(
                            mount_target,
                            "id",
                            "",
                        )

                        mount_targets.append(
                            {
                                "id": mount_target_id,
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
                                ),
                                "file_system_ids": _get(
                                    mount_target,
                                    "file_system_ids",
                                    [],
                                ),
                                "lifecycle_state": _get(
                                    mount_target,
                                    "lifecycle_state",
                                    "",
                                ),
                                "availability_domain": _get(
                                    mount_target,
                                    "availability_domain",
                                    "",
                                ),
                                "time_created": _get(
                                    mount_target,
                                    "time_created",
                                    None,
                                ),
                            }
                        )

                except Exception as exc:
                    print(
                        f"    WARNING: Could not collect mount targets "
                        f"from compartment {compartment_name}: {exc}"
                    )

                # -----------------------------------------------------
                # File systems are AD scoped.
                # -----------------------------------------------------
                for ad in availability_domains:

                    ad_name = _get(
                        ad,
                        "name",
                        "",
                    )

                    if not ad_name:
                        continue

                    print(
                        f"    Processing File Storage compartment: "
                        f"{compartment_name} | AD: {ad_name}"
                    )

                    try:
                        response = (
                            oci.pagination.list_call_get_all_results(
                                file_storage_client.list_file_systems,
                                compartment_id=compartment_id,
                                availability_domain=ad_name,
                            )
                        )

                        file_systems = response.data

                    except Exception as exc:

                        print(
                            f"    ERROR collecting File Systems "
                            f"from compartment {compartment_name} "
                            f"AD {ad_name}: {exc}"
                        )

                        continue

                    # -------------------------------------------------
                    # Export sets are also AD scoped.
                    # Collect them for this AD and map exports to FSS.
                    # -------------------------------------------------
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

                                    exports_by_file_system.setdefault(
                                        export_file_system_id,
                                        [],
                                    ).append(
                                        {
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
                                    )

                            except Exception as exc:
                                print(
                                    f"      WARNING: Could not collect "
                                    f"exports for export set "
                                    f"{export_set_id}: {exc}"
                                )

                    except Exception as exc:
                        print(
                            f"      WARNING: Could not collect export sets "
                            f"for AD {ad_name}: {exc}"
                        )

                    # -------------------------------------------------
                    # Build resource records
                    # -------------------------------------------------
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

                            availability_domain = _get(
                                file_system,
                                "availability_domain",
                                "",
                            ) or ad_name

                            # -------------------------------------------------
                            # SIZE
                            # -------------------------------------------------

                            metered_bytes = _get(
                                file_system,
                                "metered_bytes",
                                None,
                            )

                            # Keep compatibility with SDK/API variants.
                            storage_capacity = _get(
                                file_system,
                                "storage_capacity",
                                None,
                            )

                            if metered_bytes is None:
                                metered_bytes = _get(
                                    file_system,
                                    "size_bytes",
                                    None,
                                )

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
                                file_system,
                                "provisioned_throughput_in_mibps",
                                None,
                            )

                            source_snapshot_id = _get(
                                file_system,
                                "source_snapshot_id",
                                "",
                            )

                            # -------------------------------------------------
                            # ENCRYPTION
                            # -------------------------------------------------

                            kms_key_id = _get(
                                file_system,
                                "kms_key_id",
                                "",
                            )

                            # -------------------------------------------------
                            # MOUNT TARGETS belonging to this FSS
                            # -------------------------------------------------

                            fs_mount_targets = []

                            for mount_target in mount_targets:

                                mount_target_fs_ids = _get(
                                    mount_target,
                                    "file_system_ids",
                                    [],
                                ) or []

                                if (
                                    file_system_id
                                    and mount_target_fs_ids
                                    and file_system_id
                                    not in mount_target_fs_ids
                                ):
                                    continue

                                # If the mount target doesn't expose
                                # file_system_ids, keep it only when the
                                # target is in the same AD. This avoids
                                # incorrectly associating every target.
                                if not mount_target_fs_ids:
                                    mt_ad = _get(
                                        mount_target,
                                        "availability_domain",
                                        "",
                                    )

                                    if (
                                        mt_ad
                                        and availability_domain
                                        and mt_ad != availability_domain
                                    ):
                                        continue

                                fs_mount_targets.append(
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
                                        ),
                                        "lifecycle_state": _get(
                                            mount_target,
                                            "lifecycle_state",
                                            "",
                                        ),
                                        "availability_domain": _get(
                                            mount_target,
                                            "availability_domain",
                                            "",
                                        ),
                                        "time_created": _get(
                                            mount_target,
                                            "time_created",
                                            None,
                                        ),
                                    }
                                )

                            exports = exports_by_file_system.get(
                                file_system_id,
                                [],
                            )

                            # -------------------------------------------------
                            # TAGS
                            # -------------------------------------------------

                            defined_tags = _get(
                                file_system,
                                "defined_tags",
                                {},
                            )

                            freeform_tags = _get(
                                file_system,
                                "freeform_tags",
                                {},
                            )

                            # -------------------------------------------------
                            # RESOURCE
                            # -------------------------------------------------

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

                                # SIZE
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

                                "metered_size_gb":
                                    metered_size_gb,

                                "size_gb":
                                    metered_size_gb,

                                "provisioned_throughput_in_mibps":
                                    provisioned_throughput,

                                # ENCRYPTION
                                "kms_key_id":
                                    kms_key_id,

                                "kms_key_ocid":
                                    kms_key_id,

                                # SOURCE
                                "source_snapshot_id":
                                    source_snapshot_id,

                                # MOUNT TARGETS
                                "mount_targets":
                                    fs_mount_targets,

                                "mount_target_count":
                                    len(fs_mount_targets),

                                # EXPORTS
                                "exports":
                                    exports,

                                "export_count":
                                    len(exports),

                                # TIME
                                "time_created":
                                    _get(
                                        file_system,
                                        "time_created",
                                        None,
                                    ),

                                # TAGS
                                "defined_tags":
                                    defined_tags,

                                "freeform_tags":
                                    freeform_tags,
                            }

                            resources.append(resource)

                        except Exception as exc:

                            print(
                                f"    ERROR processing File System "
                                f"{_get(file_system, 'display_name', '')}: "
                                f"{exc}"
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

