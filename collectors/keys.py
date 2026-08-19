import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_keys(config):
    """
    Collect all OCI KMS keys across all subscribed regions
    and accessible compartments.
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(f"  Processing Keys region: {region}")

        region_config = config.copy()
        region_config["region"] = region

        kms_management_client = oci.key_management.KmsManagementClient(
            region_config
        )

        for compartment in compartments:

            vaults = oci.pagination.list_call_get_all_results(
                kms_management_client.list_vaults,
                compartment_id=compartment["id"],
            )

            for vault in vaults.data:

                keys = oci.pagination.list_call_get_all_results(
                    kms_management_client.list_keys,
                    compartment_id=compartment["id"],
                    vault_id=vault.id,
                )

                for key in keys.data:

                    resources.append(
                        Resource(
                            service="Key Management",
                            resource_type="Key",
                            name=key.display_name,
                            ocid=key.id,
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=key.lifecycle_state,
                            details={
                                "vault_id": vault.id,
                                "vault_name": vault.display_name,
                                "key_shape": getattr(
                                    key,
                                    "key_shape",
                                    None,
                                ),
                                "protection_mode": getattr(
                                    key,
                                    "protection_mode",
                                    "",
                                ),
                                "time_created": getattr(
                                    key,
                                    "time_created",
                                    "",
                                ),
                            },
                        )
                    )

    return resources
