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

            try:
                load_balancers = (
                    oci.pagination.list_call_get_all_results(
                        load_balancer_client.list_load_balancers,
                        compartment_id=compartment["id"],
                    )
                )

                for load_balancer in load_balancers.data:

                    ip_addresses = []

                    for ip_address in (
                        getattr(
                            load_balancer,
                            "ip_addresses",
                            []
                        ) or []
                    ):
                        ip_addresses.append(
                            getattr(
                                ip_address,
                                "ip_address",
                                ""
                            )
                        )

                    resources.append(
                        Resource(
                            service="Load Balancer",
                            resource_type="Load Balancer",
                            name=load_balancer.display_name,
                            ocid=load_balancer.id,
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=getattr(
                                load_balancer,
                                "lifecycle_state",
                                "",
                            ),
                            details={
                                "shape_name": getattr(
                                    load_balancer,
                                    "shape_name",
                                    "",
                                ),
                                "is_private": getattr(
                                    load_balancer,
                                    "is_private",
                                    "",
                                ),
                                "ip_addresses": ip_addresses,
                                "subnet_ids": getattr(
                                    load_balancer,
                                    "subnet_ids",
                                    [],
                                ),
                                "vcn_id": getattr(
                                    load_balancer,
                                    "vcn_id",
                                    "",
                                ),
                                "bandwidth_shape_name": getattr(
                                    load_balancer,
                                    "bandwidth_shape_name",
                                    "",
                                ),
                                "shape_details": getattr(
                                    load_balancer,
                                    "shape_details",
                                    None,
                                ),
                                "time_created": getattr(
                                    load_balancer,
                                    "time_created",
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
