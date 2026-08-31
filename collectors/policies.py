import oci

from collectors.base import Resource
from utils.compartments import get_compartments


def collect_policies(config):
    """
    Collect all OCI IAM Policies.

    Policies are tenancy-level IAM resources, so they are
    collected using the Identity client in the home region.

    Collects:
        - Policy name
        - OCID
        - Compartment
        - Creation date
        - Lifecycle state
        - Description
        - Policy statements
        - OCI Defined Tags
    """

    compartments = get_compartments(config)

    resources = []

    # ---------------------------------------------------------
    # IAM is a home-region service.
    #
    # Use the configured/home region instead of iterating
    # through every subscribed region, otherwise the same
    # policy can be returned repeatedly.
    # ---------------------------------------------------------

    home_region = config.get("region")

    if not home_region:

        print(
            "    ERROR: OCI home region is not available "
            "in configuration."
        )

        return resources

    print(
        f"  Processing Policies region: {home_region}"
    )

    region_config = config.copy()
    region_config["region"] = home_region

    identity_client = oci.identity.IdentityClient(
        region_config
    )

    # ---------------------------------------------------------
    # Policies are normally located in root tenancy or
    # compartments. Iterate through the compartments returned
    # by the existing compartment utility.
    # ---------------------------------------------------------

    for compartment in compartments:

        try:

            policies = (
                oci.pagination.list_call_get_all_results(
                    identity_client.list_policies,
                    compartment_id=compartment["id"],
                )
            )

            for policy in policies.data:

                resources.append(
                    Resource(
                        service="IAM",
                        resource_type="Policy",
                        name=getattr(
                            policy,
                            "name",
                            "",
                        ),
                        ocid=getattr(
                            policy,
                            "id",
                            "",
                        ),
                        compartment_id=compartment["id"],
                        compartment_name=compartment["name"],
                        region=home_region,
                        state=getattr(
                            policy,
                            "lifecycle_state",
                            "",
                        ),

                        # -----------------------------------------
                        # Creation Date
                        # -----------------------------------------

                        time_created=getattr(
                            policy,
                            "time_created",
                            None,
                        ),

                        # -----------------------------------------
                        # OCI Defined Tags
                        # -----------------------------------------

                        defined_tags=getattr(
                            policy,
                            "defined_tags",
                            None,
                        ),

                        # -----------------------------------------
                        # Policy details
                        # -----------------------------------------

                        details={
                            "description": getattr(
                                policy,
                                "description",
                                "",
                            ),
                            "statements": getattr(
                                policy,
                                "statements",
                                "",
                            ),
                            "version_date": getattr(
                                policy,
                                "version_date",
                                "",
                            ),
                            "last_updated_date": getattr(
                                policy,
                                "last_updated_date",
                                "",
                            ),
                            "policy_type": getattr(
                                policy,
                                "policy_type",
                                "",
                            ),
                        },
                    )
                )

        except Exception as error:

            print(
                f"    ERROR collecting Policies from "
                f"compartment "
                f"{compartment['name']}: {error}"
            )

    return resources
