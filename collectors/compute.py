import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def _safe_get(obj, attribute, default=""):
    """
    Safely get an attribute from an OCI SDK object.
    """
    try:
        value = getattr(obj, attribute, default)
        return default if value is None else value
    except Exception:
        return default


def _get_vnic_details(compute_client, network_client, vnic_attachment):
    """
    Get VNIC details including private/public IP, subnet and MAC.
    """

    result = {
        "vnic_id": "",
        "private_ip": "",
        "public_ip": "",
        "subnet_id": "",
        "subnet_name": "",
        "mac_address": "",
        "hostname_label": "",
        "nic_index": "",
        "vlan_tag": "",
    }

    if not vnic_attachment:
        return result

    vnic_id = _safe_get(
        vnic_attachment,
        "vnic_id",
        "",
    )

    result["vnic_id"] = vnic_id

    if not vnic_id:
        return result

    # ---------------------------------------------------------
    # GET VNIC
    # ---------------------------------------------------------

    try:
        vnic_response = network_client.get_vnic(
            vnic_id
        )

        vnic = vnic_response.data

    except Exception:
        return result

    result["private_ip"] = _safe_get(
        vnic,
        "private_ip",
        "",
    )

    result["public_ip"] = _safe_get(
        vnic,
        "public_ip",
        "",
    )

    result["subnet_id"] = _safe_get(
        vnic,
        "subnet_id",
        "",
    )

    result["mac_address"] = _safe_get(
        vnic,
        "mac_address",
        "",
    )

    result["hostname_label"] = _safe_get(
        vnic,
        "hostname_label",
        "",
    )

    result["vlan_tag"] = _safe_get(
        vnic,
        "vlan_tag",
        "",
    )

    result["nic_index"] = _safe_get(
        vnic,
        "nic_index",
        "",
    )

    # ---------------------------------------------------------
    # GET SUBNET NAME
    # ---------------------------------------------------------

    subnet_id = result["subnet_id"]

    if subnet_id:

        try:

            subnet_response = network_client.get_subnet(
                subnet_id
            )

            subnet = subnet_response.data

            result["subnet_name"] = _safe_get(
                subnet,
                "display_name",
                "",
            )

        except Exception:
            pass

    return result


def _get_shape_details(compute_client, instance):
    """
    Get OCPU, memory and VCPU information.

    OCI instances can have shape configuration directly on the
    instance. For older/flex shapes we also query the shape
    configuration API when necessary.
    """

    result = {
        "shape": _safe_get(
            instance,
            "shape",
            "",
        ),
        "ocpu": "",
        "memory_gb": "",
        "vcpus": "",
        "baseline_ocpu_utilization": "",
        "processor_description": "",
    }

    shape_config = _safe_get(
        instance,
        "shape_config",
        None,
    )

    if shape_config:

        result["ocpu"] = _safe_get(
            shape_config,
            "ocpus",
            "",
        )

        result["memory_gb"] = _safe_get(
            shape_config,
            "memory_in_gbs",
            "",
        )

        result["vcpus"] = _safe_get(
            shape_config,
            "vcpus",
            "",
        )

        result["baseline_ocpu_utilization"] = _safe_get(
            shape_config,
            "baseline_ocpu_utilization",
            "",
        )

        result["processor_description"] = _safe_get(
            shape_config,
            "processor_description",
            "",
        )

    # ---------------------------------------------------------
    # FALLBACK: GET SHAPE CONFIG
    # ---------------------------------------------------------

    if (
        not result["ocpu"]
        or not result["memory_gb"]
        or not result["vcpus"]
    ):

        shape_name = result["shape"]

        if shape_name:

            try:

                response = compute_client.get_shape(
                    shape_name
                )

                shape = response.data

                if not result["ocpu"]:
                    result["ocpu"] = _safe_get(
                        shape,
                        "ocpus",
                        "",
                    )

                if not result["memory_gb"]:
                    result["memory_gb"] = _safe_get(
                        shape,
                        "memory_in_gbs",
                        "",
                    )

                if not result["vcpus"]:
                    result["vcpus"] = _safe_get(
                        shape,
                        "vcpus",
                        "",
                    )

            except Exception:
                pass

    return result


def collect_compute(config):

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing Compute region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        compute_client = oci.core.ComputeClient(
            region_config
        )

        network_client = oci.core.VirtualNetworkClient(
            region_config
        )

        for compartment in compartments:

            compartment_id = compartment["id"]
            compartment_name = compartment["name"]

            # -----------------------------------------------------
            # LIST INSTANCES
            # -----------------------------------------------------

            try:

                instances = (
                    oci.pagination.list_call_get_all_results(
                        compute_client.list_instances,
                        compartment_id=compartment_id,
                    )
                )

            except Exception as error:

                print(
                    f"    ERROR collecting Compute instances "
                    f"from compartment {compartment_name}: {error}"
                )

                continue

            # -----------------------------------------------------
            # EACH INSTANCE
            # -----------------------------------------------------

            for instance in instances.data:

                instance_id = _safe_get(
                    instance,
                    "id",
                    "",
                )

                instance_name = _safe_get(
                    instance,
                    "display_name",
                    "",
                )

                if not instance_id:
                    continue

                # -------------------------------------------------
                # SHAPE / CPU / MEMORY
                # -------------------------------------------------

                shape_details = _get_shape_details(
                    compute_client,
                    instance,
                )

                # -------------------------------------------------
                # VNIC ATTACHMENTS
                # -------------------------------------------------

                vnic_details = {
                    "vnic_id": "",
                    "private_ip": "",
                    "public_ip": "",
                    "subnet_id": "",
                    "subnet_name": "",
                    "mac_address": "",
                    "hostname_label": "",
                    "nic_index": "",
                    "vlan_tag": "",
                }

                try:

                    vnic_attachments = (
                        oci.pagination.list_call_get_all_results(
                            compute_client.list_vnic_attachments,
                            compartment_id=compartment_id,
                            instance_id=instance_id,
                        )
                    )

                    # Primary VNIC = NIC index 0
                    selected_attachment = None

                    for attachment in vnic_attachments.data:

                        nic_index = _safe_get(
                            attachment,
                            "nic_index",
                            None,
                        )

                        if nic_index == 0:

                            selected_attachment = attachment
                            break

                    # Fallback to first attachment
                    if (
                        selected_attachment is None
                        and vnic_attachments.data
                    ):
                        selected_attachment = (
                            vnic_attachments.data[0]
                        )

                    if selected_attachment:

                        vnic_details = _get_vnic_details(
                            compute_client,
                            network_client,
                            selected_attachment,
                        )

                except Exception as error:

                    print(
                        f"    WARNING: Could not collect VNIC "
                        f"details for {instance_name}: {error}"
                    )

                # -------------------------------------------------
                # INSTANCE DETAILS
                # -------------------------------------------------

                details = {

                    # Basic
                    "shape": shape_details["shape"],

                    # CPU / MEMORY
                    "ocpu": shape_details["ocpu"],
                    "ocpus": shape_details["ocpu"],
                    "memory_gb": shape_details["memory_gb"],
                    "memory_in_gbs": shape_details["memory_gb"],
                    "vcpus": shape_details["vcpus"],

                    "baseline_ocpu_utilization":
                        shape_details[
                            "baseline_ocpu_utilization"
                        ],

                    "processor_description":
                        shape_details[
                            "processor_description"
                        ],

                    # Networking
                    "vnic_id":
                        vnic_details["vnic_id"],

                    "private_ip":
                        vnic_details["private_ip"],

                    "public_ip":
                        vnic_details["public_ip"],

                    "subnet_id":
                        vnic_details["subnet_id"],

                    "subnet_name":
                        vnic_details["subnet_name"],

                    "mac_address":
                        vnic_details["mac_address"],

                    "hostname_label":
                        vnic_details["hostname_label"],

                    "nic_index":
                        vnic_details["nic_index"],

                    "vlan_tag":
                        vnic_details["vlan_tag"],

                    # Image
                    "image_id": _safe_get(
                        instance,
                        "image_id",
                        "",
                    ),

                    # Availability / Fault domain
                    "availability_domain":
                        _safe_get(
                            instance,
                            "availability_domain",
                            "",
                        ),

                    "fault_domain":
                        _safe_get(
                            instance,
                            "fault_domain",
                            "",
                        ),

                    # Platform
                    "platform_config":
                        _safe_get(
                            instance,
                            "platform_config",
                            "",
                        ),

                    # Launch mode
                    "launch_mode":
                        _safe_get(
                            instance,
                            "launch_mode",
                            "",
                        ),

                    # Boot volume
                    "boot_volume_id":
                        _safe_get(
                            instance,
                            "boot_volume_id",
                            "",
                        ),

                    # Private DNS
                    "private_dns_name":
                        _safe_get(
                            instance,
                            "private_dns_name",
                            "",
                        ),

                    # IPv6
                    "ipv6_address":
                        _safe_get(
                            instance,
                            "ipv6_address",
                            "",
                        ),

                    # Lifecycle
                    "lifecycle_details":
                        _safe_get(
                            instance,
                            "lifecycle_details",
                            "",
                        ),

                    # Metadata
                    "metadata":
                        _safe_get(
                            instance,
                            "metadata",
                            "",
                        ),
                }

                # -------------------------------------------------
                # RESOURCE
                # -------------------------------------------------

                resources.append(
                    Resource(
                        service="Compute",
                        resource_type="Instance",
                        name=instance_name,
                        ocid=instance_id,
                        compartment_id=compartment_id,
                        compartment_name=compartment_name,
                        region=region,
                        state=_safe_get(
                            instance,
                            "lifecycle_state",
                            "",
                        ),
                        time_created=_safe_get(
                            instance,
                            "time_created",
                            None,
                        ),
                        defined_tags=_safe_get(
                            instance,
                            "defined_tags",
                            None,
                        ),
                        freeform_tags=_safe_get(
                            instance,
                            "freeform_tags",
                            None,
                        ),
                        details=details,
                    )
                )

    return resources
