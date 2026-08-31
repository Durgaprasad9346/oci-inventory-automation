import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_postgresql(config):
    """
    Collect all OCI PostgreSQL databases across:
        - All subscribed regions
        - All accessible compartments

    Collects:
        - Resource information
        - Creation date
        - OCI Defined Tags
        - Existing PostgreSQL details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing PostgreSQL region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        postgres_client = oci.psql.PostgresDbSystemClient(
            region_config
        )

        for compartment in compartments:

            try:

                db_systems = (
                    oci.pagination.list_call_get_all_results(
                        postgres_client.list_db_systems,
                        compartment_id=compartment["id"],
                    )
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
                            state=getattr(
                                db_system,
                                "lifecycle_state",
                                "",
                            ),

                            # -----------------------------------------
                            # Creation Date
                            # -----------------------------------------

                            time_created=getattr(
                                db_system,
                                "time_created",
                                None,
                            ),

                            # -----------------------------------------
                            # OCI Defined Tags
                            # -----------------------------------------

                            defined_tags=getattr(
                                db_system,
                                "defined_tags",
                                None,
                            ),

                            # -----------------------------------------
                            # Existing PostgreSQL details
                            # -----------------------------------------

                            details={
                                "availability_domain": getattr(
                                    db_system,
                                    "availability_domain",
                                    "",
                                ),
                                "subnet_id": getattr(
                                    db_system,
                                    "subnet_id",
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
                                "instance_ocpu_count": getattr(
                                    db_system,
                                    "instance_ocpu_count",
                                    "",
                                ),
                                "instance_memory_size_in_gbs": getattr(
                                    db_system,
                                    "instance_memory_size_in_gbs",
                                    "",
                                ),
                                "storage_details": getattr(
                                    db_system,
                                    "storage_details",
                                    "",
                                ),
                                "postgres_version": getattr(
                                    db_system,
                                    "db_version",
                                    "",
                                ),
                                "system_type": getattr(
                                    db_system,
                                    "system_type",
                                    "",
                                ),
                            },
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR collecting PostgreSQL "
                    f"from compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
