import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_logging(config):
    """
    Collect OCI Logging resources across:
        - All subscribed regions
        - All accessible compartments
        - All log groups
        - All logs

    Collects:
        - Log Group information
        - Log information
        - Creation date
        - OCI Defined Tags
        - Resource-specific details
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing Logging region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        logging_client = oci.logging.LoggingManagementClient(
            region_config
        )

        for compartment in compartments:

            # =========================================================
            # LOG GROUPS
            # =========================================================

            try:

                log_groups = (
                    oci.pagination.list_call_get_all_results(
                        logging_client.list_log_groups,
                        compartment_id=compartment["id"],
                    )
                )

            except Exception as error:

                print(
                    f"    ERROR collecting Log Groups from "
                    f"compartment {compartment['name']}: {error}"
                )

                continue

            for log_group in log_groups.data:

                log_group_id = getattr(
                    log_group,
                    "id",
                    "",
                )

                log_group_name = getattr(
                    log_group,
                    "display_name",
                    "",
                )

                # -----------------------------------------------------
                # Add Log Group itself
                # -----------------------------------------------------

                resources.append(
                    Resource(
                        service="Logging",
                        resource_type="Log Group",
                        name=log_group_name,
                        ocid=log_group_id,
                        compartment_id=compartment["id"],
                        compartment_name=compartment["name"],
                        region=region,
                        state=getattr(
                            log_group,
                            "lifecycle_state",
                            "",
                        ),

                        # Creation Date
                        time_created=getattr(
                            log_group,
                            "time_created",
                            None,
                        ),

                        # Defined Tags
                        defined_tags=getattr(
                            log_group,
                            "defined_tags",
                            None,
                        ),

                        details={
                            "description": getattr(
                                log_group,
                                "description",
                                "",
                            ),
                            "log_group_id": log_group_id,
                        },
                    )
                )

                if not log_group_id:
                    continue

                # =====================================================
                # LOGS INSIDE LOG GROUP
                # =====================================================

                try:

                    logs = (
                        oci.pagination.list_call_get_all_results(
                            logging_client.list_logs,
                            log_group_id=log_group_id,
                        )
                    )

                except Exception as error:

                    print(
                        f"    ERROR collecting Logs from "
                        f"Log Group {log_group_name}: {error}"
                    )

                    continue

                for log in logs.data:

                    resources.append(
                        Resource(
                            service="Logging",
                            resource_type="Log",
                            name=getattr(
                                log,
                                "display_name",
                                "",
                            ),
                            ocid=getattr(
                                log,
                                "id",
                                "",
                            ),
                            compartment_id=compartment["id"],
                            compartment_name=compartment["name"],
                            region=region,
                            state=getattr(
                                log,
                                "lifecycle_state",
                                "",
                            ),

                            # Creation Date
                            time_created=getattr(
                                log,
                                "time_created",
                                None,
                            ),

                            # Defined Tags
                            defined_tags=getattr(
                                log,
                                "defined_tags",
                                None,
                            ),

                            details={
                                "log_group_id": log_group_id,
                                "log_group_name": log_group_name,
                                "log_type": getattr(
                                    log,
                                    "log_type",
                                    "",
                                ),
                                "source": getattr(
                                    log,
                                    "source",
                                    "",
                                ),
                                "is_enabled": getattr(
                                    log,
                                    "is_enabled",
                                    "",
                                ),
                                "retention_duration": getattr(
                                    log,
                                    "retention_duration",
                                    "",
                                ),
                                "service": getattr(
                                    log,
                                    "service",
                                    "",
                                ),
                            },
                        )
                    )

    return resources
