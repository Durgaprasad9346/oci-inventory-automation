import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_compute(config):
    """
    Collect all OCI Compute instances
    from all accessible compartments
    across all subscribed regions.

    For each Compute instance we collect:

    - Resource name
    - Resource type
    - OCID
    - Compartment
    - Region
    - Lifecycle state
    - Creation date
    - Defined tags
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(f"  Processing Compute region: {region}")

        region_config = config.copy()
        region_config["region"] = region

        compute_client = oci.core.ComputeClient(
            region_config
        )

        for compartment in compartments:

            try:

                instances = (
                    oci.pagination.list_call_get_all_results(
                        compute_client.list_instances,
                        compartment["id"],
                    )
                )

                for instance in instances.data:

                    resources.append(
                        Resource(
                            service="Compute",
                            resource_type="Instance",
                            name=instance.display_name,
                            ocid=instance.id,
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=getattr(
                                instance,
                                "lifecycle_state",
                                "",
                            ),

                            # Creation date
                            time_created=getattr(
                                instance,
                                "time_created",
                                None,
                            ),

                            # OCI Defined Tags
                            defined_tags=getattr(
                                instance,
                                "defined_tags",
                                None,
                            ),

                            details={
                                "availability_domain": getattr(
                                    instance,
                                    "availability_domain",
                                    "",
                                ),
                                "shape": getattr(
                                    instance,
                                    "shape",
                                    "",
                                ),
                                "fault_domain": getattr(
                                    instance,
                                    "fault_domain",
                                    "",
                                ),
                                "subnet_id": getattr(
                                    instance,
                                    "subnet_id",
                                    "",
                                ),
                                "vnic_id": getattr(
                                    instance,
                                    "vnic_id",
                                    "",
                                ),
                            },
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR in compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
