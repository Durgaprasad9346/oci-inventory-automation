import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_dns_views(config):
    """
    Collect all OCI DNS Views across:
        - All subscribed regions
        - All accessible compartments

    Collects:
        - Resource information
        - Creation date
        - OCI Defined Tags
        - DNS scope
        - DNS View details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing DNS Views region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        dns_client = oci.dns.DnsClient(
            region_config
        )

        for compartment in compartments:

            try:

                views = (
                    oci.pagination.list_call_get_all_results(
                        dns_client.list_views,
                        compartment_id=compartment["id"],
                    )
                )

                for view in views.data:

                    resources.append(
                        Resource(
                            service="DNS",
                            resource_type="DNS View",
                            name=getattr(
                                view,
                                "name",
                                "",
                            ),
                            ocid=getattr(
                                view,
                                "id",
                                "",
                            ),
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=getattr(
                                view,
                                "lifecycle_state",
                                "",
                            ),

                            # -----------------------------------------
                            # Creation Date
                            # -----------------------------------------

                            time_created=getattr(
                                view,
                                "time_created",
                                None,
                            ),

                            # -----------------------------------------
                            # OCI Defined Tags
                            # -----------------------------------------

                            defined_tags=getattr(
                                view,
                                "defined_tags",
                                None,
                            ),

                            # -----------------------------------------
                            # Existing DNS View details
                            # -----------------------------------------

                            details={
                                "scope": getattr(
                                    view,
                                    "scope",
                                    "",
                                ),
                                "view_id": getattr(
                                    view,
                                    "id",
                                    "",
                                ),
                                "name": getattr(
                                    view,
                                    "name",
                                    "",
                                ),
                            },
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR collecting DNS Views "
                    f"from compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
