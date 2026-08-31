import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_data_safe_private_endpoints(config):
    """
    Collect OCI Data Safe Private Endpoints across:
        - All subscribed regions
        - All accessible compartments

    Collects:
        - Private Endpoint information
        - Creation date
        - OCI Defined Tags
        - Resource-specific details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing Data Safe Private Endpoints region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        data_safe_client = oci.data_safe.DataSafeClient(
            region_config
        )

        for compartment in compartments:

            try:

                private_endpoints = (
                    oci.pagination.list_call_get_all_results(
                        data_safe_client.list_data_safe_private_endpoints,
                        compartment_id=compartment["id"],
                    )
                )

                for private_endpoint in private_endpoints.data:

                    resources.append(
                        Resource(
                            service="Data Safe",
                            resource_type="Private Endpoint",
                            name=getattr(
                                private_endpoint,
                                "display_name",
                                getattr(
                                    private_endpoint,
                                    "name",
                                    "",
                                ),
                            ),
                            ocid=getattr(
                                private_endpoint,
                                "id",
                                "",
                            ),
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=getattr(
                                private_endpoint,
                                "lifecycle_state",
                                "",
                            ),

                            # -----------------------------------------
                            # Creation Date
                            # -----------------------------------------

                            time_created=getattr(
                                private_endpoint,
                                "time_created",
                                None,
                            ),

                            # -----------------------------------------
                            # OCI Defined Tags
                            # -----------------------------------------

                            defined_tags=getattr(
                                private_endpoint,
                                "defined_tags",
                                None,
                            ),

                            # -----------------------------------------
                            # Private Endpoint details
                            # -----------------------------------------

                            details={
                                "vcn_id": getattr(
                                    private_endpoint,
                                    "vcn_id",
                                    "",
                                ),
                                "subnet_id": getattr(
                                    private_endpoint,
                                    "subnet_id",
                                    "",
                                ),
                                "private_ip": getattr(
                                    private_endpoint,
                                    "private_ip",
                                    "",
                                ),
                                "nsg_ids": getattr(
                                    private_endpoint,
                                    "nsg_ids",
                                    "",
                                ),
                                "description": getattr(
                                    private_endpoint,
                                    "description",
                                    "",
                                ),
                                "lifecycle_details": getattr(
                                    private_endpoint,
                                    "lifecycle_details",
                                    "",
                                ),
                            },
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR collecting Data Safe "
                    f"Private Endpoints from compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
