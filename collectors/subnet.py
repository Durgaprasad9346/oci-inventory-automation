import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_subnet(config):
    """
    Collect all OCI Subnets across:
        - All subscribed regions
        - All accessible compartments

    Collects:
        - Resource information
        - Creation date
        - OCI Defined Tags
        - Existing Subnet details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing Subnet region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        virtual_network_client = oci.core.VirtualNetworkClient(
            region_config
        )

        for compartment in compartments:

            try:

                subnets = (
                    oci.pagination.list_call_get_all_results(
                        virtual_network_client.list_subnets,
                        compartment_id=compartment["id"],
                    )
                )

                for subnet in subnets.data:

                    resources.append(
                        Resource(
                            service="Subnet",
                            resource_type="Subnet",
                            name=subnet.display_name,
                            ocid=subnet.id,
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=getattr(
                                subnet,
                                "lifecycle_state",
                                "",
                            ),

                            # -----------------------------------------
                            # Creation Date
                            # -----------------------------------------

                            time_created=getattr(
                                subnet,
                                "time_created",
                                None,
                            ),

                            # -----------------------------------------
                            # OCI Defined Tags
                            # -----------------------------------------

                            defined_tags=getattr(
                                subnet,
                                "defined_tags",
                                None,
                            ),

                            # -----------------------------------------
                            # Existing Subnet details
                            # -----------------------------------------

                            details={
                                "cidr_block": getattr(
                                    subnet,
                                    "cidr_block",
                                    "",
                                ),
                                "ipv6_cidr_block": getattr(
                                    subnet,
                                    "ipv6_cidr_block",
                                    "",
                                ),
                                "vcn_id": getattr(
                                    subnet,
                                    "vcn_id",
                                    "",
                                ),
                                "availability_domain": getattr(
                                    subnet,
                                    "availability_domain",
                                    "",
                                ),
                                "dns_label": getattr(
                                    subnet,
                                    "dns_label",
                                    "",
                                ),
                                "route_table_id": getattr(
                                    subnet,
                                    "route_table_id",
                                    "",
                                ),
                                "security_list_ids": getattr(
                                    subnet,
                                    "security_list_ids",
                                    "",
                                ),
                                "dhcp_options_id": getattr(
                                    subnet,
                                    "dhcp_options_id",
                                    "",
                                ),
                                "prohibit_public_ip_on_vnic": getattr(
                                    subnet,
                                    "prohibit_public_ip_on_vnic",
                                    "",
                                ),
                                "virtual_router_ip": getattr(
                                    subnet,
                                    "virtual_router_ip",
                                    "",
                                ),
                                "virtual_router_mac": getattr(
                                    subnet,
                                    "virtual_router_mac",
                                    "",
                                ),
                            },
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR collecting Subnet "
                    f"from compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
