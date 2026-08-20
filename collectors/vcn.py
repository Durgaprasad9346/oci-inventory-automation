import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_vcn(config):
    """
    Collect OCI VCN resources across all subscribed regions
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

            try:
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
                            state=getattr(
                                vcn,
                                "lifecycle_state",
                                "",
                            ),
                            details={
                                "cidr_block": getattr(
                                    vcn,
                                    "cidr_block",
                                    "",
                                ),
                                "cidr_blocks": getattr(
                                    vcn,
                                    "cidr_blocks",
                                    [],
                                ),
                                "ipv6_cidr_blocks": getattr(
                                    vcn,
                                    "ipv6_cidr_blocks",
                                    [],
                                ),
                                "is_ipv6_enabled": getattr(
                                    vcn,
                                    "is_ipv6_enabled",
                                    False,
                                ),
                                "dns_label": getattr(
                                    vcn,
                                    "vcn_domain_name",
                                    "",
                                ),
                                "default_dhcp_options_id": getattr(
                                    vcn,
                                    "default_dhcp_options_id",
                                    "",
                                ),
                                "default_route_table_id": getattr(
                                    vcn,
                                    "default_route_table_id",
                                    "",
                                ),
                                "default_security_list_id": getattr(
                                    vcn,
                                    "default_security_list_id",
                                    "",
                                ),
                                "time_created": getattr(
                                    vcn,
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
