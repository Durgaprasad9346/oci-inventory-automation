import oci

from oci.certificates_management import CertificatesManagementClient

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_certificate_authorities(config):
    """
    Collect OCI Certificate Authorities across all configured
    regions and accessible compartments.
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing Certificate Authorities region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        # -------------------------------------------------------------
        # CORRECT CERTIFICATES MANAGEMENT CLIENT
        # -------------------------------------------------------------

        certificate_client = CertificatesManagementClient(
            region_config
        )

        for compartment in compartments:

            compartment_id = compartment["id"]
            compartment_name = compartment["name"]

            try:

                certificate_authorities = (
                    oci.pagination.list_call_get_all_results(
                        certificate_client.list_certificate_authorities,
                        compartment_id=compartment_id,
                    )
                )

            except Exception as error:

                print(
                    f"    ERROR collecting Certificate Authorities "
                    f"from compartment {compartment_name}: {error}"
                )

                continue

            for certificate_authority in certificate_authorities.data:

                resources.append(
                    Resource(
                        service="Certificates",
                        resource_type="Certificate Authority",
                        name=getattr(
                            certificate_authority,
                            "name",
                            "",
                        ),
                        ocid=getattr(
                            certificate_authority,
                            "id",
                            "",
                        ),
                        compartment_id=compartment_id,
                        compartment_name=compartment_name,
                        region=region,
                        state=getattr(
                            certificate_authority,
                            "lifecycle_state",
                            "",
                        ),
                        time_created=getattr(
                            certificate_authority,
                            "time_created",
                            None,
                        ),
                        defined_tags=getattr(
                            certificate_authority,
                            "defined_tags",
                            None,
                        ),
                        freeform_tags=getattr(
                            certificate_authority,
                            "freeform_tags",
                            None,
                        ),
                        details={
                            "certificate_authority_type": getattr(
                                certificate_authority,
                                "certificate_authority_type",
                                "",
                            ),
                            "certificate_type": getattr(
                                certificate_authority,
                                "certificate_type",
                                "",
                            ),
                            "issuer_certificate_authority_id": getattr(
                                certificate_authority,
                                "issuer_certificate_authority_id",
                                "",
                            ),
                            "key_algorithm": getattr(
                                certificate_authority,
                                "key_algorithm",
                                "",
                            ),
                            "signature_algorithm": getattr(
                                certificate_authority,
                                "signature_algorithm",
                                "",
                            ),
                            "validity": getattr(
                                certificate_authority,
                                "validity",
                                "",
                            ),
                            "time_of_deletion": getattr(
                                certificate_authority,
                                "time_of_deletion",
                                None,
                            ),
                            "description": getattr(
                                certificate_authority,
                                "description",
                                "",
                            ),
                        },
                    )
                )

    return resources
