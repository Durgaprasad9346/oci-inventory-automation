import oci


# ============================================================
# Generic helpers
# ============================================================

def _get(obj, name, default=None):
    """
    Safely get an attribute from an OCI SDK object or dictionary.
    """
    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(name, default)

    return getattr(obj, name, default)


def _safe_dict(obj):
    """
    Convert OCI SDK object to dictionary when possible.
    """
    if obj is None:
        return {}

    if isinstance(obj, dict):
        return obj

    try:
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
    except Exception:
        pass

    return {}


# ============================================================
# Configuration helpers
# ============================================================

def get_regions(config):
    """
    Get configured OCI regions.
    """
    return config.get("regions", [])


def get_compartments(config):
    """
    Get configured compartments.
    """
    return config.get("compartments", [])


# ============================================================
# Shape details
# ============================================================

def _get_shape_details(compute_client, shape_name):
    """
    Get additional shape information if required.
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


# ============================================================
# VNIC details
# ============================================================

def _get_vnic_details(
    virtual_network_client,
    vnic_id,
):
    """
    Get VNIC information.
    """

    if not vnic_id:
        return None

    try:

        response = virtual_network_client.get_vnic(
            vnic_id
        )

        return response.data

    except Exception:

        return None


# ============================================================
# Availability Domains
# ============================================================

def _get_availability_domains(
    config,
    region,
):
    """
    Get Availability Domains for the region.

    OCI requires availability_domain when calling
    list_boot_volume_attachments().
    """

    tenancy_id = config.get("tenancy_id")

    if not tenancy_id:
        print(
            "    WARNING: tenancy_id not found in config"
        )
        return []

    try:

        identity_client = oci.identity.IdentityClient(
            config
        )

        identity_client.base_client.set_region(
            region
        )

        response = (
            oci.pagination.list_call_get_all_results(
                identity_client.list_availability_domains,
                compartment_id=tenancy_id,
            )
        )

        availability_domains = []

        for ad in response.data:

            ad_name = _get(
                ad,
                "name",
                "",
            )

            if ad_name:
                availability_domains.append(
                    ad_name
                )

        return availability_domains

    except Exception as exc:

        print(
            f"    WARNING collecting Availability "
            f"Domains for region {region}: {exc}"
        )

        return []


# ============================================================
# Boot Volume Attachments
# ============================================================

def _get_boot_volume_attachments(
    compute_client,
    compartment_id,
    availability_domains,
):
    """
    Get Boot Volume attachments for a compartment.

    OCI requires availability_domain for
    list_boot_volume_attachments().

    Returns:

        instance_id -> boot_volume_id
    """

    result = {}

    for availability_domain in availability_domains:

        try:

            response = (
                oci.pagination.list_call_get_all_results(
                    compute_client.list_boot_volume_attachments,
                    availability_domain=availability_domain,
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
                f"{compartment_id}, "
                f"AD {availability_domain}: {exc}"
            )

    return result


# ============================================================
# Compute Collector
# ============================================================

def collect_compute(config):
    """
    Collect OCI Compute Instances.

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

    # ========================================================
    # Process every region
    # ========================================================

    for region in regions:

        print(
            f"  Processing Compute region: {region}"
        )

        try:

            # ------------------------------------------------
            # Compute Client
            # ------------------------------------------------

            compute_client = (
                oci.core.ComputeClient(
                    config
                )
            )

            compute_client.base_client.set_region(
                region
            )

            # ------------------------------------------------
            # VCN Client
            # ------------------------------------------------

            virtual_network_client = (
                oci.core.VirtualNetworkClient(
                    config
                )
            )

            virtual_network_client.base_client.set_region(
                region
            )

            # ------------------------------------------------
            # Get Availability Domains
            # ------------------------------------------------

            availability_domains = (
                _get_availability_domains(
                    config,
                    region,
                )
            )

            print(
                f"    Availability Domains found: "
                f"{len(availability_domains)}"
            )

            # =================================================
            # Process Compartments
            # =================================================

            for compartment in compartments:

                compartment_id = _get(
                    compartment,
                    "id",
                    compartment
                    if isinstance(
                        compartment,
                        str
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
                # Get Boot Volume Attachments
                # =================================================

                boot_volume_map = (
                    _get_boot_volume_attachments(
                        compute_client,
                        compartment_id,
                        availability_domains,
                    )
                )

                # =================================================
                # Get Compute Instances
                # =================================================

                try:

                    instances = (
                        oci.pagination
                        .list_call_get_all_results(
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
                # Process Instances
                # =================================================

                for instance in instances:

                    try:

                        # -----------------------------------------
                        # Basic Instance Information
                        # -----------------------------------------

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

                        # -----------------------------------------
                        # Shape
                        # -----------------------------------------

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

                        # -----------------------------------------
                        # Get shape details if necessary
                        # -----------------------------------------

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

                        # -----------------------------------------
                        # Primary VNIC
                        # -----------------------------------------

                        # OCI Compute Instance normally exposes
                        # primary_vnic_id.
                        #
                        # Keep vnic_id as fallback for compatibility.

                        vnic_id = _get(
                            instance,
                            "primary_vnic_id",
                            None,
                        )

                        if not vnic_id:

                            vnic_id = _get(
                                instance,
                                "vnic_id",
                                None,
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

                        # -----------------------------------------
                        # VNIC Details
                        # -----------------------------------------

                        if vnic_id:

                            vnic = (
                                _get_vnic_details(
                                    virtual_network_client,
                                    vnic_id,
                                )
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

                        # -----------------------------------------
                        # Boot Volume
                        # -----------------------------------------

                        boot_volume_id = (
                            boot_volume_map.get(
                                instance_id,
                                ""
                            )
                        )

                        # -----------------------------------------
                        # Resource
                        # -----------------------------------------

                        resource = {

                            # ------------------------------
                            # General
                            # ------------------------------

                            "service":
                                "Compute",

                            "resource_type":
                                "Instance",

                            "name":
                                display_name,

                            "display_name":
                                display_name,

                            "ocid":
                                instance_id,

                            "id":
                                instance_id,

                            "region":
                                region,

                            "compartment_id":
                                compartment_id,

                            "compartment_name":
                                compartment_name,

                            "state":
                                lifecycle_state,

                            "lifecycle_state":
                                lifecycle_state,

                            "lifecycle_details":
                                lifecycle_details,

                            "time_created":
                                time_created,

                            # ------------------------------
                            # Tags
                            # ------------------------------

                            "defined_tags":
                                _get(
                                    instance,
                                    "defined_tags",
                                    {},
                                ),

                            "freeform_tags":
                                _get(
                                    instance,
                                    "freeform_tags",
                                    {},
                                ),

                            # ------------------------------
                            # Compute
                            # ------------------------------

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

                            # ------------------------------
                            # Networking
                            # ------------------------------

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

                            # ------------------------------
                            # Image
                            # ------------------------------

                            "image_id":
                                _get(
                                    instance,
                                    "image_id",
                                    "",
                                ),

                            "image_ocid":
                                _get(
                                    instance,
                                    "image_id",
                                    "",
                                ),

                            # ------------------------------
                            # Placement
                            # ------------------------------

                            "availability_domain":
                                _get(
                                    instance,
                                    "availability_domain",
                                    "",
                                ),

                            "fault_domain":
                                _get(
                                    instance,
                                    "fault_domain",
                                    "",
                                ),

                            # ------------------------------
                            # Storage
                            # ------------------------------

                            "boot_volume_id":
                                boot_volume_id,

                            "boot_volume_ocid":
                                boot_volume_id,

                            # ------------------------------
                            # Other
                            # ------------------------------

                            "launch_mode":
                                _get(
                                    instance,
                                    "launch_mode",
                                    "",
                                ),
                        }

                        resources.append(
                            resource
                        )

                    except Exception as exc:

                        print(
                            f"    ERROR processing "
                            f"Compute instance "
                            f"{_get(instance, 'display_name', '')}: "
                            f"{exc}"
                        )

        except Exception as exc:

            print(
                f"  ERROR collecting Compute "
                f"region {region}: {exc}"
            )

    return resources
