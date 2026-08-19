import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_file_storage(config):
    """
    Collect all OCI File Storage file systems across
    all subscribed regions and accessible compartments.
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(f"  Processing File Storage region: {region}")

        region_config = config.copy()
        region_config["region"] = region

        file_storage_client = oci.file_storage.FileStorageClient(
            region_config
        )

        for compartment in compartments:

            file_systems = oci.pagination.list_call_get_all_results(
                file_storage_client.list_file_systems,
                compartment_id=compartment["id"],
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
                        state=file_system.lifecycle_state,
                        details={
                            "availability_domain": (
                                file_system.availability_domain
                            ),
                            "mount_target_id": (
                                file_system.mount_target_id
                            ),
                            "size_in_gbs": (
                                file_system.size_in_gbs
                            ),
                            "metered_bytes": (
                                file_system.metered_bytes
                            ),
                            "kms_key_id": (
                                file_system.kms_key_id
                            ),
                            "filesystem_snapshot_policy_id": (
                                file_system.filesystem_snapshot_policy_id
                            ),
                        },
                    )
                )

    return resources
