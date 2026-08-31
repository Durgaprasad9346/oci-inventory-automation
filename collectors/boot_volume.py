import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions
from utils.availability_domains import get_availability_domains


def collect_boot_volume(config):
    """
    Collect all OCI Boot Volumes across:
        - All subscribed regions
        - All availability domains
        - All accessible compartments

    Collects:
        - Resource information
        - Creation date
        - OCI Defined Tags
        - Existing Boot Volume details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing Boot Volume region: {region}"
        )

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

                try:

                    boot_volumes = (
                        oci.pagination.list_call_get_all_results(
                            blockstorage_client.list_boot_volumes,
                            availability_domain=availability_domain,
                            compartment_id=compartment["id"],
                        )
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
                                state=getattr(
                                    boot_volume,
                                    "lifecycle_state",
                                    "",
                                ),

                                # -----------------------------------------
                                # Creation Date
                                # -----------------------------------------

                                time_created=getattr(
                                    boot_volume,
                                    "time_created",
                                    None,
                                ),

                                # -----------------------------------------
                                # OCI Defined Tags
                                # -----------------------------------------

                                defined_tags=getattr(
                                    boot_volume,
                                    "defined_tags",
                                    None,
                                ),

                                # -----------------------------------------
                                # Existing details
                                # -----------------------------------------

                                details={
                                    "availability_domain": getattr(
                                        boot_volume,
                                        "availability_domain",
                                        "",
                                    ),
                                    "size_in_gbs": getattr(
                                        boot_volume,
                                        "size_in_gbs",
                                        "",
                                    ),
                                    "vpus_per_gb": getattr(
                                        boot_volume,
                                        "vpus_per_gb",
                                        "",
                                    ),
                                    "volume_group_id": getattr(
                                        boot_volume,
                                        "volume_group_id",
                                        "",
                                    ),
                                    "source_details": getattr(
                                        boot_volume,
                                        "source_details",
                                        "",
                                    ),
                                },
                            )
                        )

                except Exception as error:

                    print(
                        f"    ERROR collecting Boot Volume "
                        f"from compartment "
                        f"{compartment['name']}: {error}"
                    )

    return resources
