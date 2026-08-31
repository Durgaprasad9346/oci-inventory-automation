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
        - Resource information
        - Creation date
        - OCI Defined Tags
        - Existing Vault details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing Vault region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        vault_client = oci.vault.VaultsClient(
            region_config
        )

        for compartment in compartments:

            try:

                vaults = (
                    oci.pagination.list_call_get_all_results(
                        vault_client.list_vaults,
                        compartment_id=compartment["id"],
                    )
                )

                for vault in vaults.data:

                    resources.append(
                        Resource(
                            service="Vault",
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

                            # -----------------------------------------
                            # Creation Date
                            # -----------------------------------------

                            time_created=getattr(
                                vault,
                                "time_created",
                                None,
                            ),

                            # -----------------------------------------
                            # OCI Defined Tags
                            # -----------------------------------------

                            defined_tags=getattr(
                                vault,
                                "defined_tags",
                                None,
                            ),

                            # -----------------------------------------
                            # Existing Vault details
                            # -----------------------------------------

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
                                "restored_from_vault_id": getattr(
                                    vault,
                                    "restored_from_vault_id",
                                    "",
                                ),
                            },
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR collecting Vault "
                    f"from compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
