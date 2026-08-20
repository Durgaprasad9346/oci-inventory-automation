import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_dns(config):
    """
    Collect OCI DNS zones across all subscribed regions
    and accessible compartments.
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(f"  Processing DNS region: {region}")

        region_config = config.copy()
        region_config["region"] = region

        dns_client = oci.dns.DnsClient(
            region_config
        )

        for compartment in compartments:

            zones = oci.pagination.list_call_get_all_results(
                dns_client.list_zones,
                compartment_id=compartment["id"],
            )

            for zone in zones.data:

                resources.append(
                    Resource(
                        service="DNS",
                        resource_type="DNS Zone",
                        name=zone.name,
                        ocid=zone.id,
                        compartment_id=compartment["id"],
                        compartment_name=compartment["name"],
                        region=region,
                        state=getattr(
                            zone,
                            "lifecycle_state",
                            "",
                        ),
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
                        },
                    )
                )

    return resources
