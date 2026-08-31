import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_dns_resolvers(config):
    """
    Collect OCI DNS Resolver associations across:
        - All subscribed regions
        - All accessible compartments
        - All VCNs

    OCI exposes the DNS Resolver association through the VCN:
        get_vcn_dns_resolver_association(vcn_id)

    Collects:
        - DNS Resolver OCID
        - Associated VCN OCID
        - VCN name
        - Lifecycle state
        - OCI Defined Tags from the associated VCN
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

                vcns = (
                    oci.pagination.list_call_get_all_results(
                        virtual_network_client.list_vcns,
                        compartment_id=compartment["id"],
                    )
                )

            except Exception as error:

                print(
                    f"    ERROR collecting VCNs from "
                    f"compartment "
                    f"{compartment['name']}: {error}"
                )

                continue

            for vcn in vcns.data:

                vcn_id = getattr(
                    vcn,
                    "id",
                    "",
                )

                vcn_name = getattr(
                    vcn,
                    "display_name",
                    "",
                )

                if not vcn_id:
                    continue

                try:

                    response = (
                        virtual_network_client
                        .get_vcn_dns_resolver_association(
                            vcn_id=vcn_id
                        )
                    )

                    resolver = response.data

                    dns_resolver_id = getattr(
                        resolver,
                        "dns_resolver_id",
                        "",
                    )

                    lifecycle_state = getattr(
                        resolver,
                        "lifecycle_state",
                        "",
                    )

                    if not dns_resolver_id:
                        continue

                    resources.append(
                        Resource(
                            service="DNS Resolver",
                            resource_type="DNS Resolver",
                            name=(
                                f"{vcn_name} DNS Resolver"
                            ),
                            ocid=dns_resolver_id,
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=lifecycle_state,

                            # -----------------------------------------
                            # DNS Resolver does not expose its own
                            # creation timestamp through this
                            # association API.
                            # -----------------------------------------

                            time_created=getattr(
                                vcn,
                                "time_created",
                                None,
                            ),

                            # -----------------------------------------
                            # Defined Tags
                            #
                            # Resolver association itself doesn't
                            # expose defined_tags, so use the VCN's
                            # defined tags.
                            # -----------------------------------------

                            defined_tags=getattr(
                                vcn,
                                "defined_tags",
                                None,
                            ),

                            # -----------------------------------------
                            # DNS Resolver details
                            # -----------------------------------------

                            details={
                                "dns_resolver_id": dns_resolver_id,
                                "vcn_id": vcn_id,
                                "vcn_name": vcn_name,
                                "vcn_dns_label": getattr(
                                    vcn,
                                    "dns_label",
                                    "",
                                ),
                                "resolver_lifecycle_state": (
                                    lifecycle_state
                                ),
                            },
                        )
                    )

                except Exception as error:

                    print(
                        f"    ERROR collecting DNS Resolver "
                        f"for VCN "
                        f"{vcn_name}: {error}"
                    )

    return resources
