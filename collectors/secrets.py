import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_secrets(config):
    """
    Collect OCI Vault Secrets across:
        - All subscribed regions
        - All accessible compartments
        - All vaults

    Vaults are discovered using KmsVaultClient.
    Secrets are discovered using VaultsClient.
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(f"  Processing Secrets region: {region}")

        region_config = config.copy()
        region_config["region"] = region

        # ---------------------------------------------------------
        # KmsVaultClient = Vault management
        # ---------------------------------------------------------

        kms_vault_client = oci.key_management.KmsVaultClient(
            region_config
        )

        # ---------------------------------------------------------
        # VaultsClient = Secrets management
        # ---------------------------------------------------------

        secrets_client = oci.vault.VaultsClient(
            region_config
        )

        for compartment in compartments:

            try:

                vaults = (
                    oci.pagination.list_call_get_all_results(
                        kms_vault_client.list_vaults,
                        compartment_id=compartment["id"],
                    )
                )

            except Exception as error:

                print(
                    f"    ERROR collecting vaults from "
                    f"compartment {compartment['name']}: {error}"
                )

                continue

            for vault in vaults.data:

                vault_id = getattr(
                    vault,
                    "id",
                    "",
                )

                vault_name = getattr(
                    vault,
                    "display_name",
                    "",
                )

                if not vault_id:
                    continue

                try:

                    secrets = (
                        oci.pagination.list_call_get_all_results(
                            secrets_client.list_secrets,
                            compartment_id=compartment["id"],
                            vault_id=vault_id,
                        )
                    )

                    for secret in secrets.data:

                        resources.append(
                            Resource(
                                service="Secrets",
                                resource_type="Secret",
                                name=getattr(
                                    secret,
                                    "secret_name",
                                    getattr(
                                        secret,
                                        "name",
                                        "",
                                    ),
                                ),
                                ocid=getattr(
                                    secret,
                                    "id",
                                    "",
                                ),
                                compartment_id=compartment["id"],
                                compartment_name=compartment["name"],
                                region=region,
                                state=getattr(
                                    secret,
                                    "lifecycle_state",
                                    "",
                                ),

                                # -----------------------------------------
                                # Creation Date
                                # -----------------------------------------

                                time_created=getattr(
                                    secret,
                                    "time_created",
                                    None,
                                ),

                                # -----------------------------------------
                                # OCI Defined Tags
                                # -----------------------------------------

                                defined_tags=getattr(
                                    secret,
                                    "defined_tags",
                                    None,
                                ),

                                # -----------------------------------------
                                # Secret details
                                # -----------------------------------------

                                details={
                                    "vault_id": vault_id,
                                    "vault_name": vault_name,
                                    "key_id": getattr(
                                        secret,
                                        "key_id",
                                        "",
                                    ),
                                    "secret_name": getattr(
                                        secret,
                                        "secret_name",
                                        getattr(
                                            secret,
                                            "name",
                                            "",
                                        ),
                                    ),
                                    "description": getattr(
                                        secret,
                                        "description",
                                        "",
                                    ),
                                    "secret_rules": getattr(
                                        secret,
                                        "secret_rules",
                                        "",
                                    ),
                                    "time_of_deletion": getattr(
                                        secret,
                                        "time_of_deletion",
                                        None,
                                    ),
                                    "time_of_expiry": getattr(
                                        secret,
                                        "time_of_expiry",
                                        None,
                                    ),
                                },
                            )
                        )

                except Exception as error:

                    print(
                        f"    ERROR collecting secrets from "
                        f"vault {vault_name}: {error}"
                    )

    return resources
