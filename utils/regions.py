import oci


def get_regions(config):
    """
    Return all READY regions subscribed to the tenancy.
    """

    identity_client = oci.identity.IdentityClient(config)

    tenancy_id = config["tenancy"]

    response = identity_client.list_region_subscriptions(
        tenancy_id
    )

    regions = []

    for subscription in response.data:

        if subscription.status == "READY":
            regions.append(subscription.region_name)

    return regions
