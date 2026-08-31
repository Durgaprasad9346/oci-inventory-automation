import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_key_management(config):
    """
    Collect OCI Key Management resources.

    Collects:
        - Master Encryption Keys
        - Creation date
        - OCI Defined Tags
        - Vault information
        - Key details

    Vaults are discovered using KmsVaultClient.
    Keys are discovered using KmsManagementClient with the
    vault's management endpoint.
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing Keys region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        # ---------------------------------------------------------
        # KMS Vault client
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

                    # -------------------------------------------------
                    # Get vault details.
                    #
                    # The Vault object exposes the management endpoint
                    # required by KmsManagementClient.
                    # -------------------------------------------------

                    vault_response = (
                        kms_vault_client.get_vault(
                            vault_id=vault_id
                        )
                    )

                    vault_details = vault_response.data

                    management_endpoint = getattr(
                        vault_details,
                        "management_endpoint",
                        "",
                    )

                    if not management_endpoint:

                        print(
                            f"    ERROR collecting keys from vault "
                            f"{vault_name}: management endpoint "
                            f"not available"
                        )

                        continue

                    # -------------------------------------------------
                    # Key management client
                    # -------------------------------------------------

                    kms_management_client = (
                        oci.key_management.KmsManagementClient(
                            region_config,
                            service_endpoint=management_endpoint,
                        )
                    )

                    # -------------------------------------------------
                    # list_keys uses compartment_id.
                    # The vault is identified by the management
                    # endpoint, not by a vault_id kwarg.
                    # -------------------------------------------------

                    keys = (
                        oci.pagination.list_call_get_all_results(
                            kms_management_client.list_keys,
                            compartment_id=compartment["id"],
                        )
                    )

                    for key in keys.data:

                        resources.append(
                            Resource(
                                service="Key Management",
                                resource_type="Key",
                                name=getattr(
                                    key,
                                    "display_name",
                                    "",
                                ),
                                ocid=getattr(
                                    key,
                                    "id",
                                    "",
                                ),
                                compartment_id=compartment["id"],
                                compartment_name=compartment["name"],
                                region=region,
                                state=getattr(
                                    key,
                                    "lifecycle_state",
                                    "",
                                ),

                                # -----------------------------------------
                                # Creation Date
                                # -----------------------------------------

                                time_created=getattr(
                                    key,
                                    "time_created",
                                    None,
                                ),

                                # -----------------------------------------
                                # OCI Defined Tags
                                # -----------------------------------------

                                defined_tags=getattr(
                                    key,
                                    "defined_tags",
                                    None,
                                ),

                                # -----------------------------------------
                                # Key details
                                # -----------------------------------------

                                details={
                                    "vault_id": vault_id,
                                    "vault_name": vault_name,
                                    "management_endpoint": (
                                        management_endpoint
                                    ),
                                    "key_shape": getattr(
                                        key,
                                        "key_shape",
                                        "",
                                    ),
                                    "algorithm": getattr(
                                        getattr(
                                            key,
                                            "key_shape",
                                            None,
                                        ),
                                        "algorithm",
                                        "",
                                    ),
                                    "length": getattr(
                                        getattr(
                                            key,
                                            "key_shape",
                                            None,
                                        ),
                                        "length",
                                        "",
                                    ),
                                    "curve_id": getattr(
                                        getattr(
                                            key,
                                            "key_shape",
                                            None,
                                        ),
                                        "curve_id",
                                        "",
                                    ),
                                    "protection_mode": getattr(
                                        key,
                                        "protection_mode",
                                        "",
                                    ),
                                    "time_of_deletion": getattr(
                                        key,
                                        "time_of_deletion",
                                        None,
                                    ),
                                },
                            )
                        )

                except Exception as error:

                    print(
                        f"    ERROR collecting keys from vault "
                        f"{vault_name}: {error}"
                    )

    return resources
