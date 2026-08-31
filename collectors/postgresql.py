import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_postgresql(config):
    """
    Collect OCI Database with PostgreSQL DB Systems.

    Collects:
        - PostgreSQL DB System
        - OCID
        - Compartment
        - Region
        - Lifecycle State
        - Creation Date
        - OCI Defined Tags
        - OCI Freeform Tags
        - PostgreSQL-specific details
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

        # =========================================================
        # OCI Database with PostgreSQL client
        # =========================================================

        postgresql_client = oci.psql.PostgresqlClient(
            region_config
        )

        for compartment in compartments:

            try:

                # =================================================
                # List PostgreSQL DB Systems
                # =================================================

                response = (
                    oci.pagination.list_call_get_all_results(
                        postgresql_client.list_db_systems,
                        compartment_id=compartment["id"],
                    )
                )

                db_systems = response.data

                for db_system in db_systems:

                    db_system_id = getattr(
                        db_system,
                        "id",
                        "",
                    )

                    display_name = getattr(
                        db_system,
                        "display_name",
                        "",
                    )

                    # =================================================
                    # Get detailed DB System information
                    # =================================================

                    details = {}

                    if db_system_id:

                        try:

                            detail_response = (
                                postgresql_client.get_db_system(
                                    db_system_id=db_system_id
                                )
                            )

                            db_system_details = (
                                detail_response.data
                            )

                            # -----------------------------------------
                            # Convert SDK model to dictionary where
                            # possible.
                            # -----------------------------------------

                            if hasattr(
                                db_system_details,
                                "swagger_types",
                            ):

                                for field_name in (
                                    db_system_details.swagger_types
                                ):

                                    try:

                                        value = getattr(
                                            db_system_details,
                                            field_name,
                                            None,
                                        )

                                        if value is not None:

                                            details[
                                                field_name
                                            ] = value

                                    except Exception:
                                        pass

                            else:

                                if hasattr(
                                    db_system_details,
                                    "__dict__",
                                ):

                                    details.update(
                                        db_system_details.__dict__
                                    )

                        except Exception as detail_error:

                            print(
                                f"    WARNING getting PostgreSQL "
                                f"DB System details for "
                                f"{display_name}: "
                                f"{detail_error}"
                            )

                    # =================================================
                    # Build Resource
                    # =================================================

                    resources.append(
                        Resource(
                            service="PostgreSQL",
                            resource_type="PostgreSQL DB System",

                            name=display_name,

                            ocid=db_system_id,

                            compartment_id=(
                                compartment["id"]
                            ),

                            compartment_name=(
                                compartment["name"]
                            ),

                            region=region,

                            state=getattr(
                                db_system,
                                "lifecycle_state",
                                "",
                            ),

                            # =================================================
                            # Creation Date
                            # =================================================

                            time_created=getattr(
                                db_system,
                                "time_created",
                                None,
                            ),

                            # =================================================
                            # OCI Defined Tags
                            # =================================================

                            defined_tags=getattr(
                                db_system,
                                "defined_tags",
                                None,
                            ),

                            # =================================================
                            # OCI Freeform Tags
                            # =================================================

                            freeform_tags=getattr(
                                db_system,
                                "freeform_tags",
                                None,
                            ),

                            # =================================================
                            # PostgreSQL-specific details
                            # =================================================

                            details={
                                "db_version": getattr(
                                    db_system,
                                    "db_version",
                                    "",
                                ),

                                "system_role": getattr(
                                    db_system,
                                    "system_role",
                                    "",
                                ),

                                "description": getattr(
                                    db_system,
                                    "description",
                                    "",
                                ),

                                "shape": getattr(
                                    db_system,
                                    "shape",
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

                                "nsg_ids": getattr(
                                    db_system,
                                    "nsg_ids",
                                    "",
                                ),

                                "private_ip": getattr(
                                    db_system,
                                    "private_ip",
                                    "",
                                ),

                                "endpoint": getattr(
                                    db_system,
                                    "endpoint",
                                    "",
                                ),

                                "backup_policy": getattr(
                                    db_system,
                                    "backup_policy",
                                    "",
                                ),

                                "is_h_a": getattr(
                                    db_system,
                                    "is_h_a",
                                    "",
                                ),

                                "is_read_only": getattr(
                                    db_system,
                                    "is_read_only",
                                    "",
                                ),

                                "lifecycle_details": getattr(
                                    db_system,
                                    "lifecycle_details",
                                    "",
                                ),

                                "time_of_deletion": getattr(
                                    db_system,
                                    "time_of_deletion",
                                    None,
                                ),

                                "configuration_id": getattr(
                                    db_system,
                                    "configuration_id",
                                    "",
                                ),

                                "freeform_tags": getattr(
                                    db_system,
                                    "freeform_tags",
                                    None,
                                ),

                                "defined_tags": getattr(
                                    db_system,
                                    "defined_tags",
                                    None,
                                ),

                                "detailed_db_system": details,
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
