import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions
from utils.availability_domains import get_availability_domains


def collect_file_storage(config):
    """
    Collect all OCI File Storage file systems across:
        - All subscribed regions
        - All availability domains
        - All accessible compartments

    Collects:
        - Resource information
        - Creation date
        - OCI Defined Tags
        - Existing File Storage details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing File Storage region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        file_storage_client = oci.file_storage.FileStorageClient(
            region_config
        )

        availability_domains = get_availability_domains(
            config,
            region,
        )

        for availability_domain in availability_domains:

            for compartment in compartments:

                try:

                    file_systems = (
                        oci.pagination.list_call_get_all_results(
                            file_storage_client.list_file_systems,
                            compartment_id=compartment["id"],
                            availability_domain=availability_domain,
                        )
                    )

                    for file_system in file_systems.data:

                        resources.append(
                            Resource(
                                service="File Storage",
                                resource_type="File System",
                                name=file_system.display_name,
                                ocid=file_system.id,
                                compartment_id=compartment["id"],
                                compartment_name=compartment["name"],
                                region=region,
                                state=getattr(
                                    file_system,
                                    "lifecycle_state",
                                    "",
                                ),

                                # -----------------------------------------
                                # Creation Date
                                # -----------------------------------------

                                time_created=getattr(
                                    file_system,
                                    "time_created",
                                    None,
                                ),

                                # -----------------------------------------
                                # OCI Defined Tags
                                # -----------------------------------------

                                defined_tags=getattr(
                                    file_system,
                                    "defined_tags",
                                    None,
                                ),

                                # -----------------------------------------
                                # Existing File Storage details
                                # -----------------------------------------

                                details={
                                    "availability_domain": getattr(
                                        file_system,
                                        "availability_domain",
                                        "",
                                    ),
                                    "export_set_id": getattr(
                                        file_system,
                                        "export_set_id",
                                        "",
                                    ),
                                    "metered_bytes": getattr(
                                        file_system,
                                        "metered_bytes",
                                        "",
                                    ),
                                    "kms_key_id": getattr(
                                        file_system,
                                        "kms_key_id",
                                        "",
                                    ),
                                    "filesystem_id": getattr(
                                        file_system,
                                        "filesystem_id",
                                        "",
                                    ),
                                    "mount_target_id": getattr(
                                        file_system,
                                        "mount_target_id",
                                        "",
                                    ),
                                },
                            )
                        )

                except Exception as error:

                    print(
                        f"    ERROR collecting File Storage "
                        f"from compartment "
                        f"{compartment['name']} "
                        f"in availability domain "
                        f"{availability_domain}: {error}"
                    )

    return resources
