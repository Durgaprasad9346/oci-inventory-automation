import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_data_safe_user_assessments(config):
    """
    Collect OCI Data Safe User Assessments across:
        - All subscribed regions
        - All accessible compartments

    Collects:
        - User Assessment information
        - Creation date
        - OCI Defined Tags
        - Assessment details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing Data Safe User Assessments region: {region}"
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
                        data_safe_client.list_user_assessments,
                        compartment_id=compartment["id"],
                    )
                )

                for assessment in assessments.data:

                    resources.append(
                        Resource(
                            service="Data Safe",
                            resource_type="User Assessment",
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

                            time_created=getattr(
                                assessment,
                                "time_created",
                                None,
                            ),

                            defined_tags=getattr(
                                assessment,
                                "defined_tags",
                                None,
                            ),

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
                            },
                        )
                    )

            except Exception as error:

                print(
                    f"    ERROR collecting Data Safe "
                    f"User Assessments from compartment "
                    f"{compartment['name']}: {error}"
                )

    return resources
