import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_postgresql(config):
    """
    Collect all OCI PostgreSQL database systems across
    all subscribed regions and accessible compartments.
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(f"  Processing PostgreSQL region: {region}")

        region_config = config.copy()
        region_config["region"] = region

        postgresql_client = oci.psql.PostgresqlClient(
            region_config
        )

        for compartment in compartments:

            db_systems = oci.pagination.list_call_get_all_results(
                postgresql_client.list_db_systems,
                compartment_id=compartment["id"],
            )

            for db_system in db_systems.data:

                resources.append(
                    Resource(
                        service="PostgreSQL",
                        resource_type="PostgreSQL DB System",
                        name=db_system.display_name,
                        ocid=db_system.id,
                        compartment_id=compartment["id"],
                        compartment_name=compartment["name"],
                        region=region,
                        state=db_system.lifecycle_state,
                        details={
                            "availability_domain": getattr(
                                db_system,
                                "availability_domain",
                                "",
                            ),
                            "shape": getattr(
                                db_system,
                                "shape",
                                "",
                            ),
                            "instance_count": getattr(
                                db_system,
                                "instance_count",
                                "",
                            ),
                            "storage_details": getattr(
                                db_system,
                                "storage_details",
                                None,
                            ),
                            "subnet_id": getattr(
                                db_system,
                                "subnet_id",
                                "",
                            ),
                            "system_type": getattr(
                                db_system,
                                "system_type",
                                "",
                            ),
                            "postgresql_version": getattr(
                                db_system,
                                "postgresql_version",
                                "",
                            ),
                        },
                    )
                )

    return resources
