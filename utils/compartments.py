import oci


def get_compartments(config):
    """
    Return the tenancy root compartment and all accessible
    active compartments.
    """

    identity_client = oci.identity.IdentityClient(config)

    tenancy_id = config["tenancy"]

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

    return compartments
