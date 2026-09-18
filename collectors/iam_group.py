import oci

from utils.compartments import get_compartments


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


def collect_iam_groups(config):
    """
    Collect OCI IAM Groups.

    IAM Groups are tenancy-level resources.

    Details collected:

        Group
        -----
        - Group OCID
        - Group Name
        - Description
        - Lifecycle State
        - Creation Date
        - Members
        - Member Count
        - Defined Tags
        - Freeform Tags
    """

    resources = []

    # ============================================================
    # TENANCY
    # ============================================================

    tenancy_id = (
        config.get("tenancy")
        or config.get("tenancy_id")
        or config.get("tenancy_ocid")
    )

    if not tenancy_id:

        print(
            "  ERROR: Tenancy OCID is missing from OCI config."
        )

        return resources

    print(
        "  Processing IAM Groups at tenancy level"
    )

    # ============================================================
    # IDENTITY CLIENT
    # ============================================================

    try:

        identity_client = oci.identity.IdentityClient(
            config
        )

    except Exception as error:

        print(
            f"  ERROR initializing Identity client: "
            f"{error}"
        )

        return resources

    # ============================================================
    # LIST GROUPS
    # ============================================================

    try:

        response = (
            oci.pagination.list_call_get_all_results(
                identity_client.list_groups,
                compartment_id=tenancy_id,
            )
        )

        groups = response.data

    except Exception as error:

        print(
            f"  ERROR collecting IAM Groups: "
            f"{error}"
        )

        return resources

    if not groups:

        print(
            "  No IAM Groups found."
        )

        return resources

    print(
        f"  Found {len(groups)} IAM Group(s)"
    )

    # ============================================================
    # PROCESS GROUPS
    # ============================================================

    for group in groups:

        try:

            group_id = _get(
                group,
                "id",
                "",
            )

            group_name = _get(
                group,
                "name",
                "",
            )

            description = _get(
                group,
                "description",
                "",
            )

            lifecycle_state = _get(
                group,
                "lifecycle_state",
                "",
            )

            time_created = _get(
                group,
                "time_created",
                None,
            )

            compartment_id = _get(
                group,
                "compartment_id",
                tenancy_id,
            )

            # ====================================================
            # GET GROUP DETAILS
            # ====================================================

            group_details = group

            if group_id:

                try:

                    detail_response = (
                        identity_client.get_group(
                            group_id
                        )
                    )

                    group_details = (
                        detail_response.data
                    )

                except Exception as detail_error:

                    print(
                        f"    WARNING: Could not get details "
                        f"for IAM Group {group_name}: "
                        f"{detail_error}"
                    )

            # ====================================================
            # REFRESH DETAILS
            # ====================================================

            group_name = _get(
                group_details,
                "name",
                group_name,
            )

            description = _get(
                group_details,
                "description",
                description,
            )

            lifecycle_state = _get(
                group_details,
                "lifecycle_state",
                lifecycle_state,
            )

            time_created = _get(
                group_details,
                "time_created",
                time_created,
            )

            compartment_id = _get(
                group_details,
                "compartment_id",
                compartment_id,
            )

            # ====================================================
            # GROUP MEMBERS
            #
            # IAM Group membership is obtained through
            # list_user_group_memberships().
            # ====================================================

            members = []

            if group_id:

                try:

                    membership_response = (
                        oci.pagination.list_call_get_all_results(
                            identity_client.list_user_group_memberships,
                            compartment_id=tenancy_id,
                            group_id=group_id,
                        )
                    )

                    for membership in membership_response.data:

                        user_id = _get(
                            membership,
                            "user_id",
                            "",
                        )

                        membership_id = _get(
                            membership,
                            "id",
                            "",
                        )

                        time_created_membership = _get(
                            membership,
                            "time_created",
                            None,
                        )

                        members.append(
                            {
                                "membership_id":
                                    membership_id,

                                "user_id":
                                    user_id,

                                "time_created":
                                    time_created_membership,
                            }
                        )

                except Exception as membership_error:

                    print(
                        f"    WARNING: Could not collect "
                        f"members for IAM Group "
                        f"{group_name}: "
                        f"{membership_error}"
                    )

            # ====================================================
            # TAGS
            # ====================================================

            defined_tags = _get(
                group_details,
                "defined_tags",
                {},
            ) or {}

            freeform_tags = _get(
                group_details,
                "freeform_tags",
                {},
            ) or {}

            # ====================================================
            # RESOURCE
            # ====================================================

            resource = {

                "service":
                    "IAM",

                "resource_type":
                    "Group",

                "id":
                    group_id,

                "ocid":
                    group_id,

                "name":
                    group_name,

                "display_name":
                    group_name,

                # ---------------------------------------------
                # SCOPE
                # ---------------------------------------------

                "region":
                    "",

                "compartment_id":
                    compartment_id,

                "compartment_name":
                    "root",

                # ---------------------------------------------
                # GROUP DETAILS
                # ---------------------------------------------

                "description":
                    description,

                # ---------------------------------------------
                # STATE
                # ---------------------------------------------

                "lifecycle_state":
                    lifecycle_state,

                "state":
                    lifecycle_state,

                # ---------------------------------------------
                # MEMBERS
                # ---------------------------------------------

                "members":
                    _safe_value(
                        members
                    ),

                "member_count":
                    len(members),

                # ---------------------------------------------
                # TIME
                # ---------------------------------------------

                "time_created":
                    time_created,

                # ---------------------------------------------
                # TAGS
                # ---------------------------------------------

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
                f"  ERROR processing IAM Group "
                f"{_get(group, 'name', '')}: "
                f"{error}"
            )

    # ============================================================
    # SUMMARY
    # ============================================================

    print(
        f"IAM Groups: {len(resources)} resources found"
    )

    return resources
