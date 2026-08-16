import oci

from collectors.base import Resource
from utils.compartments import get_compartments


def collect_compute(config):
    """
    Collect all OCI Compute instances.
    """

    compute_client = oci.core.ComputeClient(config)

    compartments = get_compartments(config)

    resources = []

    for compartment in compartments:

        instances = oci.pagination.list_call_get_all_results(
            compute_client.list_instances,
            compartment["id"],
        )

        for instance in instances.data:

            resources.append(
                Resource(
                    service="Compute",
                    resource_type="Instance",
                    name=instance.display_name,
                    ocid=instance.id,
                    compartment_id=compartment["id"],
                    region=config["region"],
                    state=instance.lifecycle_state,
                )
            )

    return resources
