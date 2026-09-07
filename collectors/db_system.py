import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def _get(obj, name, default=""):
    """
    Safely get an attribute from an OCI SDK object.
    """
    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(name, default)

    return getattr(obj, name, default)


def _to_dict(obj):
    """
    Safely convert OCI SDK model to dictionary.
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


def collect_db_systems(config):
    """
    Collect all OCI DB Systems across:

        - All subscribed regions
        - All accessible compartments

    Detailed information collected:

        Basic:
        - Name
        - OCID
        - Region
        - Compartment
        - Lifecycle State
        - Creation Time

        Compute:
        - Shape
        - OCPU / CPU Core Count
        - VCPU
        - Memory
        - Shape Configuration
        - Node Count

        Storage:
        - Data Storage Size
        - Recovery Storage
        - Storage Management
        - Disk Redundancy

        Database:
        - Database Edition
        - Database Version
        - DB Home OCID
        - DB Name
        - Database Count

        Network:
        - Subnet
        - Backup Subnet
        - Hostname
        - Listener Port
        - VCN where available

        Availability:
        - Availability Domain
        - Fault Domain

        Security:
        - License Model
        - KMS Key

        Tags:
        - Defined Tags
        - Freeform Tags
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing DB System region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        try:

            database_client = oci.database.DatabaseClient(
                region_config
            )

        except Exception as error:

            print(
                f"    ERROR creating Database client "
                f"for region {region}: {error}"
            )

            continue

        for compartment in compartments:

            compartment_id = compartment["id"]
            compartment_name = compartment["name"]

            try:

                db_systems = (
                    oci.pagination.list_call_get_all_results(
                        database_client.list_db_systems,
                        compartment_id=compartment_id,
                    )
                )

            except Exception as error:

                print(
                    f"    ERROR collecting DB Systems "
                    f"from compartment "
                    f"{compartment_name}: {error}"
                )

                continue

            for db_system in db_systems.data:

                try:

                    # =====================================================
                    # BASIC INFORMATION
                    # =====================================================

                    db_system_id = _get(
                        db_system,
                        "id",
                        "",
                    )

                    display_name = _get(
                        db_system,
                        "display_name",
                        "",
                    )

                    lifecycle_state = _get(
                        db_system,
                        "lifecycle_state",
                        "",
                    )

                    lifecycle_details = _get(
                        db_system,
                        "lifecycle_details",
                        "",
                    )

                    time_created = _get(
                        db_system,
                        "time_created",
                        None,
                    )

                    # =====================================================
                    # AVAILABILITY
                    # =====================================================

                    availability_domain = _get(
                        db_system,
                        "availability_domain",
                        "",
                    )

                    fault_domain = _get(
                        db_system,
                        "fault_domain",
                        "",
                    )

                    # =====================================================
                    # COMPUTE / SHAPE
                    # =====================================================

                    shape = _get(
                        db_system,
                        "shape",
                        "",
                    )

                    cpu_core_count = _get(
                        db_system,
                        "cpu_core_count",
                        None,
                    )

                    shape_config = _get(
                        db_system,
                        "shape_config",
                        None,
                    )

                    shape_config_dict = _to_dict(
                        shape_config
                    )

                    # OCPU

                    ocpus = _get(
                        shape_config,
                        "ocpus",
                        None,
                    )

                    if ocpus is None:
                        ocpus = shape_config_dict.get(
                            "ocpus",
                            None,
                        )

                    # VCPU

                    vcpus = _get(
                        shape_config,
                        "vcpus",
                        None,
                    )

                    if vcpus is None:
                        vcpus = shape_config_dict.get(
                            "vcpus",
                            None,
                        )

                    # Memory

                    memory_in_gbs = _get(
                        shape_config,
                        "memory_in_gbs",
                        None,
                    )

                    if memory_in_gbs is None:
                        memory_in_gbs = shape_config_dict.get(
                            "memory_in_gbs",
                            None,
                        )

                    # Baseline CPU

                    baseline_ocpu_utilization = _get(
                        shape_config,
                        "baseline_ocpu_utilization",
                        None,
                    )

                    if baseline_ocpu_utilization is None:
                        baseline_ocpu_utilization = (
                            shape_config_dict.get(
                                "baseline_ocpu_utilization",
                                None,
                            )
                        )

                    # Processor

                    processor_description = _get(
                        shape_config,
                        "processor_description",
                        "",
                    )

                    if not processor_description:
                        processor_description = (
                            shape_config_dict.get(
                                "processor_description",
                                "",
                            )
                        )

                    # =====================================================
                    # NODE COUNT
                    # =====================================================

                    node_count = _get(
                        db_system,
                        "node_count",
                        None,
                    )

                    if node_count is None:
                        node_count = _get(
                            db_system,
                            "cluster_size",
                            None,
                        )

                    # =====================================================
                    # STORAGE
                    # =====================================================

                    data_storage_size_in_gbs = _get(
                        db_system,
                        "data_storage_size_in_gbs",
                        None,
                    )

                    recovery_storage_size_in_gbs = _get(
                        db_system,
                        "recovery_storage_size_in_gbs",
                        None,
                    )

                    storage_management = _get(
                        db_system,
                        "storage_management",
                        "",
                    )

                    disk_redundancy = _get(
                        db_system,
                        "disk_redundancy",
                        "",
                    )

                    sparse_diskgroup = _get(
                        db_system,
                        "sparse_diskgroup",
                        None,
                    )

                    # =====================================================
                    # DATABASE INFORMATION
                    # =====================================================

                    database_edition = _get(
                        db_system,
                        "database_edition",
                        "",
                    )

                    version = _get(
                        db_system,
                        "version",
                        "",
                    )

                    db_home_id = _get(
                        db_system,
                        "db_home_id",
                        "",
                    )

                    db_home_ocid = db_home_id

                    db_name = _get(
                        db_system,
                        "db_name",
                        "",
                    )

                    database_count = _get(
                        db_system,
                        "database_count",
                        None,
                    )

                    # =====================================================
                    # NETWORK
                    # =====================================================

                    subnet_id = _get(
                        db_system,
                        "subnet_id",
                        "",
                    )

                    backup_subnet_id = _get(
                        db_system,
                        "backup_subnet_id",
                        "",
                    )

                    vcn_id = _get(
                        db_system,
                        "vcn_id",
                        "",
                    )

                    hostname = _get(
                        db_system,
                        "hostname",
                        "",
                    )

                    listener_port = _get(
                        db_system,
                        "listener_port",
                        None,
                    )

                    private_ip = _get(
                        db_system,
                        "private_ip",
                        "",
                    )

                    public_ip = _get(
                        db_system,
                        "public_ip",
                        "",
                    )

                    # =====================================================
                    # LICENSE
                    # =====================================================

                    license_model = _get(
                        db_system,
                        "license_model",
                        "",
                    )

                    # =====================================================
                    # SECURITY / ENCRYPTION
                    # =====================================================

                    kms_key_id = _get(
                        db_system,
                        "kms_key_id",
                        "",
                    )

                    kms_key_version_id = _get(
                        db_system,
                        "kms_key_version_id",
                        "",
                    )

                    # =====================================================
                    # CLUSTER / RAC
                    # =====================================================

                    cluster_name = _get(
                        db_system,
                        "cluster_name",
                        "",
                    )

                    cluster_type = _get(
                        db_system,
                        "cluster_type",
                        "",
                    )

                    db_system_options = _get(
                        db_system,
                        "db_system_options",
                        None,
                    )

                    db_system_options_dict = _to_dict(
                        db_system_options
                    )

                    # =====================================================
                    # BACKUP
                    # =====================================================

                    backup_network_nsg_ids = _get(
                        db_system,
                        "backup_network_security_group_ids",
                        [],
                    )

                    network_security_group_ids = _get(
                        db_system,
                        "network_security_group_ids",
                        [],
                    )

                    # =====================================================
                    # TAGS
                    # =====================================================

                    defined_tags = _get(
                        db_system,
                        "defined_tags",
                        {},
                    )

                    freeform_tags = _get(
                        db_system,
                        "freeform_tags",
                        {},
                    )

                    # =====================================================
                    # RESOURCE DETAILS
                    # =====================================================

                    details = {

                        # -------------------------------------------------
                        # LOCATION
                        # -------------------------------------------------

                        "availability_domain":
                            availability_domain,

                        "fault_domain":
                            fault_domain,

                        # -------------------------------------------------
                        # COMPUTE
                        # -------------------------------------------------

                        "shape":
                            shape,

                        "ocpus":
                            ocpus,

                        "ocpu":
                            ocpus,

                        "cpu_core_count":
                            cpu_core_count,

                        "cpu_cores":
                            cpu_core_count,

                        "vcpus":
                            vcpus,

                        "memory_in_gbs":
                            memory_in_gbs,

                        "memory_gb":
                            memory_in_gbs,

                        "baseline_ocpu_utilization":
                            baseline_ocpu_utilization,

                        "processor_description":
                            processor_description,

                        "shape_config":
                            shape_config_dict,

                        "node_count":
                            node_count,

                        "cluster_size":
                            node_count,

                        # -------------------------------------------------
                        # STORAGE
                        # -------------------------------------------------

                        "data_storage_size_in_gbs":
                            data_storage_size_in_gbs,

                        "data_storage_size_gb":
                            data_storage_size_in_gbs,

                        "storage_size_gb":
                            data_storage_size_in_gbs,

                        "recovery_storage_size_in_gbs":
                            recovery_storage_size_in_gbs,

                        "recovery_storage_gb":
                            recovery_storage_size_in_gbs,

                        "storage_management":
                            storage_management,

                        "disk_redundancy":
                            disk_redundancy,

                        "sparse_diskgroup":
                            sparse_diskgroup,

                        # -------------------------------------------------
                        # DATABASE
                        # -------------------------------------------------

                        "database_edition":
                            database_edition,

                        "version":
                            version,

                        "db_version":
                            version,

                        "db_home_id":
                            db_home_id,

                        "db_home_ocid":
                            db_home_ocid,

                        "db_name":
                            db_name,

                        "database_count":
                            database_count,

                        # -------------------------------------------------
                        # NETWORK
                        # -------------------------------------------------

                        "subnet_id":
                            subnet_id,

                        "subnet_ocid":
                            subnet_id,

                        "backup_subnet_id":
                            backup_subnet_id,

                        "backup_subnet_ocid":
                            backup_subnet_id,

                        "vcn_id":
                            vcn_id,

                        "vcn_ocid":
                            vcn_id,

                        "hostname":
                            hostname,

                        "listener_port":
                            listener_port,

                        "private_ip":
                            private_ip,

                        "public_ip":
                            public_ip,

                        "network_security_group_ids":
                            network_security_group_ids,

                        "backup_network_security_group_ids":
                            backup_network_nsg_ids,

                        # -------------------------------------------------
                        # LICENSE
                        # -------------------------------------------------

                        "license_model":
                            license_model,

                        # -------------------------------------------------
                        # ENCRYPTION
                        # -------------------------------------------------

                        "kms_key_id":
                            kms_key_id,

                        "kms_key_ocid":
                            kms_key_id,

                        "kms_key_version_id":
                            kms_key_version_id,

                        # -------------------------------------------------
                        # CLUSTER
                        # -------------------------------------------------

                        "cluster_name":
                            cluster_name,

                        "cluster_type":
                            cluster_type,

                        "db_system_options":
                            db_system_options_dict,

                        # -------------------------------------------------
                        # TAGS
                        # -------------------------------------------------

                        "defined_tags":
                            defined_tags,

                        "freeform_tags":
                            freeform_tags,
                    }

                    # =====================================================
                    # RESOURCE OBJECT
                    # =====================================================

                    resource = Resource(

                        service="DB Systems",

                        resource_type="DB System",

                        name=display_name,

                        ocid=db_system_id,

                        compartment_id=compartment_id,

                        compartment_name=compartment_name,

                        region=region,

                        state=lifecycle_state,

                        time_created=time_created,

                        defined_tags=defined_tags,

                        details=details,
                    )

                    resources.append(
                        resource
                    )

                except Exception as error:

                    print(
                        f"    ERROR processing DB System "
                        f"{display_name}: {error}"
                    )

    print(
        f"DB Systems: {len(resources)} resources found"
    )

    return resources
