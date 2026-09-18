import oci

from utils.compartments import get_compartments
from utils.regions import get_regions


def _get(obj, name, default=None):
    if obj is None:
        return default

    try:
        if isinstance(obj, dict):
            return obj.get(name, default)

        return getattr(obj, name, default)

    except Exception:
        return default


def _safe_value(value):
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


def collect_postgresql(config):
    """
    Collect OCI PostgreSQL DB Systems.

    Collects:

      - DB System OCID
      - Display Name
      - Region
      - Compartment
      - Lifecycle State
      - PostgreSQL Version
      - Shape
      - CPU Cores
      - Memory
      - Storage
      - Subnet
      - Private IP
      - Public IP
      - Availability Domain
      - Creation Date
      - KMS Key
      - Tags
    """

    resources = []

    # ============================================================
    # USE COMMON REGION / COMPARTMENT DISCOVERY
    # ============================================================

    regions = get_regions(config)
    compartments = get_compartments(config)

    if not regions:

        print(
            "  ERROR: No regions found for PostgreSQL."
        )

        return resources

    if not compartments:

        print(
            "  ERROR: No compartments found for PostgreSQL."
        )

        return resources

    # ============================================================
    # REGIONS
    # ============================================================

    for region in regions:

        print(
            f"  Processing PostgreSQL region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        # ========================================================
        # POSTGRESQL CLIENT
        # ========================================================

        try:

            client = oci.psql.PostgresqlClient(
                region_config
            )

        except Exception as error:

            print(
                f"  ERROR initializing PostgreSQL client "
                f"for region {region}: {error}"
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
                f"    Processing PostgreSQL compartment: "
                f"{compartment_name}"
            )

            # ====================================================
            # LIST DB SYSTEMS
            # ====================================================

            try:

                response = (
                    oci.pagination.list_call_get_all_results(
                        client.list_db_systems,
                        compartment_id=compartment_id,
                    )
                )

                db_systems = response.data

            except Exception as error:

                print(
                    f"      ERROR collecting PostgreSQL "
                    f"DB Systems from compartment "
                    f"{compartment_name}: {error}"
                )

                continue

            if not db_systems:
                continue

            print(
                f"      Found {len(db_systems)} PostgreSQL "
                f"DB System(s)"
            )

            # ====================================================
            # PROCESS DB SYSTEMS
            # ====================================================

            for db_system in db_systems:

                try:

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

                    # =================================================
                    # GET DETAILED DB SYSTEM
                    # =================================================

                    db_system_details = db_system

                    if db_system_id:

                        try:

                            detail_response = (
                                client.get_db_system(
                                    db_system_id
                                )
                            )

                            db_system_details = (
                                detail_response.data
                            )

                        except Exception as detail_error:

                            print(
                                f"        WARNING: Could not get "
                                f"details for PostgreSQL DB System "
                                f"{display_name}: "
                                f"{detail_error}"
                            )

                    # =================================================
                    # BASIC DETAILS
                    # =================================================

                    display_name = _get(
                        db_system_details,
                        "display_name",
                        display_name,
                    )

                    lifecycle_state = _get(
                        db_system_details,
                        "lifecycle_state",
                        lifecycle_state,
                    )

                    # =================================================
                    # POSTGRESQL VERSION
                    # =================================================

                    postgres_version = _get(
                        db_system_details,
                        "postgres_major_version",
                        None,
                    )

                    if postgres_version is None:

                        postgres_version = _get(
                            db_system_details,
                            "postgresql_version",
                            None,
                        )

                    if postgres_version is None:

                        postgres_version = _get(
                            db_system_details,
                            "db_version",
                            None,
                        )

                    if postgres_version is None:

                        postgres_version = _get(
                            db_system_details,
                            "version",
                            "",
                        )

                    # =================================================
                    # SHAPE
                    # =================================================

                    shape = _get(
                        db_system_details,
                        "shape",
                        "",
                    )

                    # =================================================
                    # CPU
                    # =================================================

                    cpu_core_count = _get(
                        db_system_details,
                        "cpu_core_count",
                        None,
                    )

                    if cpu_core_count is None:

                        cpu_core_count = _get(
                            db_system_details,
                            "cpu_cores",
                            None,
                        )

                    # =================================================
                    # MEMORY
                    # =================================================

                    memory_gb = _get(
                        db_system_details,
                        "memory_size_in_gbs",
                        None,
                    )

                    if memory_gb is None:

                        memory_gb = _get(
                            db_system_details,
                            "memory_gb",
                            None,
                        )

                    # =================================================
                    # STORAGE
                    # =================================================

                    storage_gb = _get(
                        db_system_details,
                        "storage_size_in_gbs",
                        None,
                    )

                    if storage_gb is None:

                        storage_gb = _get(
                            db_system_details,
                            "storage_gb",
                            None,
                        )

                    # =================================================
                    # NETWORK
                    # =================================================

                    subnet_id = _get(
                        db_system_details,
                        "subnet_id",
                        "",
                    )

                    private_ip = _get(
                        db_system_details,
                        "private_ip",
                        "",
                    )

                    public_ip = _get(
                        db_system_details,
                        "public_ip",
                        "",
                    )

                    # =================================================
                    # AVAILABILITY DOMAIN
                    # =================================================

                    availability_domain = _get(
                        db_system_details,
                        "availability_domain",
                        "",
                    )

                    # =================================================
                    # KMS
                    # =================================================

                    kms_key_id = _get(
                        db_system_details,
                        "kms_key_id",
                        "",
                    )

                    # =================================================
                    # CREATION DATE
                    # =================================================

                    time_created = _get(
                        db_system_details,
                        "time_created",
                        None,
                    )

                    # =================================================
                    # OTHER USEFUL DETAILS
                    # =================================================

                    description = _get(
                        db_system_details,
                        "description",
                        "",
                    )

                    instance_count = _get(
                        db_system_details,
                        "instance_count",
                        None,
                    )

                    system_type = _get(
                        db_system_details,
                        "system_type",
                        "",
                    )

                    is_highly_available = _get(
                        db_system_details,
                        "is_highly_available",
                        None,
                    )

                    backup_id = _get(
                        db_system_details,
                        "backup_id",
                        "",
                    )

                    # =================================================
                    # TAGS
                    # =================================================

                    defined_tags = _get(
                        db_system_details,
                        "defined_tags",
                        {},
                    ) or {}

                    freeform_tags = _get(
                        db_system_details,
                        "freeform_tags",
                        {},
                    ) or {}

                    # =================================================
                    # RESOURCE
                    # =================================================

                    resource = {

                        "service":
                            "PostgreSQL",

                        "resource_type":
                            "PostgreSQL DB System",

                        "id":
                            db_system_id,

                        "ocid":
                            db_system_id,

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
                            compartment_id,

                        "compartment_name":
                            compartment_name,

                        "availability_domain":
                            availability_domain,

                        # -----------------------------------------
                        # STATE
                        # -----------------------------------------

                        "lifecycle_state":
                            lifecycle_state,

                        "state":
                            lifecycle_state,

                        # -----------------------------------------
                        # DATABASE
                        # -----------------------------------------

                        "postgresql_version":
                            postgres_version,

                        "version":
                            postgres_version,

                        "db_version":
                            postgres_version,

                        # -----------------------------------------
                        # COMPUTE
                        # -----------------------------------------

                        "shape":
                            shape,

                        "cpu_core_count":
                            cpu_core_count,

                        "cpu_cores":
                            cpu_core_count,

                        "memory_gb":
                            memory_gb,

                        "memory_in_gbs":
                            memory_gb,

                        "storage_gb":
                            storage_gb,

                        "storage_size_gb":
                            storage_gb,

                        # -----------------------------------------
                        # NETWORK
                        # -----------------------------------------

                        "subnet_id":
                            subnet_id,

                        "private_ip":
                            private_ip,

                        "public_ip":
                            public_ip,

                        # -----------------------------------------
                        # OTHER
                        # -----------------------------------------

                        "description":
                            description,

                        "instance_count":
                            instance_count,

                        "system_type":
                            system_type,

                        "is_highly_available":
                            is_highly_available,

                        "backup_id":
                            backup_id,

                        # -----------------------------------------
                        # ENCRYPTION
                        # -----------------------------------------

                        "kms_key_id":
                            kms_key_id,

                        "kms_key_ocid":
                            kms_key_id,

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
                        f"      ERROR processing PostgreSQL "
                        f"DB System "
                        f"{_get(db_system, 'display_name', '')}: "
                        f"{error}"
                    )

    # ============================================================
    # SUMMARY
    # ============================================================

    print(
        f"PostgreSQL: {len(resources)} resources found"
    )

    return resources
