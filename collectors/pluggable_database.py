import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_pluggable_databases(config):
    """
    Collect OCI Pluggable Databases.

    Traversal:
        DB System
            -> DB Home
                -> Database
                    -> Pluggable Database
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

            compartment_id = compartment["id"]
            compartment_name = compartment["name"]

            # ====================================================
            # DB SYSTEMS
            # ====================================================

            try:

                db_systems = (
                    oci.pagination.list_call_get_all_results(
                        database_client.list_db_systems,
                        compartment_id=compartment_id,
                    )
                )

            except Exception as error:

                print(
                    "    ERROR collecting DB Systems "
                    f"from compartment {compartment_name}: {error}"
                )

                continue

            # ====================================================
            # DB SYSTEM LOOP
            # ====================================================

            for db_system in db_systems.data:

                db_system_id = getattr(
                    db_system,
                    "id",
                    None,
                )

                if not db_system_id:
                    continue

                db_system_name = getattr(
                    db_system,
                    "display_name",
                    "",
                )

                # =================================================
                # DB HOMES
                # =================================================

                try:

                    db_homes = (
                        oci.pagination.list_call_get_all_results(
                            database_client.list_db_homes,
                            compartment_id=compartment_id,
                            db_system_id=db_system_id,
                        )
                    )

                except Exception as error:

                    print(
                        "    ERROR collecting DB Homes "
                        f"from DB System {db_system_name}: {error}"
                    )

                    continue

                # =================================================
                # DB HOME LOOP
                # =================================================

                for db_home in db_homes.data:

                    db_home_id = getattr(
                        db_home,
                        "id",
                        None,
                    )

                    if not db_home_id:
                        continue

                    db_home_name = getattr(
                        db_home,
                        "display_name",
                        "",
                    )

                    # =============================================
                    # DATABASES
                    # =============================================

                    try:

                        databases = (
                            oci.pagination.list_call_get_all_results(
                                database_client.list_databases,
                                compartment_id=compartment_id,
                                db_home_id=db_home_id,
                            )
                        )

                    except Exception as error:

                        print(
                            "    ERROR collecting Databases "
                            f"from DB Home {db_home_name}: {error}"
                        )

                        continue

                    # =============================================
                    # DATABASE LOOP
                    # =============================================

                    for database in databases.data:

                        database_id = getattr(
                            database,
                            "id",
                            None,
                        )

                        if not database_id:
                            continue

                        database_name = getattr(
                            database,
                            "db_name",
                            "",
                        )

                        # =========================================
                        # PLUGGABLE DATABASES
                        # =========================================

                        try:

                            # IMPORTANT:
                            #
                            # Do NOT pass compartment_id here.
                            #
                            # OCI list_pluggable_databases()
                            # expects database_id for this API.
                            #
                            pdbs = (
                                oci.pagination.list_call_get_all_results(
                                    database_client.list_pluggable_databases,
                                    database_id=database_id,
                                )
                            )

                        except Exception as error:

                            print(
                                "    ERROR collecting Pluggable "
                                f"Databases from Database "
                                f"{database_name}: {error}"
                            )

                            continue

                        # =========================================
                        # PDB LOOP
                        # =========================================

                        for pdb in pdbs.data:

                            pdb_id = getattr(
                                pdb,
                                "id",
                                "",
                            )

                            pdb_name = getattr(
                                pdb,
                                "pdb_name",
                                None,
                            )

                            if not pdb_name:

                                pdb_name = getattr(
                                    pdb,
                                    "display_name",
                                    "",
                                )

                            resources.append(
                                Resource(
                                    service="DB Systems",

                                    resource_type=(
                                        "Pluggable Database"
                                    ),

                                    name=pdb_name,

                                    ocid=pdb_id,

                                    compartment_id=(
                                        compartment_id
                                    ),

                                    compartment_name=(
                                        compartment_name
                                    ),

                                    region=region,

                                    state=getattr(
                                        pdb,
                                        "lifecycle_state",
                                        "",
                                    ),

                                    time_created=getattr(
                                        pdb,
                                        "time_created",
                                        None,
                                    ),

                                    defined_tags=getattr(
                                        pdb,
                                        "defined_tags",
                                        None,
                                    ),

                                    freeform_tags=getattr(
                                        pdb,
                                        "freeform_tags",
                                        None,
                                    ),

                                    details={
                                        "db_system_id": (
                                            db_system_id
                                        ),

                                        "db_system_name": (
                                            db_system_name
                                        ),

                                        "db_home_id": (
                                            db_home_id
                                        ),

                                        "db_home_name": (
                                            db_home_name
                                        ),

                                        "database_id": (
                                            database_id
                                        ),

                                        "database_name": (
                                            database_name
                                        ),

                                        "pdb_name": (
                                            pdb_name
                                        ),

                                        "pdb_node_level_details": getattr(
                                            pdb,
                                            "pdb_node_level_details",
                                            None,
                                        ),

                                        "connection_strings": getattr(
                                            pdb,
                                            "connection_strings",
                                            None,
                                        ),

                                        "open_mode": getattr(
                                            pdb,
                                            "open_mode",
                                            None,
                                        ),

                                        "lifecycle_details": getattr(
                                            pdb,
                                            "lifecycle_details",
                                            None,
                                        ),
                                    },
                                )
                            )

    return resources
