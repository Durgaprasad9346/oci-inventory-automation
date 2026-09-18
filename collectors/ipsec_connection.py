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
    Convert OCI SDK objects / nested structures into
    safe Python values.
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


def collect_ipsec_connection(config):
    """
    Collect OCI IPSec Connections.

    Scope:
        - All subscribed regions
        - All accessible compartments

    Collects:

        IPSec Connection
        ----------------
        - IPSec Connection OCID
        - Display Name
        - CPE OCID
        - DRG OCID
        - Compartment
        - Region
        - Lifecycle State
        - Creation Date
        - Static Routes
        - Encryption Domain
        - Tags

        VPN Tunnels
        -----------
        - Tunnel OCID
        - Tunnel Display Name
        - Tunnel State
        - Routing Type
        - Oracle VPN IP
        - Customer VPN IP
        - IKE Version
        - BGP information
        - DPD information
        - NAT-T
        - Creation Date
        - Tags
    """

    resources = []

    # ============================================================
    # REGION / COMPARTMENT DISCOVERY
    # ============================================================

    regions = get_regions(config)
    compartments = get_compartments(config)

    if not regions:

        print(
            "  ERROR: No regions found for IPSec Connection."
        )

        return resources

    if not compartments:

        print(
            "  ERROR: No compartments found for IPSec Connection."
        )

        return resources

    # ============================================================
    # REGIONS
    # ============================================================

    for region in regions:

        print(
            f"  Processing IPSec Connection region: {region}"
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
                f"    Processing IPSec Connection compartment: "
                f"{compartment_name}"
            )

            # ====================================================
            # LIST IPSec CONNECTIONS
            # ====================================================

            try:

                response = (
                    oci.pagination.list_call_get_all_results(
                        virtual_network_client.list_ip_sec_connections,
                        compartment_id=compartment_id,
                    )
                )

                connections = response.data

            except Exception as error:

                print(
                    f"      ERROR collecting IPSec Connections "
                    f"from compartment {compartment_name}: "
                    f"{error}"
                )

                continue

            if not connections:
                continue

            print(
                f"      Found {len(connections)} "
                f"IPSec Connection(s)"
            )

            # ====================================================
            # PROCESS CONNECTIONS
            # ====================================================

            for connection in connections:

                try:

                    connection_id = _get(
                        connection,
                        "id",
                        "",
                    )

                    display_name = _get(
                        connection,
                        "display_name",
                        "",
                    )

                    lifecycle_state = _get(
                        connection,
                        "lifecycle_state",
                        "",
                    )

                    time_created = _get(
                        connection,
                        "time_created",
                        None,
                    )

                    cpe_id = _get(
                        connection,
                        "cpe_id",
                        "",
                    )

                    drg_id = _get(
                        connection,
                        "drg_id",
                        "",
                    )

                    static_routes = _get(
                        connection,
                        "static_routes",
                        [],
                    ) or []

                    encryption_domain_config = _get(
                        connection,
                        "encryption_domain_config",
                        None,
                    )

                    compartment_id_value = _get(
                        connection,
                        "compartment_id",
                        compartment_id,
                    )

                    # ============================================
                    # DETAILED CONNECTION
                    # ============================================

                    connection_details = connection

                    if connection_id:

                        try:

                            detail_response = (
                                virtual_network_client.get_ip_sec_connection(
                                    connection_id
                                )
                            )

                            connection_details = (
                                detail_response.data
                            )

                        except Exception as detail_error:

                            print(
                                f"        WARNING: Could not get "
                                f"details for IPSec Connection "
                                f"{display_name}: "
                                f"{detail_error}"
                            )

                    # ============================================
                    # REFRESH DETAILS
                    # ============================================

                    lifecycle_state = _get(
                        connection_details,
                        "lifecycle_state",
                        lifecycle_state,
                    )

                    time_created = _get(
                        connection_details,
                        "time_created",
                        time_created,
                    )

                    cpe_id = _get(
                        connection_details,
                        "cpe_id",
                        cpe_id,
                    )

                    drg_id = _get(
                        connection_details,
                        "drg_id",
                        drg_id,
                    )

                    static_routes = _get(
                        connection_details,
                        "static_routes",
                        static_routes,
                    ) or []

                    encryption_domain_config = _get(
                        connection_details,
                        "encryption_domain_config",
                        encryption_domain_config,
                    )

                    # ============================================
                    # TAGS
                    # ============================================

                    defined_tags = _get(
                        connection_details,
                        "defined_tags",
                        {},
                    ) or {}

                    freeform_tags = _get(
                        connection_details,
                        "freeform_tags",
                        {},
                    ) or {}

                    # ============================================
                    # TUNNELS
                    # ============================================

                    tunnels = []

                    if connection_id:

                        try:

                            tunnel_response = (
                                oci.pagination.list_call_get_all_results(
                                    virtual_network_client.list_ip_sec_connection_tunnels,
                                    ipsc_id=connection_id,
                                )
                            )

                            for tunnel in tunnel_response.data:

                                tunnel_id = _get(
                                    tunnel,
                                    "id",
                                    "",
                                )

                                tunnel_details = tunnel

                                # --------------------------------
                                # Get detailed tunnel information
                                # --------------------------------

                                if tunnel_id:

                                    try:

                                        tunnel_detail_response = (
                                            virtual_network_client.get_ip_sec_connection_tunnel(
                                                connection_id,
                                                tunnel_id,
                                            )
                                        )

                                        tunnel_details = (
                                            tunnel_detail_response.data
                                        )

                                    except Exception as tunnel_detail_error:

                                        print(
                                            f"        WARNING: Could not "
                                            f"get details for tunnel "
                                            f"{tunnel_id}: "
                                            f"{tunnel_detail_error}"
                                        )

                                # --------------------------------
                                # Tunnel properties
                                # --------------------------------

                                tunnel_data = {

                                    "id":
                                        tunnel_id,

                                    "display_name":
                                        _get(
                                            tunnel_details,
                                            "display_name",
                                            "",
                                        ),

                                    "lifecycle_state":
                                        _get(
                                            tunnel_details,
                                            "lifecycle_state",
                                            "",
                                        ),

                                    "time_created":
                                        _get(
                                            tunnel_details,
                                            "time_created",
                                            None,
                                        ),

                                    "routing":
                                        _get(
                                            tunnel_details,
                                            "routing",
                                            "",
                                        ),

                                    "ike_version":
                                        _get(
                                            tunnel_details,
                                            "ike_version",
                                            "",
                                        ),

                                    "oracle_id":
                                        _get(
                                            tunnel_details,
                                            "oracle_id",
                                            "",
                                        ),

                                    "customer_gateway_configuration":
                                        _get(
                                            tunnel_details,
                                            "customer_gateway_configuration",
                                            "",
                                        ),

                                    "vpn_ip":
                                        _get(
                                            tunnel_details,
                                            "vpn_ip",
                                            "",
                                        ),

                                    "customer_vpn_ip":
                                        _get(
                                            tunnel_details,
                                            "customer_vpn_ip",
                                            "",
                                        ),

                                    "oracle_initiation":
                                        _get(
                                            tunnel_details,
                                            "oracle_initiation",
                                            "",
                                        ),

                                    "nat_translation_enabled":
                                        _get(
                                            tunnel_details,
                                            "nat_translation_enabled",
                                            None,
                                        ),

                                    "dpd_mode":
                                        _get(
                                            tunnel_details,
                                            "dpd_mode",
                                            "",
                                        ),

                                    "dpd_timeout_in_sec":
                                        _get(
                                            tunnel_details,
                                            "dpd_timeout_in_sec",
                                            None,
                                        ),

                                    "bgp_session_info":
                                        _safe_value(
                                            _get(
                                                tunnel_details,
                                                "bgp_session_info",
                                                None,
                                            )
                                        ),

                                    "encryption_domain_config":
                                        _safe_value(
                                            _get(
                                                tunnel_details,
                                                "encryption_domain_config",
                                                None,
                                            )
                                        ),
                                }

                                tunnels.append(
                                    tunnel_data
                                )

                        except Exception as tunnel_error:

                            print(
                                f"        WARNING: Could not collect "
                                f"tunnels for IPSec Connection "
                                f"{display_name}: "
                                f"{tunnel_error}"
                            )

                    # ============================================
                    # RESOURCE
                    # ============================================

                    resource = {

                        "service":
                            "Networking",

                        "resource_type":
                            "IPSec Connection",

                        "id":
                            connection_id,

                        "ocid":
                            connection_id,

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
                        # NETWORK
                        # -----------------------------------------

                        "cpe_id":
                            cpe_id,

                        "cpe_ocid":
                            cpe_id,

                        "drg_id":
                            drg_id,

                        "drg_ocid":
                            drg_id,

                        # -----------------------------------------
                        # STATE
                        # -----------------------------------------

                        "lifecycle_state":
                            lifecycle_state,

                        "state":
                            lifecycle_state,

                        # -----------------------------------------
                        # ROUTING
                        # -----------------------------------------

                        "static_routes":
                            _safe_value(
                                static_routes
                            ),

                        "static_route_count":
                            len(static_routes),

                        # -----------------------------------------
                        # ENCRYPTION
                        # -----------------------------------------

                        "encryption_domain_config":
                            _safe_value(
                                encryption_domain_config
                            ),

                        # -----------------------------------------
                        # TUNNELS
                        # -----------------------------------------

                        "tunnels":
                            _safe_value(
                                tunnels
                            ),

                        "tunnel_count":
                            len(tunnels),

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
                        f"      ERROR processing IPSec Connection "
                        f"{_get(connection, 'display_name', '')}: "
                        f"{error}"
                    )

    # ============================================================
    # SUMMARY
    # ============================================================

    print(
        f"IPSec Connections: {len(resources)} resources found"
    )

    return resources
