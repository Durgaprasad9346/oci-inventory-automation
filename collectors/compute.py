import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def _get(obj, name, default=None):
    """
    Safely get an attribute from an OCI SDK object or dictionary.
    """

    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(name, default)

    return getattr(obj, name, default)


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


def _get_vnic_details(
    virtual_network_client,
    vnic_id,
):
    """
    Get VNIC details using VNIC OCID.
    """

    if not vnic_id:
        return None

    try:
        response = virtual_network_client.get_vnic(vnic_id)
        return response.data

    except Exception:
        return None


def _get_boot_volume_attachments(
    compute_client,
    compartment_id,
    availability_domain,
):
    """
    Get Boot Volume attachments for a compartment and
    availability domain.

    Returns:

        instance_id -> boot_volume_id
    """

    result = {}

    if not availability_domain:
        return result

    try:

        response = (
            oci.pagination.list_call_get_all_results(
                compute_client.list_boot_volume_attachments,
                compartment_id=compartment_id,
                availability_domain=availability_domain,
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

                result[instance_id] = boot_volume_id

    except Exception as exc:

        print(
            f"    WARNING collecting Boot Volume "
            f"attachments from compartment "
            f"{compartment_id}, "
            f"AD {availability_domain}: {exc}"
        )

    return result


def collect_compute(config):
    """
    Collect OCI Compute Instances across:

        - All subscribed regions
        - All accessible compartments
        - All availability domains

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

    compartments = get_compartments(config)
    regions = get_regions(config)

    for region in regions:

        print(
            f"  Processing Compute region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        try:

            compute_client = oci.core.ComputeClient(
                region_config
            )

            virtual_network_client = (
                oci.core.VirtualNetworkClient(
                    region_config
                )
            )

            # -------------------------------------------------
            # Get Availability Domains
            # -------------------------------------------------

            tenancy_id = config.get("tenancy")

            if not tenancy_id:
                print(
                    "    ERROR: tenancy OCID not found in config"
                )
                continue

            identity_client = (
                oci.identity.IdentityClient(
                    region_config
                )
            )

            availability_domains = (
                oci.pagination.list_call_get_all_results(
                    identity_client.list_availability_domains,
                    compartment_id=tenancy_id,
                )
            ).data

            # -------------------------------------------------
            # Process Compartments
            # -------------------------------------------------

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
                    "",
                )

                if not compartment_id:
                    continue

                # -------------------------------------------------
                # Get Boot Volume Attachments for every AD
                # -------------------------------------------------

                boot_volume_attachments = {}

                for availability_domain in availability_domains:

                    ad_name = _get(
                        availability_domain,
                        "name",
                        "",
                    )

                    attachments = (
                        _get_boot_volume_attachments(
                            compute_client,
                            compartment_id,
                            ad_name,
                        )
                    )

                    boot_volume_attachments.update(
                        attachments
                    )

                # -------------------------------------------------
                # Get Compute Instances
                # -------------------------------------------------

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

                # -------------------------------------------------
                # Process Instances
                # -------------------------------------------------

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

                        # -------------------------------------------------
                        # Shape information
                        # -------------------------------------------------

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

                        # -------------------------------------------------
                        # Fallback to Shape API
                        # -------------------------------------------------

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

                        # -------------------------------------------------
                        # VNIC
                        # -------------------------------------------------

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

                        # -------------------------------------------------
                        # Boot Volume
                        # -------------------------------------------------

                        boot_volume_id = _get(
                            instance,
                            "boot_volume_id",
                            "",
                        )

                        if not boot_volume_id:

                            boot_volume_id = (
                                boot_volume_attachments.get(
                                    instance_id,
                                    "",
                                )
                            )

                        # -------------------------------------------------
                        # Resource
                        # -------------------------------------------------

                        resource = Resource(

                            service="Compute",

                            resource_type="Instance",

                            name=display_name,

                            ocid=instance_id,

                            compartment_id=compartment_id,

                            compartment_name=compartment_name,

                            region=region,

                            state=_get(
                                instance,
                                "lifecycle_state",
                                "",
                            ),

                            time_created=_get(
                                instance,
                                "time_created",
                                None,
                            ),

                            defined_tags=_get(
                                instance,
                                "defined_tags",
                                {},
                            ),

                            details={

                                # -----------------------------------------
                                # Basic
                                # -----------------------------------------

                                "display_name":
                                    display_name,

                                "lifecycle_state":
                                    _get(
                                        instance,
                                        "lifecycle_state",
                                        "",
                                    ),

                                "lifecycle_details":
                                    _get(
                                        instance,
                                        "lifecycle_details",
                                        "",
                                    ),

                                # -----------------------------------------
                                # Compute
                                # -----------------------------------------

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

                                # -----------------------------------------
                                # Networking
                                # -----------------------------------------

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

                                # -----------------------------------------
                                # Image
                                # -----------------------------------------

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

                                # -----------------------------------------
                                # Placement
                                # -----------------------------------------

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

                                # -----------------------------------------
                                # Storage
                                # -----------------------------------------

                                "boot_volume_id":
                                    boot_volume_id,

                                "boot_volume_ocid":
                                    boot_volume_id,

                                # -----------------------------------------
                                # Other
                                # -----------------------------------------

                                "launch_mode":
                                    _get(
                                        instance,
                                        "launch_mode",
                                        "",
                                    ),

                                # -----------------------------------------
                                # Tags
                                # -----------------------------------------

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
                            },
                        )

                        resources.append(resource)

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

    print(
        f"Compute: {len(resources)} resources found"
    )

    return resources
