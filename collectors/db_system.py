import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_db_systems(config):
    """
    Collect all OCI DB Systems across:
        - All subscribed regions
        - All accessible compartments

    Collects:
        - Resource information
        - Creation date
        - OCI Defined Tags
        - Existing DB System details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing DB System region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        database_client = oci.database.DatabaseClient(
            region_config
        )

        for compartment in compartments:

            try:

                db_systems = (
                    oci.pagination.list_call_get_all_results(
                        database_client.list_db_systems,
                        compartment_id=compartment["id"],
                    )
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
                            # Existing DB System details
                            # -----------------------------------------

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
                                "shape_config": getattr(
                                    db_system,
                                    "shape_config",
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
                                "database_edition": getattr(
                                    db_system,
                                    "database_edition",
                                    "",
                                ),
                                "db_home_id": getattr(
                                    db_system,
                                    "db_home_id",
                                    "",
                                ),
                                "version": getattr(
                                    db_system,
                                    "version",
                                    "",
                                ),
                                "subnet_id": getattr(
                                    db_system,
                                    "subnet_id",
                                    "",
                                ),
                                "backup_subnet_id": getattr(
                                    db_system,
                                    "backup_subnet_id",
                                    "",
                                ),
                                "listener_port": getattr(
                                    db_system,
                                    "listener_port",
                                    "",
                                ),
                                "hostname": getattr(
                                    db_system,
                                    "hostname",
                                    "",
                                ),
                            },
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR collecting DB Systems "
                    f"from compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
