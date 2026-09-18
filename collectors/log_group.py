import oci

from utils.compartments import get_compartments
from utils.regions import get_regions


def _get(obj, name, default=None):
    """
    Safely get a value from an OCI SDK object or dictionary.
    """
    if obj is None:
        return default

    try:
        if isinstance(obj, dict):
            return obj.get(name, default)

        return getattr(obj, name, default)

    except Exception:
        return default


def _safe_value(value):
    """
    Convert OCI SDK objects / nested values into safe Python values.
    """

    if value is None:
        return ""

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ):
        return value

    if isinstance(value, dict):
        return {
            str(key): _safe_value(val)
            for key, val in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            _safe_value(item)
            for item in value
        ]

    try:
        if hasattr(value, "to_dict"):
            return _safe_value(
                value.to_dict()
            )
    except Exception:
        pass

    return str(value)


def collect_log_groups(config):
    """
    Collect OCI Logging Log Groups.

    Scope:
        - All subscribed regions
        - All accessible compartments

    Details collected:
        - Log Group OCID
        - Display Name
        - Description
        - Region
        - Compartment
        - Lifecycle State
        - Creation Date
        - Last Modified Date
        - Defined Tags
        - Freeform Tags
        - System Tags

    Note:
        Logs themselves are not collected here because the existing
        Logging collector already handles the Log resource type.
    """

    resources = []

    # ============================================================
    # REGION / COMPARTMENT DISCOVERY
    # ============================================================

    regions = get_regions(config)
    compartments = get_compartments(config)

    if not regions:
        print(
            "  ERROR: No regions found for Log Groups."
        )
        return resources

    if not compartments:
        print(
            "  ERROR: No compartments found for Log Groups."
        )
        return resources

    # ============================================================
    # REGIONS
    # ============================================================

    for region in regions:

        print(
            f"  Processing Log Groups region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        # ========================================================
        # LOGGING MANAGEMENT CLIENT
        # ========================================================

        try:

            logging_client = (
                oci.logging.LoggingManagementClient(
                    region_config
                )
            )

        except Exception as error:

            print(
                f"  ERROR initializing Logging client "
                f"for region {region}: {error}"
            )

            continue

        # ========================================================
        # COMPARTMENTS
        # ========================================================

        for compartment in compartments:

            compartment_id = _get(
                compartment,
                "id",
                compartment
                if isinstance(compartment, str)
                else None,
            )

            compartment_name = _get(
                compartment,
                "name",
                compartment_id,
            )

            if not compartment_id:
                continue

            print(
                f"    Processing Log Groups compartment: "
                f"{compartment_name}"
            )

            # ====================================================
            # LIST LOG GROUPS
            # ====================================================

            try:

                response = (
                    oci.pagination.list_call_get_all_results(
                        logging_client.list_log_groups,
                        compartment_id=compartment_id,
                    )
                )

                log_groups = response.data

            except Exception as error:

                print(
                    f"      ERROR collecting Log Groups "
                    f"from compartment {compartment_name}: "
                    f"{error}"
                )

                continue

            if not log_groups:
                continue

            print(
                f"      Found {len(log_groups)} "
                f"Log Group(s)"
            )

            # ====================================================
            # PROCESS LOG GROUPS
            # ====================================================

            for log_group in log_groups:

                try:

                    log_group_id = _get(
                        log_group,
                        "id",
                        "",
                    )

                    display_name = _get(
                        log_group,
                        "display_name",
                        "",
                    )

                    description = _get(
                        log_group,
                        "description",
                        "",
                    )

                    lifecycle_state = _get(
                        log_group,
                        "lifecycle_state",
                        "",
                    )

                    time_created = _get(
                        log_group,
                        "time_created",
                        None,
                    )

                    time_last_modified = _get(
                        log_group,
                        "time_last_modified",
                        None,
                    )

                    compartment_id_value = _get(
                        log_group,
                        "compartment_id",
                        compartment_id,
                    )

                    # =================================================
                    # GET FULL LOG GROUP DETAILS
                    # =================================================

                    log_group_details = log_group

                    if log_group_id:

                        try:

                            detail_response = (
                                logging_client.get_log_group(
                                    log_group_id
                                )
                            )

                            log_group_details = (
                                detail_response.data
                            )

                        except Exception as detail_error:

                            print(
                                f"        WARNING: Could not get "
                                f"details for Log Group "
                                f"{display_name}: "
                                f"{detail_error}"
                            )

                    # =================================================
                    # REFRESH DETAILS
                    # =================================================

                    display_name = _get(
                        log_group_details,
                        "display_name",
                        display_name,
                    )

                    description = _get(
                        log_group_details,
                        "description",
                        description,
                    )

                    lifecycle_state = _get(
                        log_group_details,
                        "lifecycle_state",
                        lifecycle_state,
                    )

                    time_created = _get(
                        log_group_details,
                        "time_created",
                        time_created,
                    )

                    time_last_modified = _get(
                        log_group_details,
                        "time_last_modified",
                        time_last_modified,
                    )

                    compartment_id_value = _get(
                        log_group_details,
                        "compartment_id",
                        compartment_id_value,
                    )

                    # =================================================
                    # TAGS
                    # =================================================

                    defined_tags = _get(
                        log_group_details,
                        "defined_tags",
                        {},
                    ) or {}

                    freeform_tags = _get(
                        log_group_details,
                        "freeform_tags",
                        {},
                    ) or {}

                    system_tags = _get(
                        log_group_details,
                        "system_tags",
                        {},
                    ) or {}

                    # =================================================
                    # RESOURCE
                    # =================================================

                    resource = {

                        "service":
                            "Logging",

                        "resource_type":
                            "Log Group",

                        "id":
                            log_group_id,

                        "ocid":
                            log_group_id,

                        "name":
                            display_name,

                        "display_name":
                            display_name,

                        # -----------------------------------------
                        # LOCATION
                        # -----------------------------------------

                        "region":
                            region,

                        "compartment_id":
                            compartment_id_value,

                        "compartment_name":
                            compartment_name,

                        # -----------------------------------------
                        # DETAILS
                        # -----------------------------------------

                        "description":
                            description,

                        # -----------------------------------------
                        # STATE
                        # -----------------------------------------

                        "lifecycle_state":
                            lifecycle_state,

                        "state":
                            lifecycle_state,

                        # -----------------------------------------
                        # TIME
                        # -----------------------------------------

                        "time_created":
                            time_created,

                        "time_last_modified":
                            time_last_modified,

                        # -----------------------------------------
                        # TAGS
                        # -----------------------------------------

                        "defined_tags":
                            _safe_value(
                                defined_tags
                            ),

                        "freeform_tags":
                            _safe_value(
                                freeform_tags
                            ),

                        "system_tags":
                            _safe_value(
                                system_tags
                            ),
                    }

                    resources.append(
                        resource
                    )

                except Exception as error:

                    print(
                        f"      ERROR processing Log Group "
                        f"{_get(log_group, 'display_name', '')}: "
                        f"{error}"
                    )

    # ============================================================
    # SUMMARY
    # ============================================================

    print(
        f"Log Groups: {len(resources)} resources found"
    )

    return resources
