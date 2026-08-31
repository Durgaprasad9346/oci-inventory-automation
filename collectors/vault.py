import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_vault(config):
    """
    Collect all OCI Vaults across:
        - All subscribed regions
        - All accessible compartments

    Collects:
        - Vault name
        - OCID
        - Compartment
        - Region
        - Lifecycle state
        - Creation date
        - OCI Defined Tags
        - Vault details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(f"  Processing Vault region: {region}")

        region_config = config.copy()
        region_config["region"] = region

        # ---------------------------------------------------------
        # IMPORTANT:
        # Vaults are listed using KmsVaultClient.
        # VaultsClient is for Secrets operations.
        # ---------------------------------------------------------

        kms_vault_client = oci.key_management.KmsVaultClient(
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

                for vault in vaults.data:

                    resources.append(
                        Resource(
                            service="Key Management",
                            resource_type="Vault",
                            name=getattr(
                                vault,
                                "display_name",
                                "",
                            ),
                            ocid=getattr(
                                vault,
                                "id",
                                "",
                            ),
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=getattr(
                                vault,
                                "lifecycle_state",
                                "",
                            ),

                            # -------------------------------------------------
                            # Creation Date
                            # -------------------------------------------------

                            time_created=getattr(
                                vault,
                                "time_created",
                                None,
                            ),

                            # -------------------------------------------------
                            # OCI Defined Tags
                            # -------------------------------------------------

                            defined_tags=getattr(
                                vault,
                                "defined_tags",
                                None,
                            ),

                            # -------------------------------------------------
                            # Vault details
                            # -------------------------------------------------

                            details={
                                "vault_type": getattr(
                                    vault,
                                    "vault_type",
                                    "",
                                ),
                                "crypto_endpoint": getattr(
                                    vault,
                                    "crypto_endpoint",
                                    "",
                                ),
                                "management_endpoint": getattr(
                                    vault,
                                    "management_endpoint",
                                    "",
                                ),
                                "is_primary": getattr(
                                    vault,
                                    "is_primary",
                                    "",
                                ),
                                "external_key_manager_metadata": getattr(
                                    vault,
                                    "external_key_manager_metadata",
                                    "",
                                ),
                                "lifecycle_details": getattr(
                                    vault,
                                    "lifecycle_details",
                                    "",
                                ),
                                "time_of_deletion": getattr(
                                    vault,
                                    "time_of_deletion",
                                    None,
                                ),
                            },
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR collecting Vault from compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
