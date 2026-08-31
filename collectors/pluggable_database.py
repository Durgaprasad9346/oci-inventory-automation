import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_pluggable_databases(config):
    """
    Collect all OCI Pluggable Databases across:
        - All subscribed regions
        - All accessible compartments
        - All DB Systems / Databases

    Collects:
        - Resource information
        - Creation date
        - OCI Defined Tags
        - PDB details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing Pluggable Databases region: {region}"
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

            except Exception as error:

                print(
                    f"    ERROR collecting DB Systems from "
                    f"compartment {compartment['name']}: {error}"
                )

                continue

            for db_system in db_systems.data:

                db_system_id = getattr(
                    db_system,
                    "id",
                    "",
                )

                if not db_system_id:
                    continue

                # -------------------------------------------------
                # Get databases belonging to this DB System
                # -------------------------------------------------

                try:

                    databases = (
                        oci.pagination.list_call_get_all_results(
                            database_client.list_databases,
                            compartment_id=compartment["id"],
                            db_system_id=db_system_id,
                        )
                    )

                except Exception as error:

                    print(
                        f"    ERROR collecting Databases from "
                        f"DB System "
                        f"{getattr(db_system, 'display_name', '')}: "
                        f"{error}"
                    )

                    continue

                for database in databases.data:

                    database_id = getattr(
                        database,
                        "id",
                        "",
                    )

                    if not database_id:
                        continue

                    # -------------------------------------------------
                    # Get Pluggable Databases
                    # -------------------------------------------------

                    try:

                        pdbs = (
                            oci.pagination.list_call_get_all_results(
                                database_client.list_pluggable_databases,
                                compartment_id=compartment["id"],
                                database_id=database_id,
                            )
                        )

                    except Exception as error:

                        print(
                            f"    ERROR collecting Pluggable "
                            f"Databases from Database "
                            f"{getattr(database, 'db_name', '')}: "
                            f"{error}"
                        )

                        continue

                    for pdb in pdbs.data:

                        resources.append(
                            Resource(
                                service="DB Systems",
                                resource_type="Pluggable Database",
                                name=getattr(
                                    pdb,
                                    "pdb_name",
                                    getattr(
                                        pdb,
                                        "display_name",
                                        "",
                                    ),
                                ),
                                ocid=getattr(
                                    pdb,
                                    "id",
                                    "",
                                ),
                                compartment_id=compartment["id"],
                                compartment_name=compartment["name"],
                                region=region,
                                state=getattr(
                                    pdb,
                                    "lifecycle_state",
                                    "",
                                ),

                                # -----------------------------------------
                                # Creation Date
                                # -----------------------------------------

                                time_created=getattr(
                                    pdb,
                                    "time_created",
                                    None,
                                ),

                                # -----------------------------------------
                                # OCI Defined Tags
                                # -----------------------------------------

                                defined_tags=getattr(
                                    pdb,
                                    "defined_tags",
                                    None,
                                ),

                                # -----------------------------------------
                                # PDB details
                                # -----------------------------------------

                                details={
                                    "db_system_id": db_system_id,
                                    "db_system_name": getattr(
                                        db_system,
                                        "display_name",
                                        "",
                                    ),
                                    "database_id": database_id,
                                    "database_name": getattr(
                                        database,
                                        "db_name",
                                        "",
                                    ),
                                    "pdb_name": getattr(
                                        pdb,
                                        "pdb_name",
                                        "",
                                    ),
                                    "pdb_node_level_details": getattr(
                                        pdb,
                                        "pdb_node_level_details",
                                        "",
                                    ),
                                    "connection_strings": getattr(
                                        pdb,
                                        "connection_strings",
                                        "",
                                    ),
                                    "open_mode": getattr(
                                        pdb,
                                        "open_mode",
                                        "",
                                    ),
                                    "lifecycle_details": getattr(
                                        pdb,
                                        "lifecycle_details",
                                        "",
                                    ),
                                },
                            )
                        )

    return resources
