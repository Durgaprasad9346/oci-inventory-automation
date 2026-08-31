import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_dns_resolvers(config):
    """
    Collect all OCI DNS Resolvers across:
        - All subscribed regions
        - All accessible compartments

    Collects:
        - Resource information
        - Creation date
        - OCI Defined Tags
        - Existing DNS Resolver details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing DNS Resolver region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        virtual_network_client = oci.core.VirtualNetworkClient(
            region_config
        )

        for compartment in compartments:

            try:

                resolvers = (
                    oci.pagination.list_call_get_all_results(
                        virtual_network_client.list_dhcp_options,
                        compartment_id=compartment["id"],
                    )
                )

                # -------------------------------------------------
                # DNS Resolver is associated with a VCN.
                #
                # Get VCNs first and retrieve their resolver
                # information where available.
                # -------------------------------------------------

                vcns = (
                    oci.pagination.list_call_get_all_results(
                        virtual_network_client.list_vcns,
                        compartment_id=compartment["id"],
                    )
                )

                for vcn in vcns.data:

                    resolver = getattr(
                        vcn,
                        "dns_label",
                        None,
                    )

                    # Skip VCNs without resolver-related information.
                    if resolver is None:
                        continue

                    details = {
                        "vcn_id": getattr(
                            vcn,
                            "id",
                            "",
                        ),
                        "vcn_name": getattr(
                            vcn,
                            "display_name",
                            "",
                        ),
                        "dns_label": getattr(
                            vcn,
                            "dns_label",
                            "",
                        ),
                    }

                    resources.append(
                        Resource(
                            service="DNS Resolver",
                            resource_type="DNS Resolver",
                            name=(
                                f"{getattr(vcn, 'display_name', '')}"
                                f" DNS Resolver"
                            ),
                            ocid=getattr(
                                vcn,
                                "id",
                                "",
                            ),
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=getattr(
                                vcn,
                                "lifecycle_state",
                                "",
                            ),
                            time_created=getattr(
                                vcn,
                                "time_created",
                                None,
                            ),
                            defined_tags=getattr(
                                vcn,
                                "defined_tags",
                                None,
                            ),
                            details=details,
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR collecting DNS Resolver "
                    f"from compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
