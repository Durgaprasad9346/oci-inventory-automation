import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_db_homes(config):
    """
    Collect all OCI DB Homes across:
        - All subscribed regions
        - All accessible compartments
        - All DB Systems

    Collects:
        - Resource information
        - Creation date
        - OCI Defined Tags
        - DB Home details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing DB Homes region: {region}"
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

                try:

                    db_homes = (
                        oci.pagination.list_call_get_all_results(
                            database_client.list_db_homes,
                            compartment_id=compartment["id"],
                            db_system_id=db_system_id,
                        )
                    )

                    for db_home in db_homes.data:

                        resources.append(
                            Resource(
                                service="DB Systems",
                                resource_type="DB Home",
                                name=getattr(
                                    db_home,
                                    "display_name",
                                    "",
                                ),
                                ocid=getattr(
                                    db_home,
                                    "id",
                                    "",
                                ),
                                compartment_id=compartment["id"],
                                compartment_name=compartment["name"],
                                region=region,
                                state=getattr(
                                    db_home,
                                    "lifecycle_state",
                                    "",
                                ),

                                # -----------------------------------------
                                # Creation Date
                                # -----------------------------------------

                                time_created=getattr(
                                    db_home,
                                    "time_created",
                                    None,
                                ),

                                # -----------------------------------------
                                # OCI Defined Tags
                                # -----------------------------------------

                                defined_tags=getattr(
                                    db_home,
                                    "defined_tags",
                                    None,
                                ),

                                # -----------------------------------------
                                # DB Home details
                                # -----------------------------------------

                                details={
                                    "db_system_id": db_system_id,
                                    "db_system_name": getattr(
                                        db_system,
                                        "display_name",
                                        "",
                                    ),
                                    "db_version": getattr(
                                        db_home,
                                        "db_version",
                                        "",
                                    ),
                                    "db_software_image_id": getattr(
                                        db_home,
                                        "db_software_image_id",
                                        "",
                                    ),
                                    "db_home_location": getattr(
                                        db_home,
                                        "db_home_location",
                                        "",
                                    ),
                                    "database_software_image_id": getattr(
                                        db_home,
                                        "database_software_image_id",
                                        "",
                                    ),
                                },
                            )
                        )

                except Exception as error:

                    print(
                        f"    ERROR collecting DB Homes from "
                        f"DB System "
                        f"{getattr(db_system, 'display_name', '')}: "
                        f"{error}"
                    )

    return resources
