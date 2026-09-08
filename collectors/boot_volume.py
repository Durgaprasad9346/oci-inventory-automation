import oci


def collect_boot_volume(config):
    """
    Collect OCI Boot Volumes across configured regions and compartments.
    """

    resources = []

    try:
        tenancy_id = config["tenancy_id"]
        regions = config.get("regions", [])
        compartments = config.get("compartments", [])

        for region in regions:

            print(
                f"  Processing Boot Volume region: {region}"
            )

            try:
                blockstorage_client = oci.core.BlockstorageClient(
                    config,
                    region=region
                )

                for compartment in compartments:

                    compartment_id = compartment.get("id")
                    compartment_name = compartment.get(
                        "name",
                        compartment_id
                    )

                    try:

                        response = blockstorage_client.list_boot_volumes(
                            availability_domain=None,
                            compartment_id=compartment_id
                        )

                        for boot_volume in response.data:

                            resources.append(
                                {
                                    "service": "Boot Volume",
                                    "resource_type": "Boot Volume",

                                    "id": getattr(
                                        boot_volume,
                                        "id",
                                        ""
                                    ),

                                    "display_name": getattr(
                                        boot_volume,
                                        "display_name",
                                        ""
                                    ),

                                    "name": getattr(
                                        boot_volume,
                                        "display_name",
                                        ""
                                    ),

                                    "compartment_id": getattr(
                                        boot_volume,
                                        "compartment_id",
                                        compartment_id
                                    ),

                                    "compartment_name": (
                                        compartment_name
                                    ),

                                    "availability_domain": getattr(
                                        boot_volume,
                                        "availability_domain",
                                        ""
                                    ),

                                    "lifecycle_state": getattr(
                                        boot_volume,
                                        "lifecycle_state",
                                        ""
                                    ),

                                    "size_in_gbs": getattr(
                                        boot_volume,
                                        "size_in_gbs",
                                        0
                                    ),

                                    "vpus_per_gb": getattr(
                                        boot_volume,
                                        "vpus_per_gb",
                                        0
                                    ),

                                    "volume_performance": getattr(
                                        boot_volume,
                                        "vpus_per_gb",
                                        0
                                    ),

                                    "time_created": getattr(
                                        boot_volume,
                                        "time_created",
                                        None
                                    ),

                                    "is_hydrated": getattr(
                                        boot_volume,
                                        "is_hydrated",
                                        None
                                    ),

                                    "source_volume_backup_id": getattr(
                                        boot_volume,
                                        "source_volume_backup_id",
                                        ""
                                    ),

                                    "kms_key_id": getattr(
                                        boot_volume,
                                        "kms_key_id",
                                        ""
                                    ),

                                    "freeform_tags": getattr(
                                        boot_volume,
                                        "freeform_tags",
                                        {}
                                    ),

                                    "defined_tags": getattr(
                                        boot_volume,
                                        "defined_tags",
                                        {}
                                    ),

                                    "volume_group_id": getattr(
                                        boot_volume,
                                        "volume_group_id",
                                        ""
                                    ),

                                    "autotune_policies": getattr(
                                        boot_volume,
                                        "autotune_policies",
                                        []
                                    ),

                                    "policy": getattr(
                                        boot_volume,
                                        "policy",
                                        ""
                                    ),

                                    "source_type": getattr(
                                        boot_volume,
                                        "source_type",
                                        ""
                                    ),

                                    "source_id": getattr(
                                        boot_volume,
                                        "source_id",
                                        ""
                                    ),
                                }
                            )

                    except Exception as e:

                        print(
                            f"    ERROR collecting Boot Volumes "
                            f"from compartment "
                            f"{compartment_name}: {e}"
                        )

            except Exception as e:

                print(
                    f"  ERROR collecting Boot Volumes "
                    f"from region {region}: {e}"
                )

    except Exception as e:

        print(
            f"ERROR collecting Boot Volumes: {e}"
        )

    return resources
