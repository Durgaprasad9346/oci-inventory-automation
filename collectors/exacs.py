import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_exacs(config):
    """
    Collect OCI Exadata Cloud Service VM Clusters
    across all subscribed regions and accessible compartments.
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(f"  Processing ExaCS region: {region}")

        region_config = config.copy()
        region_config["region"] = region

        database_client = oci.database.DatabaseClient(
            region_config
        )

        for compartment in compartments:

            try:

                vm_clusters = (
                    oci.pagination.list_call_get_all_results(
                        database_client.list_cloud_vm_clusters,
                        compartment_id=compartment["id"],
                    )
                )

                for vm_cluster in vm_clusters.data:

                    resources.append(
                        Resource(
                            service="ExaCS",
                            resource_type="VM Cluster",
                            name=vm_cluster.display_name,
                            ocid=vm_cluster.id,
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=getattr(
                                vm_cluster,
                                "lifecycle_state",
                                "",
                            ),
                            details={
                                "shape": getattr(
                                    vm_cluster,
                                    "shape",
                                    "",
                                ),
                                "cpu_core_count": getattr(
                                    vm_cluster,
                                    "cpu_core_count",
                                    "",
                                ),
                                "memory_size_in_gbs": getattr(
                                    vm_cluster,
                                    "memory_size_in_gbs",
                                    "",
                                ),
                                "db_node_storage_size_in_gbs": getattr(
                                    vm_cluster,
                                    "db_node_storage_size_in_gbs",
                                    "",
                                ),
                                "exadata_infrastructure_id": getattr(
                                    vm_cluster,
                                    "cloud_exadata_infrastructure_id",
                                    "",
                                ),
                                "vm_cluster_type": getattr(
                                    vm_cluster,
                                    "vm_cluster_type",
                                    "",
                                ),
                                "time_created": getattr(
                                    vm_cluster,
                                    "time_created",
                                    "",
                                ),
                            },
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR collecting ExaCS VM clusters "
                    f"from compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
