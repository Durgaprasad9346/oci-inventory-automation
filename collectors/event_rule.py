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

    if isinstance(value, (str, int, float, bool)):
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
            return _safe_value(value.to_dict())
    except Exception:
        pass

    return str(value)


def collect_event_rules(config):
    """
    Collect OCI Events Rules.

    Scope:
        - All subscribed regions
        - All accessible compartments

    Details collected:
        - Rule OCID
        - Display Name
        - Description
        - Region
        - Compartment
        - Enabled State
        - Lifecycle State
        - Lifecycle Message
        - Condition
        - Actions
        - Creation Date
        - Defined Tags
        - Freeform Tags
    """

    resources = []

    # ============================================================
    # REGION / COMPARTMENT DISCOVERY
    # ============================================================

    regions = get_regions(config)
    compartments = get_compartments(config)

    if not regions:
        print(
            "  ERROR: No regions found for Event Rules."
        )
        return resources

    if not compartments:
        print(
            "  ERROR: No compartments found for Event Rules."
        )
        return resources

    # ============================================================
    # REGIONS
    # ============================================================

    for region in regions:

        print(
            f"  Processing Event Rules region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        # ========================================================
        # EVENTS CLIENT
        # ========================================================

        try:

            events_client = (
                oci.events.EventsClient(
                    region_config
                )
            )

        except Exception as error:

            print(
                f"  ERROR initializing Events client "
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
                f"    Processing Event Rules compartment: "
                f"{compartment_name}"
            )

            # ====================================================
            # LIST RULES
            # ====================================================

            try:

                response = (
                    oci.pagination.list_call_get_all_results(
                        events_client.list_rules,
                        compartment_id=compartment_id,
                    )
                )

                rules = response.data

            except Exception as error:

                print(
                    f"      ERROR collecting Event Rules "
                    f"from compartment {compartment_name}: "
                    f"{error}"
                )

                continue

            if not rules:
                continue

            print(
                f"      Found {len(rules)} Event Rule(s)"
            )

            # ====================================================
            # PROCESS RULES
            # ====================================================

            for rule in rules:

                try:

                    rule_id = _get(
                        rule,
                        "id",
                        "",
                    )

                    display_name = _get(
                        rule,
                        "display_name",
                        "",
                    )

                    description = _get(
                        rule,
                        "description",
                        "",
                    )

                    is_enabled = _get(
                        rule,
                        "is_enabled",
                        None,
                    )

                    lifecycle_state = _get(
                        rule,
                        "lifecycle_state",
                        "",
                    )

                    lifecycle_message = _get(
                        rule,
                        "lifecycle_message",
                        "",
                    )

                    time_created = _get(
                        rule,
                        "time_created",
                        None,
                    )

                    condition = _get(
                        rule,
                        "condition",
                        None,
                    )

                    actions = _get(
                        rule,
                        "actions",
                        None,
                    )

                    compartment_id_value = _get(
                        rule,
                        "compartment_id",
                        compartment_id,
                    )

                    # =================================================
                    # GET FULL RULE DETAILS
                    # =================================================

                    rule_details = rule

                    if rule_id:

                        try:

                            detail_response = (
                                events_client.get_rule(
                                    rule_id
                                )
                            )

                            rule_details = (
                                detail_response.data
                            )

                        except Exception as detail_error:

                            print(
                                f"        WARNING: Could not get "
                                f"details for Event Rule "
                                f"{display_name}: "
                                f"{detail_error}"
                            )

                    # =================================================
                    # REFRESH DETAILS
                    # =================================================

                    display_name = _get(
                        rule_details,
                        "display_name",
                        display_name,
                    )

                    description = _get(
                        rule_details,
                        "description",
                        description,
                    )

                    is_enabled = _get(
                        rule_details,
                        "is_enabled",
                        is_enabled,
                    )

                    lifecycle_state = _get(
                        rule_details,
                        "lifecycle_state",
                        lifecycle_state,
                    )

                    lifecycle_message = _get(
                        rule_details,
                        "lifecycle_message",
                        lifecycle_message,
                    )

                    time_created = _get(
                        rule_details,
                        "time_created",
                        time_created,
                    )

                    condition = _get(
                        rule_details,
                        "condition",
                        condition,
                    )

                    actions = _get(
                        rule_details,
                        "actions",
                        actions,
                    )

                    compartment_id_value = _get(
                        rule_details,
                        "compartment_id",
                        compartment_id_value,
                    )

                    # =================================================
                    # TAGS
                    # =================================================

                    defined_tags = _get(
                        rule_details,
                        "defined_tags",
                        {},
                    ) or {}

                    freeform_tags = _get(
                        rule_details,
                        "freeform_tags",
                        {},
                    ) or {}

                    # =================================================
                    # RESOURCE
                    # =================================================

                    resource = {

                        "service":
                            "Events",

                        "resource_type":
                            "Event Rule",

                        "id":
                            rule_id,

                        "ocid":
                            rule_id,

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

                        "is_enabled":
                            is_enabled,

                        "enabled":
                            is_enabled,

                        # -----------------------------------------
                        # STATE
                        # -----------------------------------------

                        "lifecycle_state":
                            lifecycle_state,

                        "state":
                            lifecycle_state,

                        "lifecycle_message":
                            lifecycle_message,

                        # -----------------------------------------
                        # EVENT CONDITION
                        # -----------------------------------------

                        "condition":
                            _safe_value(
                                condition
                            ),

                        # -----------------------------------------
                        # ACTIONS
                        # -----------------------------------------

                        "actions":
                            _safe_value(
                                actions
                            ),

                        "action_count":
                            len(actions)
                            if isinstance(actions, (list, tuple))
                            else "",

                        # -----------------------------------------
                        # TIME
                        # -----------------------------------------

                        "time_created":
                            time_created,

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
                    }

                    resources.append(
                        resource
                    )

                except Exception as error:

                    print(
                        f"      ERROR processing Event Rule "
                        f"{_get(rule, 'display_name', '')}: "
                        f"{error}"
                    )

    # ============================================================
    # SUMMARY
    # ============================================================

    print(
        f"Event Rules: {len(resources)} resources found"
    )

    return resources
