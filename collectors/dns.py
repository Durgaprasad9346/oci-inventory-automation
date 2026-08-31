import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_dns(config):
    """
    Collect OCI DNS resources across:
        - All subscribed regions
        - All accessible compartments

    Collects DNS Zones.

    Collects:
        - Resource information
        - Creation date
        - OCI Defined Tags
        - Existing DNS details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing DNS region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        dns_client = oci.dns.DnsClient(
            region_config
        )

        for compartment in compartments:

            try:

                zones = (
                    oci.pagination.list_call_get_all_results(
                        dns_client.list_zones,
                        compartment_id=compartment["id"],
                    )
                )

                for zone in zones.data:

                    resources.append(
                        Resource(
                            service="DNS",
                            resource_type="DNS Zone",
                            name=getattr(
                                zone,
                                "name",
                                "",
                            ),
                            ocid=getattr(
                                zone,
                                "id",
                                "",
                            ),
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=getattr(
                                zone,
                                "lifecycle_state",
                                "",
                            ),

                            # -----------------------------------------
                            # Creation Date
                            # -----------------------------------------

                            time_created=getattr(
                                zone,
                                "time_created",
                                None,
                            ),

                            # -----------------------------------------
                            # OCI Defined Tags
                            # -----------------------------------------

                            defined_tags=getattr(
                                zone,
                                "defined_tags",
                                None,
                            ),

                            # -----------------------------------------
                            # Existing DNS details
                            # -----------------------------------------

                            details={
                                "zone_type": getattr(
                                    zone,
                                    "zone_type",
                                    "",
                                ),
                                "serial": getattr(
                                    zone,
                                    "serial",
                                    "",
                                ),
                                "nameservers": getattr(
                                    zone,
                                    "nameservers",
                                    "",
                                ),
                            },
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR collecting DNS "
                    f"from compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
