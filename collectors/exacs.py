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
    Safely convert an OCI SDK model to dictionary.
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


def collect_exacs(config):
    """
    Collect OCI Exadata Cloud Service VM Clusters.

    ExaCS is represented at VM Cluster level.

    Collects:

        Basic:
        - VM Cluster Name
        - VM Cluster OCID
        - Region
        - Compartment
        - Lifecycle State
        - Creation Time

        Compute:
        - Shape
        - CPU Core Count
        - OCPU
        - Memory
        - DB Node Count

        Storage:
        - DB Node Storage
        - GI Storage where available

        Exadata:
        - Cloud Exadata Infrastructure OCID
        - Cloud Exadata Infrastructure Name
        - VM Cluster Type

        Database:
        - GI Version
        - DB Version
        - DB Home

        Network:
        - VCN
        - Subnet
        - Backup Subnet
        - Hostname
        - Listener Port
        - NSGs

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
            f"  Processing ExaCS region: {region}"
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

                vm_clusters = (
                    oci.pagination.list_call_get_all_results(
                        database_client.list_cloud_vm_clusters,
                        compartment_id=compartment_id,
                    )
                )

            except Exception as error:

                print(
                    f"    ERROR collecting ExaCS VM Clusters "
                    f"from compartment "
                    f"{compartment_name}: {error}"
                )

                continue

            for vm_cluster in vm_clusters.data:

                try:

                    # =================================================
                    # BASIC INFORMATION
                    # =================================================

                    vm_cluster_id = _get(
                        vm_cluster,
                        "id",
                        "",
                    )

                    display_name = _get(
                        vm_cluster,
                        "display_name",
                        "",
                    )

                    lifecycle_state = _get(
                        vm_cluster,
                        "lifecycle_state",
                        "",
                    )

                    lifecycle_details = _get(
                        vm_cluster,
                        "lifecycle_details",
                        "",
                    )

                    time_created = _get(
                        vm_cluster,
                        "time_created",
                        None,
                    )

                    # =================================================
                    # AVAILABILITY
                    # =================================================

                    availability_domain = _get(
                        vm_cluster,
                        "availability_domain",
                        "",
                    )

                    fault_domain = _get(
                        vm_cluster,
                        "fault_domain",
                        "",
                    )

                    # =================================================
                    # COMPUTE
                    # =================================================

                    shape = _get(
                        vm_cluster,
                        "shape",
                        "",
                    )

                    cpu_core_count = _get(
                        vm_cluster,
                        "cpu_core_count",
                        None,
                    )

                    memory_size_in_gbs = _get(
                        vm_cluster,
                        "memory_size_in_gbs",
                        None,
                    )

                    db_node_count = _get(
                        vm_cluster,
                        "db_node_count",
                        None,
                    )

                    if db_node_count is None:

                        db_node_count = _get(
                            vm_cluster,
                            "node_count",
                            None,
                        )

                    # =================================================
                    # STORAGE
                    # =================================================

                    db_node_storage_size_in_gbs = _get(
                        vm_cluster,
                        "db_node_storage_size_in_gbs",
                        None,
                    )

                    gi_storage_size_in_gbs = _get(
                        vm_cluster,
                        "gi_storage_size_in_gbs",
                        None,
                    )

                    data_storage_size_in_gbs = _get(
                        vm_cluster,
                        "data_storage_size_in_gbs",
                        None,
                    )

                    # =================================================
                    # EXADATA INFRASTRUCTURE
                    # =================================================

                    cloud_exadata_infrastructure_id = _get(
                        vm_cluster,
                        "cloud_exadata_infrastructure_id",
                        "",
                    )

                    cloud_exadata_infrastructure_name = _get(
                        vm_cluster,
                        "cloud_exadata_infrastructure_name",
                        "",
                    )

                    vm_cluster_type = _get(
                        vm_cluster,
                        "vm_cluster_type",
                        "",
                    )

                    # =================================================
                    # DATABASE / GRID INFRASTRUCTURE
                    # =================================================

                    gi_version = _get(
                        vm_cluster,
                        "gi_version",
                        "",
                    )

                    grid_image_id = _get(
                        vm_cluster,
                        "grid_image_id",
                        "",
                    )

                    db_version = _get(
                        vm_cluster,
                        "db_version",
                        "",
                    )

                    db_home_id = _get(
                        vm_cluster,
                        "db_home_id",
                        "",
                    )

                    database_software_image_id = _get(
                        vm_cluster,
                        "database_software_image_id",
                        "",
                    )

                    # =================================================
                    # NETWORK
                    # =================================================

                    subnet_id = _get(
                        vm_cluster,
                        "subnet_id",
                        "",
                    )

                    backup_subnet_id = _get(
                        vm_cluster,
                        "backup_subnet_id",
                        "",
                    )

                    vcn_id = _get(
                        vm_cluster,
                        "vcn_id",
                        "",
                    )

                    hostname = _get(
                        vm_cluster,
                        "hostname",
                        "",
                    )

                    listener_port = _get(
                        vm_cluster,
                        "listener_port",
                        None,
                    )

                    private_ip = _get(
                        vm_cluster,
                        "private_ip",
                        "",
                    )

                    public_ip = _get(
                        vm_cluster,
                        "public_ip",
                        "",
                    )

                    network_security_group_ids = _get(
                        vm_cluster,
                        "network_security_group_ids",
                        [],
                    )

                    backup_network_security_group_ids = _get(
                        vm_cluster,
                        "backup_network_security_group_ids",
                        [],
                    )

                    # =================================================
                    # LICENSE
                    # =================================================

                    license_model = _get(
                        vm_cluster,
                        "license_model",
                        "",
                    )

                    # =================================================
                    # SECURITY / ENCRYPTION
                    # =================================================

                    kms_key_id = _get(
                        vm_cluster,
                        "kms_key_id",
                        "",
                    )

                    kms_key_version_id = _get(
                        vm_cluster,
                        "kms_key_version_id",
                        "",
                    )

                    # =================================================
                    # CLUSTER
                    # =================================================

                    cluster_name = _get(
                        vm_cluster,
                        "cluster_name",
                        "",
                    )

                    cluster_type = _get(
                        vm_cluster,
                        "cluster_type",
                        "",
                    )

                    # =================================================
                    # TAGS
                    # =================================================

                    defined_tags = _get(
                        vm_cluster,
                        "defined_tags",
                        {},
                    )

                    freeform_tags = _get(
                        vm_cluster,
                        "freeform_tags",
                        {},
                    )

                    # =================================================
                    # DETAILS
                    # =================================================

                    details = {

                        # ---------------------------------------------
                        # LOCATION
                        # ---------------------------------------------

                        "availability_domain":
                            availability_domain,

                        "fault_domain":
                            fault_domain,

                        # ---------------------------------------------
                        # COMPUTE
                        # ---------------------------------------------

                        "shape":
                            shape,

                        "cpu_core_count":
                            cpu_core_count,

                        "cpu_cores":
                            cpu_core_count,

                        "ocpu":
                            cpu_core_count,

                        "ocpus":
                            cpu_core_count,

                        "memory_size_in_gbs":
                            memory_size_in_gbs,

                        "memory_gb":
                            memory_size_in_gbs,

                        "memory_in_gbs":
                            memory_size_in_gbs,

                        "db_node_count":
                            db_node_count,

                        "node_count":
                            db_node_count,

                        # ---------------------------------------------
                        # STORAGE
                        # ---------------------------------------------

                        "db_node_storage_size_in_gbs":
                            db_node_storage_size_in_gbs,

                        "db_node_storage_gb":
                            db_node_storage_size_in_gbs,

                        "data_storage_size_in_gbs":
                            data_storage_size_in_gbs,

                        "data_storage_gb":
                            data_storage_size_in_gbs,

                        "gi_storage_size_in_gbs":
                            gi_storage_size_in_gbs,

                        "gi_storage_gb":
                            gi_storage_size_in_gbs,

                        # ---------------------------------------------
                        # EXADATA
                        # ---------------------------------------------

                        "cloud_exadata_infrastructure_id":
                            cloud_exadata_infrastructure_id,

                        "cloud_exadata_infrastructure_ocid":
                            cloud_exadata_infrastructure_id,

                        "cloud_exadata_infrastructure_name":
                            cloud_exadata_infrastructure_name,

                        "vm_cluster_type":
                            vm_cluster_type,

                        # ---------------------------------------------
                        # DATABASE
                        # ---------------------------------------------

                        "gi_version":
                            gi_version,

                        "grid_infrastructure_version":
                            gi_version,

                        "grid_image_id":
                            grid_image_id,

                        "db_version":
                            db_version,

                        "database_version":
                            db_version,

                        "db_home_id":
                            db_home_id,

                        "db_home_ocid":
                            db_home_id,

                        "database_software_image_id":
                            database_software_image_id,

                        # ---------------------------------------------
                        # NETWORK
                        # ---------------------------------------------

                        "vcn_id":
                            vcn_id,

                        "vcn_ocid":
                            vcn_id,

                        "subnet_id":
                            subnet_id,

                        "subnet_ocid":
                            subnet_id,

                        "backup_subnet_id":
                            backup_subnet_id,

                        "backup_subnet_ocid":
                            backup_subnet_id,

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
                            backup_network_security_group_ids,

                        # ---------------------------------------------
                        # LICENSE
                        # ---------------------------------------------

                        "license_model":
                            license_model,

                        # ---------------------------------------------
                        # ENCRYPTION
                        # ---------------------------------------------

                        "kms_key_id":
                            kms_key_id,

                        "kms_key_ocid":
                            kms_key_id,

                        "kms_key_version_id":
                            kms_key_version_id,

                        # ---------------------------------------------
                        # CLUSTER
                        # ---------------------------------------------

                        "cluster_name":
                            cluster_name,

                        "cluster_type":
                            cluster_type,

                        # ---------------------------------------------
                        # TAGS
                        # ---------------------------------------------

                        "defined_tags":
                            defined_tags,

                        "freeform_tags":
                            freeform_tags,
                    }

                    # =================================================
                    # RESOURCE
                    # =================================================

                    resource = Resource(

                        service="ExaCS",

                        resource_type="VM Cluster",

                        name=display_name,

                        ocid=vm_cluster_id,

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
                        f"    ERROR processing ExaCS VM Cluster "
                        f"{display_name}: {error}"
                    )

    print(
        f"ExaCS VM Clusters: "
        f"{len(resources)} resources found"
    )

    return resources
