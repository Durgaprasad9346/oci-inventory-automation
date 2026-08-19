import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_vcn(config):
    """
    Collect all OCI VCNs across all subscribed regions
    and accessible compartments.
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(f"  Processing VCN region: {region}")

        region_config = config.copy()
        region_config["region"] = region

        virtual_network_client = oci.core.VirtualNetworkClient(
            region_config
        )

        for compartment in compartments:

            vcns = oci.pagination.list_call_get_all_results(
                virtual_network_client.list_vcns,
                compartment_id=compartment["id"],
            )

            for vcn in vcns.data:

                resources.append(
                    Resource(
                        service="VCN",
                        resource_type="VCN",
                        name=vcn.display_name,
                        ocid=vcn.id,
                        compartment_id=compartment["id"],
                        compartment_name=compartment["name"],
                        region=region,
                        state=vcn.lifecycle_state,
                        details={
                            "cidr_blocks": vcn.cidr_blocks,
                            "default_route_table_id": (
                                vcn.default_route_table_id
                            ),
                            "default_security_list_id": (
                                vcn.default_security_list_id
                            ),
                            "default_dhcp_options_id": (
                                vcn.default_dhcp_options_id
                            ),
                            "dns_label": vcn.dns_label,
                            "is_ipv6enabled": vcn.is_ipv6enabled,
                        },
                    )
                )

    return resources
