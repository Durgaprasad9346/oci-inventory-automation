import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_data_safe_security_assessments(config):
    """
    Collect OCI Data Safe Security Assessments across:
        - All subscribed regions
        - All accessible compartments

    Collects:
        - Security Assessment information
        - Creation date
        - OCI Defined Tags
        - Resource-specific details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing Data Safe Security Assessments region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        data_safe_client = oci.data_safe.DataSafeClient(
            region_config
        )

        for compartment in compartments:

            try:

                assessments = (
                    oci.pagination.list_call_get_all_results(
                        data_safe_client.list_security_assessments,
                        compartment_id=compartment["id"],
                    )
                )

                for assessment in assessments.data:

                    resources.append(
                        Resource(
                            service="Data Safe",
                            resource_type="Security Assessment",
                            name=getattr(
                                assessment,
                                "display_name",
                                getattr(
                                    assessment,
                                    "name",
                                    "",
                                ),
                            ),
                            ocid=getattr(
                                assessment,
                                "id",
                                "",
                            ),
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=getattr(
                                assessment,
                                "lifecycle_state",
                                "",
                            ),

                            # -----------------------------------------
                            # Creation Date
                            # -----------------------------------------

                            time_created=getattr(
                                assessment,
                                "time_created",
                                None,
                            ),

                            # -----------------------------------------
                            # OCI Defined Tags
                            # -----------------------------------------

                            defined_tags=getattr(
                                assessment,
                                "defined_tags",
                                None,
                            ),

                            # -----------------------------------------
                            # Resource-specific details
                            # -----------------------------------------

                            details={
                                "target_id": getattr(
                                    assessment,
                                    "target_id",
                                    "",
                                ),
                                "target_name": getattr(
                                    assessment,
                                    "target_name",
                                    "",
                                ),
                                "database_id": getattr(
                                    assessment,
                                    "database_id",
                                    "",
                                ),
                                "assessment_type": getattr(
                                    assessment,
                                    "assessment_type",
                                    "",
                                ),
                                "assessment_time": getattr(
                                    assessment,
                                    "assessment_time",
                                    "",
                                ),
                                "schedule_type": getattr(
                                    assessment,
                                    "schedule_type",
                                    "",
                                ),
                                "status": getattr(
                                    assessment,
                                    "status",
                                    "",
                                ),
                                "description": getattr(
                                    assessment,
                                    "description",
                                    "",
                                ),
                                "lifecycle_details": getattr(
                                    assessment,
                                    "lifecycle_details",
                                    "",
                                ),
                            },
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR collecting Data Safe "
                    f"Security Assessments from compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
