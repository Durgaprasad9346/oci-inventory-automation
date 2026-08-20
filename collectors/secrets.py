import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_secrets(config):
    """
    Collect all OCI Secrets metadata across all subscribed
    regions and accessible compartments.

    Secret values are NEVER retrieved.
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(f"  Processing Secrets region: {region}")

        region_config = config.copy()
        region_config["region"] = region

        vault_client = oci.vault.VaultsClient(
            region_config
        )

        for compartment in compartments:

            try:
                secrets = (
                    oci.pagination.list_call_get_all_results(
                        vault_client.list_secrets,
                        compartment_id=compartment["id"],
                    )
                )

                for secret in secrets.data:

                    resources.append(
                        Resource(
                            service="Secrets",
                            resource_type="Secret",
                            name=secret.secret_name,
                            ocid=secret.id,
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=getattr(
                                secret,
                                "lifecycle_state",
                                "",
                            ),
                            details={
                                "vault_id": getattr(
                                    secret,
                                    "vault_id",
                                    "",
                                ),
                                "key_id": getattr(
                                    secret,
                                    "key_id",
                                    "",
                                ),
                                "time_created": getattr(
                                    secret,
                                    "time_created",
                                    "",
                                ),
                                "time_of_deletion": getattr(
                                    secret,
                                    "time_of_deletion",
                                    "",
                                ),
                            },
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR in compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
