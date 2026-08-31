import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_network_security_groups(config):
    """
    Collect all OCI Network Security Groups (NSGs) across:
        - All subscribed regions
        - All accessible compartments

    Collects:
        - Resource information
        - Creation date
        - OCI Defined Tags
        - Existing NSG details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing Network Security Groups region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        virtual_network_client = oci.core.VirtualNetworkClient(
            region_config
        )

        for compartment in compartments:

            try:

                network_security_groups = (
                    oci.pagination.list_call_get_all_results(
                        virtual_network_client.list_network_security_groups,
                        compartment_id=compartment["id"],
                    )
                )

                for nsg in network_security_groups.data:

                    resources.append(
                        Resource(
                            service="Network Security Group",
                            resource_type="Network Security Group",
                            name=getattr(
                                nsg,
                                "display_name",
                                "",
                            ),
                            ocid=getattr(
                                nsg,
                                "id",
                                "",
                            ),
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=getattr(
                                nsg,
                                "lifecycle_state",
                                "",
                            ),

                            # -----------------------------------------
                            # Creation Date
                            # -----------------------------------------

                            time_created=getattr(
                                nsg,
                                "time_created",
                                None,
                            ),

                            # -----------------------------------------
                            # OCI Defined Tags
                            # -----------------------------------------

                            defined_tags=getattr(
                                nsg,
                                "defined_tags",
                                None,
                            ),

                            # -----------------------------------------
                            # Existing NSG details
                            # -----------------------------------------

                            details={
                                "vcn_id": getattr(
                                    nsg,
                                    "vcn_id",
                                    "",
                                ),
                                "time_created": getattr(
                                    nsg,
                                    "time_created",
                                    None,
                                ),
                            },
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR collecting Network Security "
                    f"Groups from compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
