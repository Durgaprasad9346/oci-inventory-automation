import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def _get(obj, name, default=""):
    """
    Safely get a value from an OCI SDK object.
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

    try:
        if hasattr(obj, "__dict__"):
            return obj.__dict__
    except Exception:
        pass

    return {}


def collect_postgresql(config):
    """
    Collect OCI Database with PostgreSQL DB Systems.

    Collects:

        BASIC
        - Name
        - OCID
        - Compartment
        - Region
        - Lifecycle State
        - Lifecycle Details
        - Creation Date

        COMPUTE
        - Shape
        - OCPU
        - Memory
        - Storage

        DATABASE
        - PostgreSQL Version
        - System Role
        - Configuration ID

        NETWORK
        - Subnet
        - NSGs
        - Private IP
        - Endpoint

        BACKUP / HA
        - Backup Policy
        - HA
        - Read Only

        TAGS
        - Defined Tags
        - Freeform Tags
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing PostgreSQL region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        # =============================================================
        # CREATE POSTGRESQL CLIENT
        # =============================================================

        try:

            postgresql_client = oci.psql.PostgresqlClient(
                region_config
            )

        except Exception as error:

            print(
                f"    ERROR creating PostgreSQL client "
                f"for region {region}: {error}"
            )

            continue

        # =============================================================
        # COMPARTMENTS
        # =============================================================

        for compartment in compartments:

            compartment_id = compartment["id"]
            compartment_name = compartment["name"]

            try:

                # =====================================================
                # LIST DB SYSTEMS
                # =====================================================

                response = (
                    oci.pagination.list_call_get_all_results(
                        postgresql_client.list_db_systems,
                        compartment_id=compartment_id,
                    )
                )

                db_systems = response.data

            except Exception as error:

                print(
                    f"    ERROR collecting PostgreSQL "
                    f"from compartment "
                    f"{compartment_name}: {error}"
                )

                continue

            # =========================================================
            # PROCESS DB SYSTEMS
            # =========================================================

            for db_system in db_systems:

                try:

                    # =================================================
                    # BASIC
                    # =================================================

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

                    description = _get(
                        db_system,
                        "description",
                        "",
                    )

                    time_created = _get(
                        db_system,
                        "time_created",
                        None,
                    )

                    time_of_deletion = _get(
                        db_system,
                        "time_of_deletion",
                        None,
                    )

                    # =================================================
                    # DATABASE
                    # =================================================

                    db_version = _get(
                        db_system,
                        "db_version",
                        "",
                    )

                    system_role = _get(
                        db_system,
                        "system_role",
                        "",
                    )

                    configuration_id = _get(
                        db_system,
                        "configuration_id",
                        "",
                    )

                    # =================================================
                    # COMPUTE
                    # =================================================

                    shape = _get(
                        db_system,
                        "shape",
                        "",
                    )

                    instance_ocpu_count = _get(
                        db_system,
                        "instance_ocpu_count",
                        None,
                    )

                    instance_memory_size_in_gbs = _get(
                        db_system,
                        "instance_memory_size_in_gbs",
                        None,
                    )

                    # =================================================
                    # STORAGE
                    # =================================================

                    storage_size_in_gbs = _get(
                        db_system,
                        "storage_size_in_gbs",
                        None,
                    )

                    instance_storage_size_in_gbs = _get(
                        db_system,
                        "instance_storage_size_in_gbs",
                        None,
                    )

                    if (
                        storage_size_in_gbs is None
                        and instance_storage_size_in_gbs is not None
                    ):
                        storage_size_in_gbs = (
                            instance_storage_size_in_gbs
                        )

                    # =================================================
                    # LOCATION
                    # =================================================

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

                    # =================================================
                    # NETWORK
                    # =================================================

                    subnet_id = _get(
                        db_system,
                        "subnet_id",
                        "",
                    )

                    nsg_ids = _get(
                        db_system,
                        "nsg_ids",
                        [],
                    )

                    private_ip = _get(
                        db_system,
                        "private_ip",
                        "",
                    )

                    endpoint = _get(
                        db_system,
                        "endpoint",
                        "",
                    )

                    hostname = _get(
                        db_system,
                        "hostname",
                        "",
                    )

                    # =================================================
                    # BACKUP
                    # =================================================

                    backup_policy = _get(
                        db_system,
                        "backup_policy",
                        None,
                    )

                    backup_policy_dict = _to_dict(
                        backup_policy
                    )

                    # =================================================
                    # HIGH AVAILABILITY
                    # =================================================

                    is_h_a = _get(
                        db_system,
                        "is_h_a",
                        None,
                    )

                    is_read_only = _get(
                        db_system,
                        "is_read_only",
                        None,
                    )

                    # =================================================
                    # TAGS
                    # =================================================

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

                    # =================================================
                    # DETAILS
                    # =================================================

                    details = {

                        # ---------------------------------------------
                        # BASIC
                        # ---------------------------------------------

                        "description":
                            description,

                        "lifecycle_details":
                            lifecycle_details,

                        "time_of_deletion":
                            time_of_deletion,

                        # ---------------------------------------------
                        # DATABASE
                        # ---------------------------------------------

                        "db_version":
                            db_version,

                        "postgresql_version":
                            db_version,

                        "system_role":
                            system_role,

                        "configuration_id":
                            configuration_id,

                        # ---------------------------------------------
                        # COMPUTE
                        # ---------------------------------------------

                        "shape":
                            shape,

                        "instance_ocpu_count":
                            instance_ocpu_count,

                        "ocpu":
                            instance_ocpu_count,

                        "ocpus":
                            instance_ocpu_count,

                        "instance_memory_size_in_gbs":
                            instance_memory_size_in_gbs,

                        "memory_gb":
                            instance_memory_size_in_gbs,

                        "memory_in_gbs":
                            instance_memory_size_in_gbs,

                        # ---------------------------------------------
                        # STORAGE
                        # ---------------------------------------------

                        "storage_size_in_gbs":
                            storage_size_in_gbs,

                        "storage_size_gb":
                            storage_size_in_gbs,

                        "instance_storage_size_in_gbs":
                            instance_storage_size_in_gbs,

                        # ---------------------------------------------
                        # LOCATION
                        # ---------------------------------------------

                        "availability_domain":
                            availability_domain,

                        "fault_domain":
                            fault_domain,

                        # ---------------------------------------------
                        # NETWORK
                        # ---------------------------------------------

                        "subnet_id":
                            subnet_id,

                        "subnet_ocid":
                            subnet_id,

                        "nsg_ids":
                            nsg_ids,

                        "network_security_group_ids":
                            nsg_ids,

                        "private_ip":
                            private_ip,

                        "endpoint":
                            endpoint,

                        "hostname":
                            hostname,

                        # ---------------------------------------------
                        # BACKUP
                        # ---------------------------------------------

                        "backup_policy":
                            backup_policy_dict,

                        # ---------------------------------------------
                        # HA
                        # ---------------------------------------------

                        "is_h_a":
                            is_h_a,

                        "high_availability":
                            is_h_a,

                        "is_read_only":
                            is_read_only,

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

                        service="PostgreSQL",

                        resource_type="PostgreSQL DB System",

                        name=display_name,

                        ocid=db_system_id,

                        compartment_id=compartment_id,

                        compartment_name=compartment_name,

                        region=region,

                        state=lifecycle_state,

                        time_created=time_created,

                        defined_tags=defined_tags,

                        freeform_tags=freeform_tags,

                        details=details,
                    )

                    resources.append(
                        resource
                    )

                except Exception as error:

                    print(
                        f"    ERROR processing PostgreSQL "
                        f"DB System "
                        f"{display_name}: {error}"
                    )

    print(
        f"PostgreSQL DB Systems: "
        f"{len(resources)} resources found"
    )

    return resources
