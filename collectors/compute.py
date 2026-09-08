import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def _get(obj, name, default=None):
    """
    Safely get a value from an OCI SDK object or dictionary.
    """
    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(name, default)

    return getattr(obj, name, default)


def _safe_value(value):
    """
    Convert OCI SDK objects into Excel-safe values.
    """

    if value is None:
        return ""

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, dict):
        result = {}

        for key, val in value.items():
            result[str(key)] = _safe_value(val)

        return result

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


def _get_shape_details(
    compute_client,
    shape_name,
):
    """
    Get additional shape information when
    instance.shape_config does not contain
    complete information.
    """

    if not shape_name:
        return None

    try:

        response = compute_client.get_shape(
            shape_name
        )

        return response.data

    except Exception:
        return None


def _get_vnic_details(
    virtual_network_client,
    vnic_id,
):
    """
    Get primary VNIC details.
    """

    if not vnic_id:
        return None

    try:

        response = (
            virtual_network_client.get_vnic(
                vnic_id
            )
        )

        return response.data

    except Exception:
        return None


def _get_boot_volume_attachments(
    compute_client,
    compartment_id,
):
    """
    Get Boot Volume attachments for a compartment.

    Returns a dictionary:

        instance_id -> boot_volume_id
    """

    result = {}

    try:

        response = (
            oci.pagination.list_call_get_all_results(
                compute_client.list_boot_volume_attachments,
                compartment_id=compartment_id,
            )
        )

        for attachment in response.data:

            instance_id = _get(
                attachment,
                "instance_id",
                "",
            )

            boot_volume_id = _get(
                attachment,
                "boot_volume_id",
                "",
            )

            if instance_id and boot_volume_id:

                result[instance_id] = (
                    boot_volume_id
                )

    except Exception as exc:

        print(
            f"    WARNING collecting Boot Volume "
            f"attachments from compartment "
            f"{compartment_id}: {exc}"
        )

    return result


def collect_compute(config):
    """
    Collect OCI Compute Instances across:

        - All subscribed regions
        - All accessible compartments

    Detailed information collected:

        Basic
        -----
        Instance Name
        OCID
        Lifecycle State
        Lifecycle Details
        Time Created

        Compute
        -------
        Shape
        OCPU
        Memory GB
        VCPU
        Baseline OCPU Utilization
        Processor Description

        Networking
        ----------
        VNIC OCID
        Private IP
        Public IP
        IPv6
        MAC Address
        Subnet OCID
        Hostname
        Private DNS Name
        VLAN Tag
        NIC Index

        Placement
        ---------
        Availability Domain
        Fault Domain

        Image
        -----
        Image OCID

        Storage
        -------
        Boot Volume OCID

        Tags
        ----
        Freeform Tags
        Defined Tags
    """

    resources = []

    compartments = get_compartments(
        config
    )

    regions = get_regions(
        config
    )

    for region in regions:

        print(
            f"  Processing Compute region: {region}"
        )

        region_config = config.copy()

        region_config["region"] = region

        try:

            compute_client = (
                oci.core.ComputeClient(
                    region_config
                )
            )

            virtual_network_client = (
                oci.core.VirtualNetworkClient(
                    region_config
                )
            )

        except Exception as exc:

            print(
                f"  ERROR creating Compute clients "
                f"for region {region}: {exc}"
            )

            continue

        for compartment in compartments:

            compartment_id = _get(
                compartment,
                "id",
                "",
            )

            compartment_name = _get(
                compartment,
                "name",
                compartment_id,
            )

            if not compartment_id:
                continue

            # ----------------------------------------------------
            # Collect Compute Instances
            # ----------------------------------------------------

            try:

                instances_response = (
                    oci.pagination.list_call_get_all_results(
                        compute_client.list_instances,
                        compartment_id=compartment_id,
                    )
                )

                instances = (
                    instances_response.data
                )

            except Exception as exc:

                print(
                    f"    ERROR collecting Compute "
                    f"from compartment "
                    f"{compartment_name}: {exc}"
                )

                continue

            # ----------------------------------------------------
            # Get Boot Volume Attachments
            # ----------------------------------------------------

            boot_volume_map = (
                _get_boot_volume_attachments(
                    compute_client,
                    compartment_id,
                )
            )

            for instance in instances:

                try:

                    instance_id = _get(
                        instance,
                        "id",
                        "",
                    )

                    display_name = _get(
                        instance,
                        "display_name",
                        "",
                    )

                    lifecycle_state = _get(
                        instance,
                        "lifecycle_state",
                        "",
                    )

                    lifecycle_details = _get(
                        instance,
                        "lifecycle_details",
                        "",
                    )

                    time_created = _get(
                        instance,
                        "time_created",
                        None,
                    )

                    # ==================================================
                    # SHAPE
                    # ==================================================

                    shape = _get(
                        instance,
                        "shape",
                        "",
                    )

                    shape_config = _get(
                        instance,
                        "shape_config",
                        None,
                    )

                    ocpus = _get(
                        shape_config,
                        "ocpus",
                        None,
                    )

                    memory_in_gbs = _get(
                        shape_config,
                        "memory_in_gbs",
                        None,
                    )

                    vcpus = _get(
                        shape_config,
                        "vcpus",
                        None,
                    )

                    baseline_ocpu_utilization = _get(
                        shape_config,
                        "baseline_ocpu_utilization",
                        None,
                    )

                    processor_description = _get(
                        shape_config,
                        "processor_description",
                        None,
                    )

                    # --------------------------------------------------
                    # If shape_config is incomplete, get shape details
                    # --------------------------------------------------

                    if (
                        ocpus is None
                        or memory_in_gbs is None
                        or vcpus is None
                    ):

                        shape_details = (
                            _get_shape_details(
                                compute_client,
                                shape,
                            )
                        )

                        if shape_details:

                            if ocpus is None:

                                ocpus = _get(
                                    shape_details,
                                    "ocpus",
                                    None,
                                )

                            if memory_in_gbs is None:

                                memory_in_gbs = _get(
                                    shape_details,
                                    "memory_in_gbs",
                                    None,
                                )

                            if vcpus is None:

                                vcpus = _get(
                                    shape_details,
                                    "vcpus",
                                    None,
                                )

                    # ==================================================
                    # PRIMARY VNIC
                    # ==================================================

                    vnic_id = _get(
                        instance,
                        "vnic_id",
                        "",
                    )

                    private_ip = ""
                    public_ip = ""
                    ipv6_address = ""
                    mac_address = ""
                    subnet_id = ""
                    hostname = ""
                    hostname_label = ""
                    private_dns_name = ""
                    vlan_tag = ""
                    nic_index = ""

                    if vnic_id:

                        vnic = _get_vnic_details(
                            virtual_network_client,
                            vnic_id,
                        )

                        if vnic:

                            private_ip = _get(
                                vnic,
                                "private_ip",
                                "",
                            )

                            public_ip = _get(
                                vnic,
                                "public_ip",
                                "",
                            )

                            ipv6_address = _get(
                                vnic,
                                "ipv6_address",
                                "",
                            )

                            mac_address = _get(
                                vnic,
                                "mac_address",
                                "",
                            )

                            subnet_id = _get(
                                vnic,
                                "subnet_id",
                                "",
                            )

                            hostname = _get(
                                vnic,
                                "hostname_label",
                                "",
                            )

                            hostname_label = _get(
                                vnic,
                                "hostname_label",
                                "",
                            )

                            private_dns_name = _get(
                                vnic,
                                "private_dns_name",
                                "",
                            )

                            vlan_tag = _get(
                                vnic,
                                "vlan_tag",
                                "",
                            )

                            nic_index = _get(
                                vnic,
                                "nic_index",
                                "",
                            )

                    # ==================================================
                    # BOOT VOLUME
                    # ==================================================

                    boot_volume_id = (
                        boot_volume_map.get(
                            instance_id,
                            "",
                        )
                    )

                    # ==================================================
                    # IMAGE
                    # ==================================================

                    image_id = _get(
                        instance,
                        "image_id",
                        "",
                    )

                    # ==================================================
                    # PLACEMENT
                    # ==================================================

                    availability_domain = _get(
                        instance,
                        "availability_domain",
                        "",
                    )

                    fault_domain = _get(
                        instance,
                        "fault_domain",
                        "",
                    )

                    launch_mode = _get(
                        instance,
                        "launch_mode",
                        "",
                    )

                    # ==================================================
                    # TAGS
                    # ==================================================

                    freeform_tags = _get(
                        instance,
                        "freeform_tags",
                        {},
                    )

                    defined_tags = _get(
                        instance,
                        "defined_tags",
                        {},
                    )

                    # ==================================================
                    # RESOURCE OBJECT
                    # ==================================================

                    resource = Resource(

                        service="Compute",

                        resource_type="Instance",

                        name=display_name,

                        ocid=instance_id,

                        compartment_id=compartment_id,

                        compartment_name=compartment_name,

                        region=region,

                        state=lifecycle_state,

                        time_created=time_created,

                        defined_tags=_safe_value(
                            defined_tags
                        ),

                        details={

                            # ------------------------------------------
                            # BASIC
                            # ------------------------------------------

                            "display_name":
                                display_name,

                            "instance_id":
                                instance_id,

                            "lifecycle_state":
                                lifecycle_state,

                            "lifecycle_details":
                                lifecycle_details,

                            "time_created":
                                time_created,

                            # ------------------------------------------
                            # COMPUTE
                            # ------------------------------------------

                            "shape":
                                shape,

                            "ocpu":
                                ocpus,

                            "ocpus":
                                ocpus,

                            "memory_gb":
                                memory_in_gbs,

                            "memory_in_gbs":
                                memory_in_gbs,

                            "vcpus":
                                vcpus,

                            "vcpu":
                                vcpus,

                            "baseline_ocpu_utilization":
                                baseline_ocpu_utilization,

                            "processor_description":
                                processor_description,

                            # ------------------------------------------
                            # NETWORK
                            # ------------------------------------------

                            "vnic_id":
                                vnic_id,

                            "vnic_ocid":
                                vnic_id,

                            "private_ip":
                                private_ip,

                            "public_ip":
                                public_ip,

                            "ipv6_address":
                                ipv6_address,

                            "mac_address":
                                mac_address,

                            "subnet_id":
                                subnet_id,

                            "subnet_ocid":
                                subnet_id,

                            "hostname":
                                hostname,

                            "hostname_label":
                                hostname_label,

                            "private_dns_name":
                                private_dns_name,

                            "vlan_tag":
                                vlan_tag,

                            "nic_index":
                                nic_index,

                            # ------------------------------------------
                            # IMAGE
                            # ------------------------------------------

                            "image_id":
                                image_id,

                            "image_ocid":
                                image_id,

                            # ------------------------------------------
                            # PLACEMENT
                            # ------------------------------------------

                            "availability_domain":
                                availability_domain,

                            "fault_domain":
                                fault_domain,

                            # ------------------------------------------
                            # STORAGE
                            # ------------------------------------------

                            "boot_volume_id":
                                boot_volume_id,

                            "boot_volume_ocid":
                                boot_volume_id,

                            # ------------------------------------------
                            # LAUNCH
                            # ------------------------------------------

                            "launch_mode":
                                launch_mode,

                            # ------------------------------------------
                            # TAGS
                            # ------------------------------------------

                            "freeform_tags":
                                _safe_value(
                                    freeform_tags
                                ),

                            "defined_tags":
                                _safe_value(
                                    defined_tags
                                ),
                        },
                    )

                    resources.append(
                        resource
                    )

                except Exception as exc:

                    print(
                        f"    ERROR processing Compute "
                        f"instance "
                        f"{_get(instance, 'display_name', '')}: "
                        f"{exc}"
                    )

    return resources
