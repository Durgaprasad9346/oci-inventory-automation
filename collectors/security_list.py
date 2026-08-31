import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_security_lists(config):
    """
    Collect all OCI Security Lists across:
        - All subscribed regions
        - All accessible compartments

    Collects:
        - Resource information
        - Creation date
        - OCI Defined Tags
        - Existing Security List details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing Security Lists region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        virtual_network_client = oci.core.VirtualNetworkClient(
            region_config
        )

        for compartment in compartments:

            try:

                security_lists = (
                    oci.pagination.list_call_get_all_results(
                        virtual_network_client.list_security_lists,
                        compartment_id=compartment["id"],
                    )
                )

                for security_list in security_lists.data:

                    resources.append(
                        Resource(
                            service="Security List",
                            resource_type="Security List",
                            name=getattr(
                                security_list,
                                "display_name",
                                "",
                            ),
                            ocid=getattr(
                                security_list,
                                "id",
                                "",
                            ),
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=getattr(
                                security_list,
                                "lifecycle_state",
                                "",
                            ),

                            # -----------------------------------------
                            # Creation Date
                            # -----------------------------------------

                            time_created=getattr(
                                security_list,
                                "time_created",
                                None,
                            ),

                            # -----------------------------------------
                            # OCI Defined Tags
                            # -----------------------------------------

                            defined_tags=getattr(
                                security_list,
                                "defined_tags",
                                None,
                            ),

                            # -----------------------------------------
                            # Existing Security List details
                            # -----------------------------------------

                            details={
                                "vcn_id": getattr(
                                    security_list,
                                    "vcn_id",
                                    "",
                                ),
                                "ingress_security_rules": getattr(
                                    security_list,
                                    "ingress_security_rules",
                                    "",
                                ),
                                "egress_security_rules": getattr(
                                    security_list,
                                    "egress_security_rules",
                                    "",
                                ),
                            },
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR collecting Security Lists "
                    f"from compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
