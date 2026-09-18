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
    Convert OCI SDK nested objects into safe Python values.
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


def collect_internet_gateway(config):
    """
    Collect OCI Internet Gateways.

    Scope:
        - All subscribed regions
        - All accessible compartments

    Details collected:
        - Internet Gateway OCID
        - Display Name
        - VCN OCID
        - Compartment
        - Region
        - Lifecycle State
        - Enabled / Disabled
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
            "  ERROR: No regions found for Internet Gateway."
        )
        return resources

    if not compartments:
        print(
            "  ERROR: No compartments found for Internet Gateway."
        )
        return resources

    # ============================================================
    # REGIONS
    # ============================================================

    for region in regions:

        print(
            f"  Processing Internet Gateway region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        # ========================================================
        # VIRTUAL NETWORK CLIENT
        # ========================================================

        try:

            virtual_network_client = (
                oci.core.VirtualNetworkClient(
                    region_config
                )
            )

        except Exception as error:

            print(
                f"  ERROR initializing Virtual Network "
                f"client for region {region}: {error}"
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
                f"    Processing Internet Gateway compartment: "
                f"{compartment_name}"
            )

            # ====================================================
            # LIST INTERNET GATEWAYS
            #
            # No VCN filter is used, so all Internet Gateways
            # belonging to this compartment are returned.
            # ====================================================

            try:

                response = (
                    oci.pagination.list_call_get_all_results(
                        virtual_network_client.list_internet_gateways,
                        compartment_id=compartment_id,
                    )
                )

                internet_gateways = response.data

            except Exception as error:

                print(
                    f"      ERROR collecting Internet Gateways "
                    f"from compartment {compartment_name}: "
                    f"{error}"
                )

                continue

            if not internet_gateways:
                continue

            print(
                f"      Found {len(internet_gateways)} "
                f"Internet Gateway(s)"
            )

            # ====================================================
            # PROCESS INTERNET GATEWAYS
            # ====================================================

            for internet_gateway in internet_gateways:

                try:

                    gateway_id = _get(
                        internet_gateway,
                        "id",
                        "",
                    )

                    display_name = _get(
                        internet_gateway,
                        "display_name",
                        "",
                    )

                    vcn_id = _get(
                        internet_gateway,
                        "vcn_id",
                        "",
                    )

                    lifecycle_state = _get(
                        internet_gateway,
                        "lifecycle_state",
                        "",
                    )

                    time_created = _get(
                        internet_gateway,
                        "time_created",
                        None,
                    )

                    enabled = _get(
                        internet_gateway,
                        "is_enabled",
                        None,
                    )

                    route_table_id = _get(
                        internet_gateway,
                        "route_table_id",
                        "",
                    )

                    defined_tags = _get(
                        internet_gateway,
                        "defined_tags",
                        {},
                    ) or {}

                    freeform_tags = _get(
                        internet_gateway,
                        "freeform_tags",
                        {},
                    ) or {}

                    # =================================================
                    # RESOURCE
                    # =================================================

                    resource = {

                        "service":
                            "Networking",

                        "resource_type":
                            "Internet Gateway",

                        "id":
                            gateway_id,

                        "ocid":
                            gateway_id,

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
                            compartment_id,

                        "compartment_name":
                            compartment_name,

                        # -----------------------------------------
                        # NETWORK
                        # -----------------------------------------

                        "vcn_id":
                            vcn_id,

                        "vcn_ocid":
                            vcn_id,

                        # -----------------------------------------
                        # STATE
                        # -----------------------------------------

                        "lifecycle_state":
                            lifecycle_state,

                        "state":
                            lifecycle_state,

                        "is_enabled":
                            enabled,

                        "enabled":
                            enabled,

                        # -----------------------------------------
                        # ROUTING
                        # -----------------------------------------

                        "route_table_id":
                            route_table_id,

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
                        f"      ERROR processing Internet Gateway "
                        f"{_get(internet_gateway, 'display_name', '')}: "
                        f"{error}"
                    )

    # ============================================================
    # SUMMARY
    # ============================================================

    print(
        f"Internet Gateway: {len(resources)} resources found"
    )

    return resources
