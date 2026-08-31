import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_keys(config):
    """
    Collect OCI KMS keys across:
        - All subscribed regions
        - All accessible compartments
        - All accessible vaults

    Keys are listed through each vault's
    management endpoint.

    Collects:
        - Resource information
        - Creation date
        - OCI Defined Tags
        - Existing Key details
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

        # -----------------------------------------------------
        # Vault client
        # -----------------------------------------------------

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
                        f"Skipping keys."
                    )

                    continue

                try:

                    # -------------------------------------------------
                    # Create KMS Management client using the
                    # vault-specific management endpoint.
                    # -------------------------------------------------

                    kms_client = (
                        oci.key_management.KmsManagementClient(
                            region_config,
                            service_endpoint=management_endpoint,
                        )
                    )

                    keys = (
                        oci.pagination.list_call_get_all_results(
                            kms_client.list_keys,
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

                                # -------------------------------------
                                # Creation Date
                                # -------------------------------------

                                time_created=getattr(
                                    key,
                                    "time_created",
                                    None,
                                ),

                                # -------------------------------------
                                # OCI Defined Tags
                                # -------------------------------------

                                defined_tags=getattr(
                                    key,
                                    "defined_tags",
                                    None,
                                ),

                                # -------------------------------------
                                # Existing Key details
                                # -------------------------------------

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
                        f"    ERROR collecting keys "
                        f"from vault "
                        f"{vault_name}: {error}"
                    )

    return resources
