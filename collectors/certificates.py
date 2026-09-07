import oci

from oci.certificates_management import CertificatesManagementClient

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_certificates(config):
    """
    Collect OCI Certificates across all configured regions
    and accessible compartments.
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing Certificates region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        # -------------------------------------------------------------
        # CORRECT CLIENT
        # -------------------------------------------------------------

        certificates_client = CertificatesManagementClient(
            region_config
        )

        for compartment in compartments:

            compartment_id = compartment["id"]
            compartment_name = compartment["name"]

            try:

                certificates = (
                    oci.pagination.list_call_get_all_results(
                        certificates_client.list_certificates,
                        compartment_id=compartment_id,
                    )
                )

            except Exception as error:

                print(
                    f"    ERROR collecting Certificates from compartment "
                    f"{compartment_name}: {error}"
                )

                continue

            for certificate in certificates.data:

                resources.append(
                    Resource(
                        service="Certificates",
                        resource_type="Certificate",
                        name=getattr(
                            certificate,
                            "name",
                            "",
                        ),
                        ocid=getattr(
                            certificate,
                            "id",
                            "",
                        ),
                        compartment_id=compartment_id,
                        compartment_name=compartment_name,
                        region=region,
                        state=getattr(
                            certificate,
                            "lifecycle_state",
                            "",
                        ),
                        time_created=getattr(
                            certificate,
                            "time_created",
                            None,
                        ),
                        defined_tags=getattr(
                            certificate,
                            "defined_tags",
                            None,
                        ),
                        freeform_tags=getattr(
                            certificate,
                            "freeform_tags",
                            None,
                        ),
                        details={
                            "certificate_authority_id": getattr(
                                certificate,
                                "certificate_authority_id",
                                "",
                            ),
                            "certificate_type": getattr(
                                certificate,
                                "certificate_type",
                                "",
                            ),
                            "issuer_certificate_authority_id": getattr(
                                certificate,
                                "issuer_certificate_authority_id",
                                "",
                            ),
                            "key_algorithm": getattr(
                                certificate,
                                "key_algorithm",
                                "",
                            ),
                            "signature_algorithm": getattr(
                                certificate,
                                "signature_algorithm",
                                "",
                            ),
                            "validity": getattr(
                                certificate,
                                "validity",
                                "",
                            ),
                            "time_of_deletion": getattr(
                                certificate,
                                "time_of_deletion",
                                None,
                            ),
                            "description": getattr(
                                certificate,
                                "description",
                                "",
                            ),
                        },
                    )
                )

    return resources
