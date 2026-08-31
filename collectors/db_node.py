import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_db_nodes(config):
    """
    Collect all OCI DB Nodes across:
        - All subscribed regions
        - All accessible compartments
        - All DB Systems

    Collects:
        - Resource information
        - Creation date
        - OCI Defined Tags
        - DB Node details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing DB Nodes region: {region}"
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

                    db_nodes = (
                        oci.pagination.list_call_get_all_results(
                            database_client.list_db_nodes,
                            compartment_id=compartment["id"],
                            db_system_id=db_system_id,
                        )
                    )

                    for db_node in db_nodes.data:

                        resources.append(
                            Resource(
                                service="DB Systems",
                                resource_type="DB Node",
                                name=getattr(
                                    db_node,
                                    "hostname",
                                    "",
                                ),
                                ocid=getattr(
                                    db_node,
                                    "id",
                                    "",
                                ),
                                compartment_id=compartment["id"],
                                compartment_name=compartment["name"],
                                region=region,
                                state=getattr(
                                    db_node,
                                    "lifecycle_state",
                                    "",
                                ),

                                # -----------------------------------------
                                # Creation Date
                                # -----------------------------------------

                                time_created=getattr(
                                    db_node,
                                    "time_created",
                                    None,
                                ),

                                # -----------------------------------------
                                # OCI Defined Tags
                                # -----------------------------------------

                                defined_tags=getattr(
                                    db_node,
                                    "defined_tags",
                                    None,
                                ),

                                # -----------------------------------------
                                # DB Node details
                                # -----------------------------------------

                                details={
                                    "db_system_id": db_system_id,
                                    "db_system_name": getattr(
                                        db_system,
                                        "display_name",
                                        "",
                                    ),
                                    "hostname": getattr(
                                        db_node,
                                        "hostname",
                                        "",
                                    ),
                                    "fault_domain": getattr(
                                        db_node,
                                        "fault_domain",
                                        "",
                                    ),
                                    "availability_domain": getattr(
                                        db_node,
                                        "availability_domain",
                                        "",
                                    ),
                                    "vnic_id": getattr(
                                        db_node,
                                        "vnic_id",
                                        "",
                                    ),
                                    "backup_vnic_id": getattr(
                                        db_node,
                                        "backup_vnic_id",
                                        "",
                                    ),
                                    "software_storage_size_in_gb": getattr(
                                        db_node,
                                        "software_storage_size_in_gb",
                                        "",
                                    ),
                                },
                            )
                        )

                except Exception as error:

                    print(
                        f"    ERROR collecting DB Nodes from "
                        f"DB System "
                        f"{getattr(db_system, 'display_name', '')}: "
                        f"{error}"
                    )

    return resources
