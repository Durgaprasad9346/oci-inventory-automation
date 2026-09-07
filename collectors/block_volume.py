import oci


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
    Convert OCI SDK object to dictionary when possible.
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


def collect_block_volume(config):
    """
    Collect OCI Block Volumes.

    Important details collected:

    - Display Name
    - OCID
    - Size in GB
    - Volume Type
    - VPUs per GB
    - Lifecycle State
    - Availability Domain
    - Compartment
    - Encryption
    - KMS Key
    - Source Volume
    - Source Type
    - Backup Policy
    - Volume Group
    - Replica Information
    - Read Only
    - Shareable
    - Time Created
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
            f"  Processing Block Volume region: {region}"
        )

        try:

            blockstorage_client = (
                oci.core.BlockstorageClient(
                    config
                )
            )

            blockstorage_client.base_client.set_region(
                region
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

                try:

                    response = (
                        oci.pagination.list_call_get_all_results(
                            blockstorage_client.list_volumes,
                            compartment_id=compartment_id
                        )
                    )

                    volumes = response.data

                except Exception as exc:

                    print(
                        f"    ERROR collecting Block Volumes "
                        f"from compartment "
                        f"{compartment_name}: {exc}"
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

                        size_in_gbs = _get(
                            volume,
                            "size_in_gbs",
                            None
                        )

                        size_in_mbs = _get(
                            volume,
                            "size_in_mbs",
                            None
                        )

                        vpus_per_gb = _get(
                            volume,
                            "vpus_per_gb",
                            None
                        )

                        volume_type = _get(
                            volume,
                            "volume_type",
                            ""
                        )

                        availability_domain = _get(
                            volume,
                            "availability_domain",
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
                            None
                        )

                        is_reservable = _get(
                            volume,
                            "is_reservable",
                            None
                        )

                        is_read_only = _get(
                            volume,
                            "is_read_only",
                            None
                        )

                        is_volume_group_clone = _get(
                            volume,
                            "is_volume_group_clone",
                            None
                        )

                        is_auto_tune_enabled = _get(
                            volume,
                            "is_auto_tune_enabled",
                            None
                        )

                        auto_tuned_vpus_per_gb = _get(
                            volume,
                            "auto_tuned_vpus_per_gb",
                            None
                        )

                        size_in_gbs = (
                            size_in_gbs
                            if size_in_gbs is not None
                            else ""
                        )

                        size_in_mbs = (
                            size_in_mbs
                            if size_in_mbs is not None
                            else ""
                        )

                        vpus_per_gb = (
                            vpus_per_gb
                            if vpus_per_gb is not None
                            else ""
                        )

                        # ------------------------------------------------
                        # ENCRYPTION
                        # ------------------------------------------------

                        kms_key_id = _get(
                            volume,
                            "kms_key_id",
                            ""
                        )

                        encryption_in_transit_type = _get(
                            volume,
                            "encryption_in_transit_type",
                            ""
                        )

                        # ------------------------------------------------
                        # SOURCE DETAILS
                        # ------------------------------------------------

                        source_details = _get(
                            volume,
                            "source_details",
                            None
                        )

                        source_dict = _safe_dict(
                            source_details
                        )

                        source_type = _get(
                            source_details,
                            "type",
                            source_dict.get(
                                "type",
                                ""
                            )
                        )

                        source_volume_id = _get(
                            source_details,
                            "id",
                            source_dict.get(
                                "id",
                                ""
                            )
                        )

                        source_volume_size = _get(
                            source_details,
                            "size_in_gbs",
                            source_dict.get(
                                "size_in_gbs",
                                ""
                            )
                        )

                        # ------------------------------------------------
                        # BACKUP POLICY
                        # ------------------------------------------------

                        backup_policy_id = ""

                        try:

                            backup_policy_assignments = (
                                oci.pagination.list_call_get_all_results(
                                    blockstorage_client.list_volume_backup_policy_assignments,
                                    asset_id=volume_id
                                ).data
                            )

                            if backup_policy_assignments:

                                assignment = (
                                    backup_policy_assignments[0]
                                )

                                backup_policy_id = _get(
                                    assignment,
                                    "policy_id",
                                    ""
                                )

                        except Exception:
                            backup_policy_id = ""

                        # ------------------------------------------------
                        # VOLUME GROUP
                        # ------------------------------------------------

                        volume_group_id = _get(
                            volume,
                            "volume_group_id",
                            ""
                        )

                        # ------------------------------------------------
                        # REPLICA DETAILS
                        # ------------------------------------------------

                        block_volume_replicas = []

                        try:

                            replicas_response = (
                                blockstorage_client.list_block_volume_replicas(
                                    block_volume_id=volume_id
                                )
                            )

                            replicas = replicas_response.data

                            for replica in replicas:

                                replica_data = {

                                    "id": _get(
                                        replica,
                                        "id",
                                        ""
                                    ),

                                    "region": _get(
                                        replica,
                                        "region",
                                        ""
                                    ),

                                    "availability_domain": _get(
                                        replica,
                                        "availability_domain",
                                        ""
                                    ),

                                    "lifecycle_state": _get(
                                        replica,
                                        "lifecycle_state",
                                        ""
                                    ),

                                    "time_created": _get(
                                        replica,
                                        "time_created",
                                        None
                                    )
                                }

                                block_volume_replicas.append(
                                    replica_data
                                )

                        except Exception:
                            block_volume_replicas = []

                        # ------------------------------------------------
                        # TAGS
                        #
                        # Do NOT pass these into OCI constructors.
                        # We only read them from the returned object.
                        # ------------------------------------------------

                        defined_tags = _get(
                            volume,
                            "defined_tags",
                            {}
                        )

                        freeform_tags = _get(
                            volume,
                            "freeform_tags",
                            {}
                        )

                        # ------------------------------------------------
                        # RESOURCE
                        # ------------------------------------------------

                        resource = {

                            # Basic
                            "service":
                                "Block Storage",

                            "resource_type":
                                "Block Volume",

                            "name":
                                display_name,

                            "display_name":
                                display_name,

                            "id":
                                volume_id,

                            "ocid":
                                volume_id,

                            # Location
                            "region":
                                region,

                            "availability_domain":
                                availability_domain,

                            "compartment_id":
                                compartment_id,

                            "compartment_name":
                                compartment_name,

                            # State
                            "lifecycle_state":
                                lifecycle_state,

                            "state":
                                lifecycle_state,

                            # ------------------------------------------------
                            # SIZE
                            # ------------------------------------------------

                            "size_in_gbs":
                                size_in_gbs,

                            "size_gb":
                                size_in_gbs,

                            "size":
                                size_in_gbs,

                            "size_in_mbs":
                                size_in_mbs,

                            "volume_size_gb":
                                size_in_gbs,

                            "volume_size":
                                size_in_gbs,

                            # ------------------------------------------------
                            # PERFORMANCE
                            # ------------------------------------------------

                            "vpus_per_gb":
                                vpus_per_gb,

                            "vpu_per_gb":
                                vpus_per_gb,

                            "vp_us_per_gb":
                                vpus_per_gb,

                            "auto_tuned_vpus_per_gb":
                                auto_tuned_vpus_per_gb,

                            "is_auto_tune_enabled":
                                is_auto_tune_enabled,

                            # ------------------------------------------------
                            # VOLUME TYPE
                            # ------------------------------------------------

                            "volume_type":
                                volume_type,

                            # ------------------------------------------------
                            # ENCRYPTION
                            # ------------------------------------------------

                            "kms_key_id":
                                kms_key_id,

                            "kms_key_ocid":
                                kms_key_id,

                            "encryption_in_transit_type":
                                encryption_in_transit_type,

                            # ------------------------------------------------
                            # SOURCE
                            # ------------------------------------------------

                            "source_type":
                                source_type,

                            "source_volume_id":
                                source_volume_id,

                            "source_volume_ocid":
                                source_volume_id,

                            "source_volume_size_gb":
                                source_volume_size,

                            # ------------------------------------------------
                            # BACKUP
                            # ------------------------------------------------

                            "backup_policy_id":
                                backup_policy_id,

                            "backup_policy_ocid":
                                backup_policy_id,

                            # ------------------------------------------------
                            # VOLUME GROUP
                            # ------------------------------------------------

                            "volume_group_id":
                                volume_group_id,

                            "volume_group_ocid":
                                volume_group_id,

                            # ------------------------------------------------
                            # FLAGS
                            # ------------------------------------------------

                            "is_hydrated":
                                is_hydrated,

                            "is_reservable":
                                is_reservable,

                            "is_read_only":
                                is_read_only,

                            "read_only":
                                is_read_only,

                            "is_volume_group_clone":
                                is_volume_group_clone,

                            # ------------------------------------------------
                            # REPLICATION
                            # ------------------------------------------------

                            "replicas":
                                block_volume_replicas,

                            "replica_count":
                                len(
                                    block_volume_replicas
                                ),

                            # ------------------------------------------------
                            # TIME
                            # ------------------------------------------------

                            "time_created":
                                time_created,

                            "created":
                                time_created,

                            # ------------------------------------------------
                            # TAGS
                            # ------------------------------------------------

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
                            f"    ERROR processing Block Volume "
                            f"{display_name}: {exc}"
                        )

        except Exception as exc:

            print(
                f"  ERROR collecting Block Volume "
                f"region {region}: {exc}"
            )

    print(
        f"Block Volumes: {len(resources)} resources found"
    )

    return resources
