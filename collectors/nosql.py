import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_nosql(config):
    """
    Collect all OCI NoSQL tables across all subscribed
    regions and accessible compartments.
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(f"  Processing NoSQL region: {region}")

        region_config = config.copy()
        region_config["region"] = region

        nosql_client = oci.nosql.NosqlClient(
            region_config
        )

        for compartment in compartments:

            tables = oci.pagination.list_call_get_all_results(
                nosql_client.list_tables,
                compartment_id=compartment["id"],
            )

            for table in tables.data:

                resources.append(
                    Resource(
                        service="NoSQL Database",
                        resource_type="NoSQL Table",
                        name=table.name,
                        ocid=table.id,
                        compartment_id=compartment["id"],
                        compartment_name=compartment["name"],
                        region=region,
                        state=getattr(
                            table,
                            "lifecycle_state",
                            "",
                        ),
                        details={
                            "table_name": getattr(
                                table,
                                "name",
                                "",
                            ),
                            "table_state": getattr(
                                table,
                                "lifecycle_state",
                                "",
                            ),
                            "compartment_id": getattr(
                                table,
                                "compartment_id",
                                "",
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
                        },
                    )
                )

    return resources
