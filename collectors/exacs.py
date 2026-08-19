import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_exacs(config):
    """
    Collect all OCI Exadata Cloud Service (ExaCS)
    infrastructures across all subscribed regions
    and accessible compartments.
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(f"  Processing ExaCS region: {region}")

        region_config = config.copy()
        region_config["region"] = region

        database_client = oci.database.DatabaseClient(
            region_config
        )

        for compartment in compartments:

            infrastructures = (
                oci.pagination.list_call_get_all_results(
                    database_client.list_cloud_exadata_infrastructures,
                    compartment_id=compartment["id"],
                )
            )

            for infrastructure in infrastructures.data:

                resources.append(
                    Resource(
                        service="ExaCS",
                        resource_type="Exadata Infrastructure",
                        name=infrastructure.display_name,
                        ocid=infrastructure.id,
                        compartment_id=compartment["id"],
                        compartment_name=compartment["name"],
                        region=region,
                        state=infrastructure.lifecycle_state,
                        details={
                            "shape": getattr(
                                infrastructure,
                                "shape",
                                "",
                            ),
                            "availability_domain": getattr(
                                infrastructure,
                                "availability_domain",
                                "",
                            ),
                            "compute_count": getattr(
                                infrastructure,
                                "compute_count",
                                "",
                            ),
                            "storage_count": getattr(
                                infrastructure,
                                "storage_count",
                                "",
                            ),
                            "total_storage_size_in_gbs": getattr(
                                infrastructure,
                                "total_storage_size_in_gbs",
                                "",
                            ),
                            "cpu_count": getattr(
                                infrastructure,
                                "cpu_count",
                                "",
                            ),
                            "cloud_exadata_infrastructure_id": (
                                infrastructure.id
                            ),
                        },
                    )
                )

    return resources
