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


def collect_nat_gateway(config):
    """
    Collect OCI NAT Gateways.

    Scope:
        - All subscribed regions
        - All accessible compartments

    Details collected:
        - NAT Gateway OCID
        - Display Name
        - VCN OCID
        - NAT IP
        - Public IP OCID
        - Route Table OCID
        - Block Traffic
        - Lifecycle State
        - Creation Date
        - Compartment
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
            "  ERROR: No regions found for NAT Gateway."
        )
        return resources

    if not compartments:
        print(
            "  ERROR: No compartments found for NAT Gateway."
        )
        return resources

    # ============================================================
    # REGIONS
    # ============================================================

    for region in regions:

        print(
            f"  Processing NAT Gateway region: {region}"
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
                f"    Processing NAT Gateway compartment: "
                f"{compartment_name}"
            )

            # ====================================================
            # LIST NAT GATEWAYS
            # ====================================================

            try:

                response = (
                    oci.pagination.list_call_get_all_results(
                        virtual_network_client.list_nat_gateways,
                        compartment_id=compartment_id,
                    )
                )

                nat_gateways = response.data

            except Exception as error:

                print(
                    f"      ERROR collecting NAT Gateways "
                    f"from compartment {compartment_name}: "
                    f"{error}"
                )

                continue

            if not nat_gateways:
                continue

            print(
                f"      Found {len(nat_gateways)} "
                f"NAT Gateway(s)"
            )

            # ====================================================
            # PROCESS NAT GATEWAYS
            # ====================================================

            for nat_gateway in nat_gateways:

                try:

                    nat_gateway_id = _get(
                        nat_gateway,
                        "id",
                        "",
                    )

                    display_name = _get(
                        nat_gateway,
                        "display_name",
                        "",
                    )

                    vcn_id = _get(
                        nat_gateway,
                        "vcn_id",
                        "",
                    )

                    nat_ip = _get(
                        nat_gateway,
                        "nat_ip",
                        "",
                    )

                    public_ip_id = _get(
                        nat_gateway,
                        "public_ip_id",
                        "",
                    )

                    route_table_id = _get(
                        nat_gateway,
                        "route_table_id",
                        "",
                    )

                    block_traffic = _get(
                        nat_gateway,
                        "block_traffic",
                        None,
                    )

                    lifecycle_state = _get(
                        nat_gateway,
                        "lifecycle_state",
                        "",
                    )

                    time_created = _get(
                        nat_gateway,
                        "time_created",
                        None,
                    )

                    # =================================================
                    # GET DETAILS
                    # =================================================

                    nat_gateway_details = nat_gateway

                    if nat_gateway_id:

                        try:

                            detail_response = (
                                virtual_network_client.get_nat_gateway(
                                    nat_gateway_id
                                )
                            )

                            nat_gateway_details = (
                                detail_response.data
                            )

                        except Exception as detail_error:

                            print(
                                f"        WARNING: Could not get "
                                f"details for NAT Gateway "
                                f"{display_name}: "
                                f"{detail_error}"
                            )

                    # =================================================
                    # REFRESH DETAILS
                    # =================================================

                    display_name = _get(
                        nat_gateway_details,
                        "display_name",
                        display_name,
                    )

                    vcn_id = _get(
                        nat_gateway_details,
                        "vcn_id",
                        vcn_id,
                    )

                    nat_ip = _get(
                        nat_gateway_details,
                        "nat_ip",
                        nat_ip,
                    )

                    public_ip_id = _get(
                        nat_gateway_details,
                        "public_ip_id",
                        public_ip_id,
                    )

                    route_table_id = _get(
                        nat_gateway_details,
                        "route_table_id",
                        route_table_id,
                    )

                    block_traffic = _get(
                        nat_gateway_details,
                        "block_traffic",
                        block_traffic,
                    )

                    lifecycle_state = _get(
                        nat_gateway_details,
                        "lifecycle_state",
                        lifecycle_state,
                    )

                    time_created = _get(
                        nat_gateway_details,
                        "time_created",
                        time_created,
                    )

                    compartment_id_value = _get(
                        nat_gateway_details,
                        "compartment_id",
                        compartment_id,
                    )

                    # =================================================
                    # TAGS
                    # =================================================

                    defined_tags = _get(
                        nat_gateway_details,
                        "defined_tags",
                        {},
                    ) or {}

                    freeform_tags = _get(
                        nat_gateway_details,
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
                            "NAT Gateway",

                        "id":
                            nat_gateway_id,

                        "ocid":
                            nat_gateway_id,

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

                        "vcn_id":
                            vcn_id,

                        "vcn_ocid":
                            vcn_id,

                        "nat_ip":
                            nat_ip,

                        "public_ip_id":
                            public_ip_id,

                        "public_ip_ocid":
                            public_ip_id,

                        "route_table_id":
                            route_table_id,

                        "route_table_ocid":
                            route_table_id,

                        # -----------------------------------------
                        # STATE
                        # -----------------------------------------

                        "block_traffic":
                            block_traffic,

                        "is_block_traffic":
                            block_traffic,

                        "lifecycle_state":
                            lifecycle_state,

                        "state":
                            lifecycle_state,

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
                        f"      ERROR processing NAT Gateway "
                        f"{_get(nat_gateway, 'display_name', '')}: "
                        f"{error}"
                    )

    # ============================================================
    # SUMMARY
    # ============================================================

    print(
        f"NAT Gateway: {len(resources)} resources found"
    )

    return resources
