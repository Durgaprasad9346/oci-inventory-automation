import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_service_gateways(config):
    """
    Collect all OCI Service Gateways across:
        - All subscribed regions
        - All accessible compartments

    Collects:
        - Resource information
        - Creation date
        - OCI Defined Tags
        - Existing Service Gateway details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing Service Gateways region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        virtual_network_client = oci.core.VirtualNetworkClient(
            region_config
        )

        for compartment in compartments:

            try:

                service_gateways = (
                    oci.pagination.list_call_get_all_results(
                        virtual_network_client.list_service_gateways,
                        compartment_id=compartment["id"],
                    )
                )

                for service_gateway in service_gateways.data:

                    resources.append(
                        Resource(
                            service="Service Gateway",
                            resource_type="Service Gateway",
                            name=getattr(
                                service_gateway,
                                "display_name",
                                "",
                            ),
                            ocid=getattr(
                                service_gateway,
                                "id",
                                "",
                            ),
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=getattr(
                                service_gateway,
                                "lifecycle_state",
                                "",
                            ),

                            # -----------------------------------------
                            # Creation Date
                            # -----------------------------------------

                            time_created=getattr(
                                service_gateway,
                                "time_created",
                                None,
                            ),

                            # -----------------------------------------
                            # OCI Defined Tags
                            # -----------------------------------------

                            defined_tags=getattr(
                                service_gateway,
                                "defined_tags",
                                None,
                            ),

                            # -----------------------------------------
                            # Existing Service Gateway details
                            # -----------------------------------------

                            details={
                                "vcn_id": getattr(
                                    service_gateway,
                                    "vcn_id",
                                    "",
                                ),
                                "route_table_id": getattr(
                                    service_gateway,
                                    "route_table_id",
                                    "",
                                ),
                                "services": getattr(
                                    service_gateway,
                                    "services",
                                    "",
                                ),
                                "block_traffic": getattr(
                                    service_gateway,
                                    "block_traffic",
                                    "",
                                ),
                            },
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR collecting Service Gateways "
                    f"from compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
