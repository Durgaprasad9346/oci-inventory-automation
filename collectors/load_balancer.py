import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_load_balancer(config):
    """
    Collect all OCI Load Balancers across:
        - All subscribed regions
        - All accessible compartments

    Collects:
        - Resource information
        - Creation date
        - OCI Defined Tags
        - Existing Load Balancer details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing Load Balancer region: {region}"
        )

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

                            # -----------------------------------------
                            # Creation Date
                            # -----------------------------------------

                            time_created=getattr(
                                load_balancer,
                                "time_created",
                                None,
                            ),

                            # -----------------------------------------
                            # OCI Defined Tags
                            # -----------------------------------------

                            defined_tags=getattr(
                                load_balancer,
                                "defined_tags",
                                None,
                            ),

                            # -----------------------------------------
                            # Existing Load Balancer details
                            # -----------------------------------------

                            details={
                                "ip_addresses": getattr(
                                    load_balancer,
                                    "ip_addresses",
                                    "",
                                ),
                                "shape_name": getattr(
                                    load_balancer,
                                    "shape_name",
                                    "",
                                ),
                                "shape_details": getattr(
                                    load_balancer,
                                    "shape_details",
                                    "",
                                ),
                                "is_private": getattr(
                                    load_balancer,
                                    "is_private",
                                    "",
                                ),
                                "subnet_ids": getattr(
                                    load_balancer,
                                    "subnet_ids",
                                    "",
                                ),
                                "network_security_group_ids": getattr(
                                    load_balancer,
                                    "network_security_group_ids",
                                    "",
                                ),
                                "backend_sets": getattr(
                                    load_balancer,
                                    "backend_sets",
                                    "",
                                ),
                                "listeners": getattr(
                                    load_balancer,
                                    "listeners",
                                    "",
                                ),
                                "rule_sets": getattr(
                                    load_balancer,
                                    "rule_sets",
                                    "",
                                ),
                            },
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR collecting Load Balancer "
                    f"from compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
