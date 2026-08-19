import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_vault(config):
    """
    Collect all OCI Vaults across all subscribed regions
    and accessible compartments.
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(f"  Processing Vault region: {region}")

        region_config = config.copy()
        region_config["region"] = region

        kms_vault_client = oci.key_management.KmsVaultClient(
            region_config
        )

        for compartment in compartments:

            vaults = oci.pagination.list_call_get_all_results(
                kms_vault_client.list_vaults,
                compartment_id=compartment["id"],
            )

            for vault in vaults.data:

                resources.append(
                    Resource(
                        service="Vault",
                        resource_type="Vault",
                        name=vault.display_name,
                        ocid=vault.id,
                        compartment_id=compartment["id"],
                        compartment_name=compartment["name"],
                        region=region,
                        state=vault.lifecycle_state,
                        details={
                            "vault_type": getattr(
                                vault,
                                "vault_type",
                                "",
                            ),
                            "management_endpoint": getattr(
                                vault,
                                "management_endpoint",
                                "",
                            ),
                            "crypto_endpoint": getattr(
                                vault,
                                "crypto_endpoint",
                                "",
                            ),
                            "time_created": getattr(
                                vault,
                                "time_created",
                                "",
                            ),
                        },
                    )
                )

    return resources
