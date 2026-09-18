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


def collect_remote_peering_connection(config):
    """
    Collect OCI Remote Peering Connections (RPCs).

    Scope:
        - All subscribed regions
        - All accessible compartments

    Details collected:
        - RPC OCID
        - Display Name
        - DRG OCID
        - Peer Region
        - Peer RPC OCID
        - Peering Status
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
            "  ERROR: No regions found for Remote Peering Connection."
        )
        return resources

    if not compartments:
        print(
            "  ERROR: No compartments found for Remote Peering Connection."
        )
        return resources

    # ============================================================
    # REGIONS
    # ============================================================

    for region in regions:

        print(
            f"  Processing Remote Peering Connection region: {region}"
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
                f"    Processing Remote Peering Connection "
                f"compartment: {compartment_name}"
            )

            # ====================================================
            # LIST RPCs
            #
            # No DRG filter means all RPCs in this compartment.
            # ====================================================

            try:

                response = (
                    oci.pagination.list_call_get_all_results(
                        virtual_network_client.list_remote_peering_connections,
                        compartment_id=compartment_id,
                    )
                )

                rpc_connections = response.data

            except Exception as error:

                print(
                    f"      ERROR collecting Remote Peering "
                    f"Connections from compartment "
                    f"{compartment_name}: {error}"
                )

                continue

            if not rpc_connections:
                continue

            print(
                f"      Found {len(rpc_connections)} "
                f"Remote Peering Connection(s)"
            )

            # ====================================================
            # PROCESS RPCs
            # ====================================================

            for rpc in rpc_connections:

                try:

                    rpc_id = _get(
                        rpc,
                        "id",
                        "",
                    )

                    display_name = _get(
                        rpc,
                        "display_name",
                        "",
                    )

                    lifecycle_state = _get(
                        rpc,
                        "lifecycle_state",
                        "",
                    )

                    time_created = _get(
                        rpc,
                        "time_created",
                        None,
                    )

                    drg_id = _get(
                        rpc,
                        "drg_id",
                        "",
                    )

                    peer_id = _get(
                        rpc,
                        "peer_id",
                        "",
                    )

                    peer_region = _get(
                        rpc,
                        "peer_region",
                        "",
                    )

                    peering_status = _get(
                        rpc,
                        "peering_status",
                        "",
                    )

                    # =================================================
                    # GET DETAILED RPC
                    # =================================================

                    rpc_details = rpc

                    if rpc_id:

                        try:

                            detail_response = (
                                virtual_network_client.get_remote_peering_connection(
                                    rpc_id
                                )
                            )

                            rpc_details = (
                                detail_response.data
                            )

                        except Exception as detail_error:

                            print(
                                f"        WARNING: Could not get "
                                f"details for RPC {display_name}: "
                                f"{detail_error}"
                            )

                    # =================================================
                    # REFRESH DETAILS
                    # =================================================

                    display_name = _get(
                        rpc_details,
                        "display_name",
                        display_name,
                    )

                    lifecycle_state = _get(
                        rpc_details,
                        "lifecycle_state",
                        lifecycle_state,
                    )

                    time_created = _get(
                        rpc_details,
                        "time_created",
                        time_created,
                    )

                    drg_id = _get(
                        rpc_details,
                        "drg_id",
                        drg_id,
                    )

                    peer_id = _get(
                        rpc_details,
                        "peer_id",
                        peer_id,
                    )

                    peer_region = _get(
                        rpc_details,
                        "peer_region",
                        peer_region,
                    )

                    peering_status = _get(
                        rpc_details,
                        "peering_status",
                        peering_status,
                    )

                    compartment_id_value = _get(
                        rpc_details,
                        "compartment_id",
                        compartment_id,
                    )

                    # =================================================
                    # TAGS
                    # =================================================

                    defined_tags = _get(
                        rpc_details,
                        "defined_tags",
                        {},
                    ) or {}

                    freeform_tags = _get(
                        rpc_details,
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
                            "Remote Peering Connection",

                        "id":
                            rpc_id,

                        "ocid":
                            rpc_id,

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
                        # DRG
                        # -----------------------------------------

                        "drg_id":
                            drg_id,

                        "drg_ocid":
                            drg_id,

                        # -----------------------------------------
                        # PEERING
                        # -----------------------------------------

                        "peer_id":
                            peer_id,

                        "peer_rpc_ocid":
                            peer_id,

                        "peer_region":
                            peer_region,

                        "peering_status":
                            peering_status,

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
                        f"      ERROR processing RPC "
                        f"{_get(rpc, 'display_name', '')}: "
                        f"{error}"
                    )

    # ============================================================
    # SUMMARY
    # ============================================================

    print(
        f"Remote Peering Connections: "
        f"{len(resources)} resources found"
    )

    return resources
