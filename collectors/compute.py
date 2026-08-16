import oci

from collectors.base import Resource


def collect_compute(config):
    """
    Collect OCI Compute instances.

    Returns:
        list[Resource]: List of compute instances.
    """

    compute_client = oci.core.ComputeClient(config)
    identity_client = oci.identity.IdentityClient(config)

    tenancy_id = config["tenancy"]

    resources = []

    # Get all compartments including the tenancy root
    compartments = [
        {
            "id": tenancy_id,
            "name": "root",
        }
    ]

    response = oci.pagination.list_call_get_all_results(
        identity_client.list_compartments,
        tenancy_id,
        compartment_id_in_subtree=True,
        access_level="ACCESSIBLE",
    )

    for compartment in response.data:
        if compartment.lifecycle_state == "ACTIVE":
            compartments.append(
                {
                    "id": compartment.id,
                    "name": compartment.name,
                }
            )

    # Collect instances from every compartment
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
