import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_secrets(config):
    """
    Collect all OCI Secrets across all subscribed regions
    and accessible compartments.
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(f"  Processing Secrets region: {region}")

        region_config = config.copy()
        region_config["region"] = region

        vaults_client = oci.key_management.KmsVaultClient(
            region_config
        )

        secrets_client = oci.secrets.SecretsClient(
            region_config
        )

        for compartment in compartments:

            vaults = oci.pagination.list_call_get_all_results(
                vaults_client.list_vaults,
                compartment_id=compartment["id"],
            )

            for vault in vaults.data:

                secrets = oci.pagination.list_call_get_all_results(
                    secrets_client.list_secrets,
                    compartment_id=compartment["id"],
                    vault_id=vault.id,
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
                            state=secret.lifecycle_state,
                            details={
                                "vault_id": vault.id,
                                "vault_name": vault.display_name,
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

    return resources
