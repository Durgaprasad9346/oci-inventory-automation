import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_db_system(config):
    """
    Collect all OCI DB Systems across all subscribed
    regions and accessible compartments.
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(f"  Processing DB System region: {region}")

        region_config = config.copy()
        region_config["region"] = region

        database_client = oci.database.DatabaseClient(
            region_config
        )

        for compartment in compartments:

            db_systems = oci.pagination.list_call_get_all_results(
                database_client.list_db_systems,
                compartment_id=compartment["id"],
            )

            for db_system in db_systems.data:

                resources.append(
                    Resource(
                        service="DB Systems",
                        resource_type="DB System",
                        name=db_system.display_name,
                        ocid=db_system.id,
                        compartment_id=compartment["id"],
                        compartment_name=compartment["name"],
                        region=region,
                        state=db_system.lifecycle_state,
                        details={
                            "db_system_options": getattr(
                                db_system,
                                "db_system_options",
                                None,
                            ),
                            "shape": getattr(
                                db_system,
                                "shape",
                                "",
                            ),
                            "availability_domain": getattr(
                                db_system,
                                "availability_domain",
                                "",
                            ),
                            "cpu_core_count": getattr(
                                db_system,
                                "cpu_core_count",
                                "",
                            ),
                            "data_storage_size_in_gbs": getattr(
                                db_system,
                                "data_storage_size_in_gbs",
                                "",
                            ),
                            "node_count": getattr(
                                db_system,
                                "node_count",
                                "",
                            ),
                            "subnet_id": getattr(
                                db_system,
                                "subnet_id",
                                "",
                            ),
                        },
                    )
                )

    return resources
