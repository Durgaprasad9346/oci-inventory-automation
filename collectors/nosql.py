import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_nosql(config):
    """
    Collect all OCI NoSQL tables across:
        - All subscribed regions
        - All accessible compartments

    Collects:
        - Resource information
        - Creation date
        - OCI Defined Tags
        - Existing NoSQL details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing NoSQL region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        nosql_client = oci.nosql.NosqlClient(
            region_config
        )

        for compartment in compartments:

            try:

                tables = (
                    oci.pagination.list_call_get_all_results(
                        nosql_client.list_tables,
                        compartment_id=compartment["id"],
                    )
                )

                for table in tables.data:

                    resources.append(
                        Resource(
                            service="NoSQL Database",
                            resource_type="NoSQL Table",
                            name=getattr(
                                table,
                                "name",
                                "",
                            ),
                            ocid=getattr(
                                table,
                                "id",
                                "",
                            ),
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=getattr(
                                table,
                                "lifecycle_state",
                                "",
                            ),

                            # -----------------------------------------
                            # Creation Date
                            # -----------------------------------------

                            time_created=getattr(
                                table,
                                "time_created",
                                None,
                            ),

                            # -----------------------------------------
                            # OCI Defined Tags
                            # -----------------------------------------

                            defined_tags=getattr(
                                table,
                                "defined_tags",
                                None,
                            ),

                            # -----------------------------------------
                            # Existing NoSQL details
                            # -----------------------------------------

                            details={
                                "table_name": getattr(
                                    table,
                                    "name",
                                    "",
                                ),
                                "table_limits": getattr(
                                    table,
                                    "table_limits",
                                    "",
                                ),
                                "compartment_id": getattr(
                                    table,
                                    "compartment_id",
                                    compartment["id"],
                                ),
                                "ddl_statement": getattr(
                                    table,
                                    "ddl_statement",
                                    "",
                                ),
                                "is_auto_reclaimable": getattr(
                                    table,
                                    "is_auto_reclaimable",
                                    "",
                                ),
                                "freeform_tags": getattr(
                                    table,
                                    "freeform_tags",
                                    "",
                                ),
                            },
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR collecting NoSQL "
                    f"from compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
