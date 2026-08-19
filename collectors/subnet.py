import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_subnet(config):
    """
    Collect all OCI Subnets across all subscribed regions
    and accessible compartments.
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(f"  Processing Subnet region: {region}")

        region_config = config.copy()
        region_config["region"] = region

        virtual_network_client = oci.core.VirtualNetworkClient(
            region_config
        )

        for compartment in compartments:

            subnets = oci.pagination.list_call_get_all_results(
                virtual_network_client.list_subnets,
                compartment_id=compartment["id"],
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
                        state=subnet.lifecycle_state,
                        details={
                            "vcn_id": subnet.vcn_id,
                            "cidr_block": subnet.cidr_block,
                            "availability_domain": (
                                subnet.availability_domain
                            ),
                            "route_table_id": (
                                subnet.route_table_id
                            ),
                            "security_list_ids": (
                                subnet.security_list_ids
                            ),
                            "dhcp_options_id": (
                                subnet.dhcp_options_id
                            ),
                            "dns_label": subnet.dns_label,
                            "subnet_domain_name": (
                                subnet.subnet_domain_name
                            ),
                            "prohibit_public_ip_on_vnic": (
                                subnet.prohibit_public_ip_on_vnic
                            ),
                        },
                    )
                )

    return resources
