import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions
from utils.availability_domains import get_availability_domains


def collect_boot_volume(config):
    """
    Collect all OCI Boot Volumes across
    all subscribed regions, availability domains,
    and accessible compartments.
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(f"  Processing Boot Volume region: {region}")

        region_config = config.copy()
        region_config["region"] = region

        blockstorage_client = oci.core.BlockstorageClient(
            region_config
        )

        availability_domains = get_availability_domains(
            config,
            region,
        )

        for availability_domain in availability_domains:

            for compartment in compartments:

                boot_volumes = oci.pagination.list_call_get_all_results(
                    blockstorage_client.list_boot_volumes,
                    availability_domain=availability_domain,
                    compartment_id=compartment["id"],
                )

                for boot_volume in boot_volumes.data:

                    resources.append(
                        Resource(
                            service="Boot Volume",
                            resource_type="Boot Volume",
                            name=boot_volume.display_name,
                            ocid=boot_volume.id,
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=boot_volume.lifecycle_state,
                            details={
                                "availability_domain": (
                                    boot_volume.availability_domain
                                ),
                                "size_in_gbs": (
                                    boot_volume.size_in_gbs
                                ),
                            },
                        )
                    )

    return resources
