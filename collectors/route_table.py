import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_route_tables(config):
    """
    Collect all OCI Route Tables across:
        - All subscribed regions
        - All accessible compartments

    Collects:
        - Resource information
        - Creation date
        - OCI Defined Tags
        - Existing Route Table details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing Route Tables region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        virtual_network_client = oci.core.VirtualNetworkClient(
            region_config
        )

        for compartment in compartments:

            try:

                route_tables = (
                    oci.pagination.list_call_get_all_results(
                        virtual_network_client.list_route_tables,
                        compartment_id=compartment["id"],
                    )
                )

                for route_table in route_tables.data:

                    resources.append(
                        Resource(
                            service="Route Table",
                            resource_type="Route Table",
                            name=getattr(
                                route_table,
                                "display_name",
                                "",
                            ),
                            ocid=getattr(
                                route_table,
                                "id",
                                "",
                            ),
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=getattr(
                                route_table,
                                "lifecycle_state",
                                "",
                            ),

                            # -----------------------------------------
                            # Creation Date
                            # -----------------------------------------

                            time_created=getattr(
                                route_table,
                                "time_created",
                                None,
                            ),

                            # -----------------------------------------
                            # OCI Defined Tags
                            # -----------------------------------------

                            defined_tags=getattr(
                                route_table,
                                "defined_tags",
                                None,
                            ),

                            # -----------------------------------------
                            # Existing Route Table details
                            # -----------------------------------------

                            details={
                                "vcn_id": getattr(
                                    route_table,
                                    "vcn_id",
                                    "",
                                ),
                                "route_rules": getattr(
                                    route_table,
                                    "route_rules",
                                    "",
                                ),
                            },
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR collecting Route Tables "
                    f"from compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
