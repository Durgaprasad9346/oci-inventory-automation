import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_file_storage(config):
    """
    Collect all OCI File Storage File Systems across all
    subscribed regions, availability domains, and compartments.
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(f"  Processing File Storage region: {region}")

        region_config = config.copy()
        region_config["region"] = region

        identity_client = oci.identity.IdentityClient(
            region_config
        )

        file_storage_client = oci.file_storage.FileStorageClient(
            region_config
        )

        tenancy_id = region_config["tenancy"]

        # Get all Availability Domains
        try:
            availability_domains = (
                oci.pagination.list_call_get_all_results(
                    identity_client.list_availability_domains,
                    tenancy_id,
                )
            ).data
        except Exception as error:
            print(
                f"    ERROR getting Availability Domains "
                f"for region {region}: {error}"
            )
            continue

        for compartment in compartments:

            for availability_domain in availability_domains:

                try:

                    file_systems = (
                        oci.pagination.list_call_get_all_results(
                            file_storage_client.list_file_systems,
                            compartment_id=compartment["id"],
                            availability_domain=(
                                availability_domain.name
                            ),
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
                                details={
                                    "availability_domain": (
                                        getattr(
                                            file_system,
                                            "availability_domain",
                                            availability_domain.name,
                                        )
                                    ),
                                    "mount_target_id": getattr(
                                        file_system,
                                        "mount_target_id",
                                        "",
                                    ),
                                    "size_in_gbs": getattr(
                                        file_system,
                                        "size_in_gbs",
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
                                    "filesystem_snapshot_policy_id": (
                                        getattr(
                                            file_system,
                                            "filesystem_snapshot_policy_id",
                                            "",
                                        )
                                    ),
                                    "time_created": getattr(
                                        file_system,
                                        "time_created",
                                        "",
                                    ),
                                },
                            )
                        )

                except Exception as error:

                    print(
                        f"    ERROR in compartment "
                        f"{compartment['name']} "
                        f"AD {availability_domain.name}: {error}"
                    )

    return resources
