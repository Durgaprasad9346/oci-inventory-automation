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


def collect_iam_users(config):
    """
    Collect OCI IAM Users.

    IAM Users are tenancy-level resources.

    Details collected:
        - User OCID
        - User Name
        - Description
        - Email
        - Email Verified
        - Identity Provider OCID
        - External Identifier
        - Lifecycle State
        - Inactive Status
        - MFA Activated
        - Last Successful Login
        - Previous Successful Login
        - DB User Name
        - Capabilities
        - Creation Date
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
        "  Processing IAM Users at tenancy level"
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
    # LIST USERS
    #
    # OCI requires the tenancy OCID here because users are
    # tenancy-level resources.
    # ============================================================

    try:

        response = (
            oci.pagination.list_call_get_all_results(
                identity_client.list_users,
                compartment_id=tenancy_id,
            )
        )

        users = response.data

    except Exception as error:

        print(
            f"  ERROR collecting IAM Users: {error}"
        )

        return resources

    if not users:

        print(
            "  No IAM Users found."
        )

        return resources

    print(
        f"  Found {len(users)} IAM User(s)"
    )

    # ============================================================
    # PROCESS USERS
    # ============================================================

    for user in users:

        try:

            user_id = _get(
                user,
                "id",
                "",
            )

            name = _get(
                user,
                "name",
                "",
            )

            description = _get(
                user,
                "description",
                "",
            )

            email = _get(
                user,
                "email",
                "",
            )

            email_verified = _get(
                user,
                "email_verified",
                None,
            )

            identity_provider_id = _get(
                user,
                "identity_provider_id",
                "",
            )

            external_identifier = _get(
                user,
                "external_identifier",
                "",
            )

            lifecycle_state = _get(
                user,
                "lifecycle_state",
                "",
            )

            inactive_status = _get(
                user,
                "inactive_status",
                None,
            )

            is_mfa_activated = _get(
                user,
                "is_mfa_activated",
                None,
            )

            last_successful_login_time = _get(
                user,
                "last_successful_login_time",
                None,
            )

            previous_successful_login_time = _get(
                user,
                "previous_successful_login_time",
                None,
            )

            db_user_name = _get(
                user,
                "db_user_name",
                "",
            )

            capabilities = _get(
                user,
                "capabilities",
                None,
            )

            time_created = _get(
                user,
                "time_created",
                None,
            )

            compartment_id = _get(
                user,
                "compartment_id",
                tenancy_id,
            )

            # ====================================================
            # TAGS
            # ====================================================

            defined_tags = _get(
                user,
                "defined_tags",
                {},
            ) or {}

            freeform_tags = _get(
                user,
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
                    "User",

                "id":
                    user_id,

                "ocid":
                    user_id,

                "name":
                    name,

                "display_name":
                    name,

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
                # USER DETAILS
                # ---------------------------------------------

                "description":
                    description,

                "email":
                    email,

                "email_verified":
                    email_verified,

                "identity_provider_id":
                    identity_provider_id,

                "external_identifier":
                    external_identifier,

                "db_user_name":
                    db_user_name,

                # ---------------------------------------------
                # STATE
                # ---------------------------------------------

                "lifecycle_state":
                    lifecycle_state,

                "state":
                    lifecycle_state,

                "inactive_status":
                    inactive_status,

                # ---------------------------------------------
                # SECURITY
                # ---------------------------------------------

                "is_mfa_activated":
                    is_mfa_activated,

                # ---------------------------------------------
                # LOGIN
                # ---------------------------------------------

                "last_successful_login_time":
                    last_successful_login_time,

                "previous_successful_login_time":
                    previous_successful_login_time,

                # ---------------------------------------------
                # CAPABILITIES
                # ---------------------------------------------

                "capabilities":
                    _safe_value(
                        capabilities
                    ),

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
                f"  ERROR processing IAM User "
                f"{_get(user, 'name', '')}: "
                f"{error}"
            )

    # ============================================================
    # SUMMARY
    # ============================================================

    print(
        f"IAM Users: {len(resources)} resources found"
    )

    return resources
