import oci


def get_availability_domains(config, region):
    """
    Return all availability domains for a region.
    """

    region_config = config.copy()
    region_config["region"] = region

    identity_client = oci.identity.IdentityClient(
        region_config
    )

    tenancy_id = config["tenancy"]

    response = identity_client.list_availability_domains(
        tenancy_id
    )

    return [
        availability_domain.name
        for availability_domain in response.data
    ]
