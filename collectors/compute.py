import oci


def _get(obj, name, default=None):
    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(name, default)

    return getattr(obj, name, default)


def _safe_dict(obj):
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


def _get_shape_details(compute_client, shape_name):
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
    if not vnic_id:
        return None

    try:
        response = virtual_network_client.get_vnic(vnic_id)

        return response.data

    except Exception:
        return None


def collect_compute(config):
    """
    Collect OCI Compute instances with detailed information.

    Returned fields include:

    - Shape
    - OCPU
    - Memory
    - VCPU
    - Private IP
    - Public IP
    - IPv6
    - VNIC OCID
    - MAC Address
    - Subnet
    - Hostname
    - Image OCID
    - Availability Domain
    - Fault Domain
    - Boot Volume OCID
    """

    resources = []

    tenancy_id = config.get("tenancy_id")

    regions = config.get(
        "regions",
        [],
    )

    compartments = config.get(
        "compartments",
        [],
    )

    for region in regions:

        print(
            f"  Processing Compute region: {region}"
        )

        try:

            compute_client = oci.core.ComputeClient(
                config,
            )

            compute_client.base_client.set_region(
                region
            )

            virtual_network_client = (
                oci.core.VirtualNetworkClient(
                    config
                )
            )

            virtual_network_client.base_client.set_region(
                region
            )

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

                for instance in instances:

                    try:

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

                        # If shape_config did not contain
                        # complete information, query shape.
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

                        resource = {

                            "service": "Compute",

                            "resource_type": "Instance",

                            "name": _get(
                                instance,
                                "display_name",
                                "",
                            ),

                            "display_name": _get(
                                instance,
                                "display_name",
                                "",
                            ),

                            "ocid": _get(
                                instance,
                                "id",
                                "",
                            ),

                            "id": _get(
                                instance,
                                "id",
                                "",
                            ),

                            "region": region,

                            "compartment_id":
                                compartment_id,

                            "compartment_name":
                                compartment_name,

                            "state": _get(
                                instance,
                                "lifecycle_state",
                                "",
                            ),

                            "lifecycle_state": _get(
                                instance,
                                "lifecycle_state",
                                "",
                            ),

                            "lifecycle_details": _get(
                                instance,
                                "lifecycle_details",
                                "",
                            ),

                            "time_created": _get(
                                instance,
                                "time_created",
                                None,
                            ),

                            "defined_tags": _get(
                                instance,
                                "defined_tags",
                                {},
                            ),

                            "freeform_tags": _get(
                                instance,
                                "freeform_tags",
                                {},
                            ),

                            # -------------------------
                            # COMPUTE DETAILS
                            # -------------------------

                            "shape": shape,

                            "ocpu": ocpus,

                            "ocpus": ocpus,

                            "memory_gb":
                                memory_in_gbs,

                            "memory_in_gbs":
                                memory_in_gbs,

                            "vcpus": vcpus,

                            "vcpu": vcpus,

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

                            "image_id": _get(
                                instance,
                                "image_id",
                                "",
                            ),

                            "image_ocid": _get(
                                instance,
                                "image_id",
                                "",
                            ),

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

                            "boot_volume_id":
                                _get(
                                    instance,
                                    "boot_volume_id",
                                    "",
                                ),

                            "boot_volume_ocid":
                                _get(
                                    instance,
                                    "boot_volume_id",
                                    "",
                                ),

                            "launch_mode":
                                _get(
                                    instance,
                                    "launch_mode",
                                    "",
                                ),

                            "baseline_ocpu_utilization":
                                baseline_ocpu_utilization,

                            "processor_description":
                                processor_description,

                            "private_dns_name":
                                private_dns_name,

                            "vlan_tag":
                                vlan_tag,

                            "nic_index":
                                nic_index,
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
