import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_compute(config):
    """
    Collect all OCI Compute instances
    from all accessible compartments
    across all subscribed regions.
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

            instances = oci.pagination.list_call_get_all_results(
                compute_client.list_instances,
                compartment["id"],
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
                        state=instance.lifecycle_state,
                    )
                )

    return resources
