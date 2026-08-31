import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_secrets(config):
    """
    Collect OCI Secrets across:
        - All subscribed regions
        - All accessible compartments
        - All accessible vaults

    Secrets are listed through the VaultsClient
    management endpoint.

    Collects:
        - Resource information
        - Creation date
        - OCI Defined Tags
        - Existing Secret details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing Secrets region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        # -----------------------------------------------------
        # Vault management client
        # -----------------------------------------------------

        vault_client = oci.vault.VaultsClient(
            region_config
        )

        for compartment in compartments:

            # -------------------------------------------------
            # Get all vaults in the compartment
            # -------------------------------------------------

            try:

                vaults = (
                    oci.pagination.list_call_get_all_results(
                        vault_client.list_vaults,
                        compartment_id=compartment["id"],
                    )
                )

            except Exception as error:

                print(
                    f"    ERROR collecting vaults from "
                    f"compartment "
                    f"{compartment['name']}: {error}"
                )

                continue

            # -------------------------------------------------
            # Process every vault
            # -------------------------------------------------

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

                management_endpoint = getattr(
                    vault,
                    "management_endpoint",
                    None,
                )

                if not vault_id:

                    continue

                if not management_endpoint:

                    print(
                        f"    WARNING: Vault "
                        f"{vault_name} does not have "
                        f"a management endpoint. "
                        f"Skipping secrets."
                    )

                    continue

                try:

                    # -------------------------------------------------
                    # Create a VaultsClient using the vault-specific
                    # management endpoint.
                    # -------------------------------------------------

                    management_client = (
                        oci.vault.VaultsClient(
                            region_config,
                            service_endpoint=management_endpoint,
                        )
                    )

                    # -------------------------------------------------
                    # List secrets
                    # -------------------------------------------------

                    secrets = (
                        oci.pagination.list_call_get_all_results(
                            management_client.list_secrets,
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
                                    "",
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

                                # -------------------------------------
                                # Creation Date
                                # -------------------------------------

                                time_created=getattr(
                                    secret,
                                    "time_created",
                                    None,
                                ),

                                # -------------------------------------
                                # OCI Defined Tags
                                # -------------------------------------

                                defined_tags=getattr(
                                    secret,
                                    "defined_tags",
                                    None,
                                ),

                                # -------------------------------------
                                # Existing Secret details
                                # -------------------------------------

                                details={
                                    "vault_id": vault_id,
                                    "vault_name": vault_name,
                                    "key_id": getattr(
                                        secret,
                                        "key_id",
                                        "",
                                    ),
                                    "description": getattr(
                                        secret,
                                        "description",
                                        "",
                                    ),
                                    "time_of_deletion": getattr(
                                        secret,
                                        "time_of_deletion",
                                        None,
                                    ),
                                    "rotation_state": getattr(
                                        secret,
                                        "rotation_state",
                                        "",
                                    ),
                                    "secret_rules": getattr(
                                        secret,
                                        "secret_rules",
                                        "",
                                    ),
                                },
                            )
                        )

                except Exception as error:

                    print(
                        f"    ERROR collecting secrets "
                        f"from vault "
                        f"{vault_name}: {error}"
                    )

    return resources
