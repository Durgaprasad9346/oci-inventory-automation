import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_dhcp_options(config):
    """
    Collect all OCI DHCP Options across:
        - All subscribed regions
        - All accessible compartments

    Collects:
        - Resource information
        - Creation date
        - OCI Defined Tags
        - Existing DHCP Options details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing DHCP Options region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        virtual_network_client = oci.core.VirtualNetworkClient(
            region_config
        )

        for compartment in compartments:

            try:

                dhcp_options = (
                    oci.pagination.list_call_get_all_results(
                        virtual_network_client.list_dhcp_options,
                        compartment_id=compartment["id"],
                    )
                )

                for dhcp in dhcp_options.data:

                    resources.append(
                        Resource(
                            service="DHCP Options",
                            resource_type="DHCP Options",
                            name=getattr(
                                dhcp,
                                "display_name",
                                "",
                            ),
                            ocid=getattr(
                                dhcp,
                                "id",
                                "",
                            ),
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=getattr(
                                dhcp,
                                "lifecycle_state",
                                "",
                            ),

                            # -----------------------------------------
                            # Creation Date
                            # -----------------------------------------

                            time_created=getattr(
                                dhcp,
                                "time_created",
                                None,
                            ),

                            # -----------------------------------------
                            # OCI Defined Tags
                            # -----------------------------------------

                            defined_tags=getattr(
                                dhcp,
                                "defined_tags",
                                None,
                            ),

                            # -----------------------------------------
                            # Existing DHCP Options details
                            # -----------------------------------------

                            details={
                                "vcn_id": getattr(
                                    dhcp,
                                    "vcn_id",
                                    "",
                                ),
                                "options": getattr(
                                    dhcp,
                                    "options",
                                    "",
                                ),
                            },
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR collecting DHCP Options "
                    f"from compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
