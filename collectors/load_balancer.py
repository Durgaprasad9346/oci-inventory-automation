import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_load_balancer(config):
    """
    Collect all OCI Load Balancers across all subscribed
    regions and accessible compartments.
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(f"  Processing Load Balancer region: {region}")

        region_config = config.copy()
        region_config["region"] = region

        load_balancer_client = oci.load_balancer.LoadBalancerClient(
            region_config
        )

        for compartment in compartments:

            load_balancers = oci.pagination.list_call_get_all_results(
                load_balancer_client.list_load_balancers,
                compartment_id=compartment["id"],
            )

            for load_balancer in load_balancers.data:

                resources.append(
                    Resource(
                        service="Load Balancer",
                        resource_type="Load Balancer",
                        name=load_balancer.display_name,
                        ocid=load_balancer.id,
                        compartment_id=compartment["id"],
                        compartment_name=compartment["name"],
                        region=region,
                        state=load_balancer.lifecycle_state,
                        details={
                            "ip_addresses": [
                                ip_address.ip_address
                                for ip_address in (
                                    load_balancer.ip_addresses or []
                                )
                            ],
                            "shape": load_balancer.shape,
                            "is_private": load_balancer.is_private,
                            "subnet_ids": (
                                load_balancer.subnet_ids
                            ),
                            "vcn_id": load_balancer.vcn_id,
                            "bandwidth_shape_name": (
                                load_balancer.bandwidth_shape_name
                            ),
                        },
                    )
                )

    return resources
