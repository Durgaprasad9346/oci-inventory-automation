import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


# ============================================================
# SAFE GET
# ============================================================

def _get(obj, name, default=None):
    """
    Safely get an attribute from an OCI SDK object or dictionary.
    """

    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(name, default)

    try:
        return getattr(obj, name, default)
    except Exception:
        return default


# ============================================================
# SHAPE DETAILS
# ============================================================

def _get_shape_details(compute_client, shape_name):
    """
    Get additional shape information when instance.shape_config
    does not contain complete information.
    """

    if not shape_name:
        return None

    try:
        response = compute_client.get_shape(shape_name)
        return response.data

    except Exception:
        return None


# ============================================================
# GET VNIC ATTACHMENTS
# ============================================================

def _get_vnic_attachments(
    compute_client,
    compartment_id,
    instance_id,
):
    """
    Get VNIC attachments for a Compute instance.

    Returns:
        List of VNIC attachment objects.
    """

    if not instance_id:
        return []

    try:

        response = (
            oci.pagination.list_call_get_all_results(
                compute_client.list_vnic_attachments,
                compartment_id=compartment_id,
                instance_id=instance_id,
            )
        )

        return response.data

    except Exception as exc:

        print(
            f"    WARNING collecting VNIC attachments "
            f"for instance {instance_id}: {exc}"
        )

        return []


# ============================================================
# GET PRIVATE IP DETAILS
# ============================================================

def _get_private_ip_details(
    virtual_network_client,
    vnic_id,
):
    """
    Get Private IP information using VNIC OCID.

    This avoids VirtualNetworkClient.get_vnic().

    Returns:
        Dictionary containing networking details.
    """

    result = {
        "private_ip": "",
        "public_ip": "",
        "ipv6_address": "",
        "subnet_id": "",
        "hostname": "",
        "hostname_label": "",
        "private_dns_name": "",
        "mac_address": "",
        "vlan_tag": "",
        "nic_index": "",
        "vnic_id": vnic_id or "",
    }

    if not vnic_id:
        return result

    try:

        response = (
            oci.pagination.list_call_get_all_results(
                virtual_network_client.list_private_ips,
                vnic_id=vnic_id,
            )
        )

        private_ips = response.data

        if not private_ips:
            return result

        # ----------------------------------------------------
        # Prefer primary private IP
        # ----------------------------------------------------

        primary_ip = None

        for private_ip in private_ips:

            if _get(
                private_ip,
                "is_primary",
                False,
            ):

                primary_ip = private_ip
                break

        if primary_ip is None:
            primary_ip = private_ips[0]

        # ----------------------------------------------------
        # Private IP
        # ----------------------------------------------------

        result["private_ip"] = _get(
            primary_ip,
            "ip_address",
            "",
        )

        # ----------------------------------------------------
        # Public IP
        # ----------------------------------------------------

        public_ip = _get(
            primary_ip,
            "public_ip",
            None,
        )

        if public_ip:

            if isinstance(public_ip, str):

                result["public_ip"] = public_ip

            else:

                result["public_ip"] = _get(
                    public_ip,
                    "ip_address",
                    "",
                )

        # ----------------------------------------------------
        # IPv6
        # ----------------------------------------------------

        ipv6_addresses = _get(
            primary_ip,
            "ipv6_addresses",
            None,
        )

        if ipv6_addresses:

            if isinstance(
                ipv6_addresses,
                list,
            ):

                ipv6_values = []

                for ipv6 in ipv6_addresses:

                    if isinstance(
                        ipv6,
                        str,
                    ):

                        ipv6_values.append(
                            ipv6
                        )

                    else:

                        address = _get(
                            ipv6,
                            "ipv6_address",
                            "",
                        )

                        if address:
                            ipv6_values.append(
                                address
                            )

                result["ipv6_address"] = ", ".join(
                    ipv6_values
                )

        # Some SDK versions may expose a single value.
        if not result["ipv6_address"]:

            ipv6_address = _get(
                primary_ip,
                "ipv6_address",
                "",
            )

            if ipv6_address:
                result["ipv6_address"] = (
                    ipv6_address
                )

        # ----------------------------------------------------
        # Subnet
        # ----------------------------------------------------

        result["subnet_id"] = _get(
            primary_ip,
            "subnet_id",
            "",
        )

        # ----------------------------------------------------
        # Hostname
        # ----------------------------------------------------

        result["hostname_label"] = _get(
            primary_ip,
            "hostname_label",
            "",
        )

        result["hostname"] = result[
            "hostname_label"
        ]

        # ----------------------------------------------------
        # Private DNS
        # ----------------------------------------------------

        result["private_dns_name"] = _get(
            primary_ip,
            "hostname_label",
            "",
        )

        # ----------------------------------------------------
        # VLAN
        # ----------------------------------------------------

        result["vlan_tag"] = _get(
            primary_ip,
            "vlan_tag",
            "",
        )

        return result

    except Exception as exc:

        print(
            f"    WARNING collecting Private IP "
            f"details for VNIC {vnic_id}: {exc}"
        )

        return result


# ============================================================
# COLLECT COMPUTE
# ============================================================

def collect_compute(config):
    """
    Collect OCI Compute Instances across:

        - All subscribed regions
        - All accessible compartments

    Details collected:

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
        Subnet OCID
        Hostname
        Private DNS Name
        VLAN Tag

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
        Defined Tags
        Freeform Tags
    """

    resources = []

    compartments = get_compartments(
        config
    )

    regions = get_regions(
        config
    )

    # ========================================================
    # REGIONS
    # ========================================================

    for region in regions:

        print(
            f"  Processing Compute region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        try:

            # ------------------------------------------------
            # Compute Client
            # ------------------------------------------------

            compute_client = (
                oci.core.ComputeClient(
                    region_config
                )
            )

            # ------------------------------------------------
            # Virtual Network Client
            # ------------------------------------------------

            virtual_network_client = (
                oci.core.VirtualNetworkClient(
                    region_config
                )
            )

            # =================================================
            # COMPARTMENTS
            # =================================================

            for compartment in compartments:

                compartment_id = _get(
                    compartment,
                    "id",
                    compartment
                    if isinstance(
                        compartment,
                        str,
                    )
                    else None,
                )

                compartment_name = _get(
                    compartment,
                    "name",
                    "",
                )

                if not compartment_id:
                    continue

                # =================================================
                # LIST COMPUTE INSTANCES
                # =================================================

                try:

                    instances = (
                        oci.pagination.list_call_get_all_results(
                            compute_client.list_instances,
                            compartment_id=compartment_id,
                        ).data
                    )

                except Exception as exc:

                    print(
                        f"    ERROR collecting Compute "
                        f"from compartment "
                        f"{compartment_name}: {exc}"
                    )

                    continue

                # =================================================
                # PROCESS INSTANCES
                # =================================================

                for instance in instances:

                    display_name = _get(
                        instance,
                        "display_name",
                        "",
                    )

                    try:

                        # =================================================
                        # BASIC
                        # =================================================

                        instance_id = _get(
                            instance,
                            "id",
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

                        # =================================================
                        # SHAPE
                        # =================================================

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

                        # =================================================
                        # SHAPE API FALLBACK
                        # =================================================

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

                        # =================================================
                        # NETWORKING
                        #
                        # NO get_vnic()
                        # NO list_boot_volume_attachments()
                        # =================================================

                        private_ip = ""
                        public_ip = ""
                        ipv6_address = ""
                        vnic_id = ""
                        mac_address = ""
                        subnet_id = ""
                        hostname = ""
                        hostname_label = ""
                        private_dns_name = ""
                        vlan_tag = ""
                        nic_index = ""

                        # -------------------------------------------------
                        # Get VNIC attachments for THIS instance
                        # -------------------------------------------------

                        vnic_attachments = (
                            _get_vnic_attachments(
                                compute_client,
                                compartment_id,
                                instance_id,
                            )
                        )

                        # -------------------------------------------------
                        # Prefer primary VNIC
                        # -------------------------------------------------

                        selected_attachment = None

                        for attachment in (
                            vnic_attachments
                        ):

                            is_primary = _get(
                                attachment,
                                "is_primary",
                                False,
                            )

                            if is_primary:

                                selected_attachment = (
                                    attachment
                                )

                                break

                        if (
                            selected_attachment
                            is None
                            and vnic_attachments
                        ):

                            selected_attachment = (
                                vnic_attachments[0]
                            )

                        # -------------------------------------------------
                        # Get VNIC OCID
                        # -------------------------------------------------

                        if selected_attachment:

                            vnic_id = _get(
                                selected_attachment,
                                "vnic_id",
                                "",
                            )

                            nic_index = _get(
                                selected_attachment,
                                "nic_index",
                                "",
                            )

                        # -------------------------------------------------
                        # Get Private IP information
                        # -------------------------------------------------

                        if vnic_id:

                            network_details = (
                                _get_private_ip_details(
                                    virtual_network_client,
                                    vnic_id,
                                )
                            )

                            private_ip = (
                                network_details[
                                    "private_ip"
                                ]
                            )

                            public_ip = (
                                network_details[
                                    "public_ip"
                                ]
                            )

                            ipv6_address = (
                                network_details[
                                    "ipv6_address"
                                ]
                            )

                            subnet_id = (
                                network_details[
                                    "subnet_id"
                                ]
                            )

                            hostname = (
                                network_details[
                                    "hostname"
                                ]
                            )

                            hostname_label = (
                                network_details[
                                    "hostname_label"
                                ]
                            )

                            private_dns_name = (
                                network_details[
                                    "private_dns_name"
                                ]
                            )

                            vlan_tag = (
                                network_details[
                                    "vlan_tag"
                                ]
                            )

                        # =================================================
                        # BOOT VOLUME
                        # =================================================

                        boot_volume_id = _get(
                            instance,
                            "boot_volume_id",
                            "",
                        )

                        # =================================================
                        # IMAGE
                        # =================================================

                        image_id = _get(
                            instance,
                            "image_id",
                            "",
                        )

                        # =================================================
                        # PLACEMENT
                        # =================================================

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

                        # =================================================
                        # TAGS
                        # =================================================

                        defined_tags = _get(
                            instance,
                            "defined_tags",
                            {},
                        )

                        freeform_tags = _get(
                            instance,
                            "freeform_tags",
                            {},
                        )

                        # =================================================
                        # RESOURCE
                        # =================================================

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

                            defined_tags=defined_tags,

                            details={

                                # =========================================
                                # BASIC
                                # =========================================

                                "display_name":
                                    display_name,

                                "lifecycle_state":
                                    lifecycle_state,

                                "lifecycle_details":
                                    lifecycle_details,

                                # =========================================
                                # COMPUTE
                                # =========================================

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

                                # =========================================
                                # NETWORK
                                # =========================================

                                "private_ip":
                                    private_ip,

                                "public_ip":
                                    public_ip,

                                "ipv6_address":
                                    ipv6_address,

                                "vnic_id":
                                    vnic_id,

                                "vnic_ocid":
                                    vnic_id,

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

                                # =========================================
                                # IMAGE
                                # =========================================

                                "image_id":
                                    image_id,

                                "image_ocid":
                                    image_id,

                                # =========================================
                                # PLACEMENT
                                # =========================================

                                "availability_domain":
                                    availability_domain,

                                "fault_domain":
                                    fault_domain,

                                # =========================================
                                # STORAGE
                                # =========================================

                                "boot_volume_id":
                                    boot_volume_id,

                                "boot_volume_ocid":
                                    boot_volume_id,

                                # =========================================
                                # OTHER
                                # =========================================

                                "launch_mode":
                                    _get(
                                        instance,
                                        "launch_mode",
                                        "",
                                    ),

                                # =========================================
                                # TAGS
                                #
                                # Workbook will flatten these into
                                # individual columns at the END.
                                # =========================================

                                "defined_tags":
                                    defined_tags,

                                "freeform_tags":
                                    freeform_tags,
                            },
                        )

                        resources.append(
                            resource
                        )

                    except Exception as exc:

                        print(
                            f"    ERROR processing Compute "
                            f"instance {display_name}: {exc}"
                        )

        except Exception as exc:

            print(
                f"  ERROR collecting Compute "
                f"region {region}: {exc}"
            )

    # ========================================================
    # FINAL COUNT
    # ========================================================

    print(
        f"Compute: {len(resources)} resources found"
    )

    return resources
