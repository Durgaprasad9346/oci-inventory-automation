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

        if hasattr(
            value,
            "to_dict",
        ):
            return _safe_value(
                value.to_dict()
            )

    except Exception:
        pass

    return str(value)


def collect_drg(config):
    """
    Collect OCI Dynamic Routing Gateways (DRGs).

    Scope:
        - All subscribed regions
        - All accessible compartments

    Details collected:
        - DRG OCID
        - Display Name
        - Region
        - Compartment
        - Lifecycle State
        - Creation Date
        - Default DRG Route Table information
        - Default Export Route Distribution
        - Defined Tags
        - Freeform Tags
    """

    resources = []

    # ============================================================
    # COMMON REGION / COMPARTMENT DISCOVERY
    # ============================================================

    regions = get_regions(config)
    compartments = get_compartments(config)

    if not regions:

        print(
            "  ERROR: No regions found for DRG."
        )

        return resources

    if not compartments:

        print(
            "  ERROR: No compartments found for DRG."
        )

        return resources

    # ============================================================
    # REGIONS
    # ============================================================

    for region in regions:

        print(
            f"  Processing DRG region: {region}"
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
                f"client for region {region}: "
                f"{error}"
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
                f"    Processing DRG compartment: "
                f"{compartment_name}"
            )

            # ====================================================
            # LIST DRGs
            # ====================================================

            try:

                response = (
                    oci.pagination.list_call_get_all_results(
                        virtual_network_client.list_drgs,
                        compartment_id=compartment_id,
                    )
                )

                drgs = response.data

            except Exception as error:

                print(
                    f"      ERROR collecting DRGs from "
                    f"compartment {compartment_name}: "
                    f"{error}"
                )

                continue

            if not drgs:
                continue

            print(
                f"      Found {len(drgs)} DRG(s)"
            )

            # ====================================================
            # PROCESS DRGs
            # ====================================================

            for drg in drgs:

                try:

                    drg_id = _get(
                        drg,
                        "id",
                        "",
                    )

                    display_name = _get(
                        drg,
                        "display_name",
                        "",
                    )

                    lifecycle_state = _get(
                        drg,
                        "lifecycle_state",
                        "",
                    )

                    time_created = _get(
                        drg,
                        "time_created",
                        None,
                    )

                    # ============================================
                    # DEFAULT DRG ROUTE TABLES
                    # ============================================

                    default_drg_route_tables = _get(
                        drg,
                        "default_drg_route_tables",
                        None,
                    )

                    default_drg_route_tables_value = (
                        _safe_value(
                            default_drg_route_tables
                        )
                    )

                    default_vcn_drg_route_table_id = ""

                    default_drg_route_table_id = ""

                    if default_drg_route_tables is not None:

                        default_vcn_drg_route_table_id = _get(
                            default_drg_route_tables,
                            "default_vcn_route_table_id",
                            "",
                        )

                        default_drg_route_table_id = _get(
                            default_drg_route_tables,
                            "default_drg_route_table_id",
                            "",
                        )

                    # ============================================
                    # DEFAULT EXPORT ROUTE DISTRIBUTION
                    # ============================================

                    default_export_drg_route_distribution_id = _get(
                        drg,
                        "default_export_drg_route_distribution_id",
                        "",
                    )

                    # ============================================
                    # TAGS
                    # ============================================

                    defined_tags = _get(
                        drg,
                        "defined_tags",
                        {},
                    ) or {}

                    freeform_tags = _get(
                        drg,
                        "freeform_tags",
                        {},
                    ) or {}

                    # ============================================
                    # RESOURCE
                    # ============================================

                    resource = {

                        "service":
                            "DRG",

                        "resource_type":
                            "Dynamic Routing Gateway",

                        "id":
                            drg_id,

                        "ocid":
                            drg_id,

                        "name":
                            display_name,

                        "display_name":
                            display_name,

                        # ----------------------------------------
                        # LOCATION
                        # ----------------------------------------

                        "region":
                            region,

                        "compartment_id":
                            compartment_id,

                        "compartment_name":
                            compartment_name,

                        # ----------------------------------------
                        # STATE
                        # ----------------------------------------

                        "lifecycle_state":
                            lifecycle_state,

                        "state":
                            lifecycle_state,

                        # ----------------------------------------
                        # TIME
                        # ----------------------------------------

                        "time_created":
                            time_created,

                        # ----------------------------------------
                        # ROUTE TABLES
                        # ----------------------------------------

                        "default_drg_route_table_id":
                            default_drg_route_table_id,

                        "default_vcn_drg_route_table_id":
                            default_vcn_drg_route_table_id,

                        "default_drg_route_tables":
                            default_drg_route_tables_value,

                        # ----------------------------------------
                        # ROUTE DISTRIBUTION
                        # ----------------------------------------

                        "default_export_drg_route_distribution_id":
                            default_export_drg_route_distribution_id,

                        # ----------------------------------------
                        # TAGS
                        # ----------------------------------------

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
                        f"      ERROR processing DRG "
                        f"{_get(drg, 'display_name', '')}: "
                        f"{error}"
                    )

    # ============================================================
    # SUMMARY
    # ============================================================

    print(
        f"DRG: {len(resources)} resources found"
    )

    return resources
