import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_local_peering_gateways(config):
    """
    Collect all OCI Local Peering Gateways (LPGs) across:
        - All subscribed regions
        - All accessible compartments

    Collects:
        - Resource information
        - Creation date
        - OCI Defined Tags
        - Existing LPG details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing Local Peering Gateways region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        virtual_network_client = oci.core.VirtualNetworkClient(
            region_config
        )

        for compartment in compartments:

            try:

                lpgs = (
                    oci.pagination.list_call_get_all_results(
                        virtual_network_client.list_local_peering_gateways,
                        compartment_id=compartment["id"],
                    )
                )

                for lpg in lpgs.data:

                    resources.append(
                        Resource(
                            service="Local Peering Gateway",
                            resource_type="Local Peering Gateway",
                            name=getattr(
                                lpg,
                                "display_name",
                                "",
                            ),
                            ocid=getattr(
                                lpg,
                                "id",
                                "",
                            ),
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=getattr(
                                lpg,
                                "lifecycle_state",
                                "",
                            ),

                            # -----------------------------------------
                            # Creation Date
                            # -----------------------------------------

                            time_created=getattr(
                                lpg,
                                "time_created",
                                None,
                            ),

                            # -----------------------------------------
                            # OCI Defined Tags
                            # -----------------------------------------

                            defined_tags=getattr(
                                lpg,
                                "defined_tags",
                                None,
                            ),

                            # -----------------------------------------
                            # Existing LPG details
                            # -----------------------------------------

                            details={
                                "vcn_id": getattr(
                                    lpg,
                                    "vcn_id",
                                    "",
                                ),
                                "peering_status": getattr(
                                    lpg,
                                    "peering_status",
                                    "",
                                ),
                                "peering_status_details": getattr(
                                    lpg,
                                    "peering_status_details",
                                    "",
                                ),
                                "route_table_id": getattr(
                                    lpg,
                                    "route_table_id",
                                    "",
                                ),
                            },
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR collecting Local Peering "
                    f"Gateways from compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
