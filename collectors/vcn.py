import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_vcn(config):
    """
    Collect all OCI VCNs across:
        - All subscribed regions
        - All accessible compartments

    Collects:
        - Resource information
        - Creation date
        - OCI Defined Tags
        - Existing VCN details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing VCN region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        virtual_network_client = oci.core.VirtualNetworkClient(
            region_config
        )

        for compartment in compartments:

            try:

                vcns = (
                    oci.pagination.list_call_get_all_results(
                        virtual_network_client.list_vcns,
                        compartment_id=compartment["id"],
                    )
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

                            # -----------------------------------------
                            # Creation Date
                            # -----------------------------------------

                            time_created=getattr(
                                vcn,
                                "time_created",
                                None,
                            ),

                            # -----------------------------------------
                            # OCI Defined Tags
                            # -----------------------------------------

                            defined_tags=getattr(
                                vcn,
                                "defined_tags",
                                None,
                            ),

                            # -----------------------------------------
                            # Existing VCN details
                            # -----------------------------------------

                            details={
                                "cidr_block": getattr(
                                    vcn,
                                    "cidr_block",
                                    "",
                                ),
                                "cidr_blocks": getattr(
                                    vcn,
                                    "cidr_blocks",
                                    "",
                                ),
                                "ipv6_cidr_blocks": getattr(
                                    vcn,
                                    "ipv6_cidr_blocks",
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
                                "dns_label": getattr(
                                    vcn,
                                    "dns_label",
                                    "",
                                ),
                            },
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR collecting VCN "
                    f"from compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
