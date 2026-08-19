import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions
from utils.availability_domains import get_availability_domains


def collect_block_volume(config):
    """
    Collect all OCI Block Volumes across
    all subscribed regions, availability domains,
    and accessible compartments.
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(f"  Processing Block Volume region: {region}")

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

                volumes = oci.pagination.list_call_get_all_results(
                    blockstorage_client.list_volumes,
                    availability_domain=availability_domain,
                    compartment_id=compartment["id"],
                )

                for volume in volumes.data:

                    resources.append(
                        Resource(
                            service="Block Volume",
                            resource_type="Block Volume",
                            name=volume.display_name,
                            ocid=volume.id,
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=volume.lifecycle_state,
                            details={
                                "availability_domain": (
                                    volume.availability_domain
                                ),
                                "size_in_gbs": (
                                    volume.size_in_gbs
                                ),
                                "vpus_per_gb": (
                                    volume.vpus_per_gb
                                ),
                            },
                        )
                    )

    return resources
