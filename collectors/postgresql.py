import oci


def _get(obj, name, default=None):
    if obj is None:
        return default
    try:
        if isinstance(obj, dict):
            return obj.get(name, default)
        return getattr(obj, name, default)
    except Exception:
        return default


def collect_postgresql(config):
    """
    Collect OCI Database with PostgreSQL resources.

    Uses the OCI PostgreSQL service client and lists DB systems
    by configured region and compartment.

    Collects:
      - DB System OCID
      - Name
      - Region
      - Compartment
      - Lifecycle state
      - Creation date
      - PostgreSQL version
      - Shape
      - CPU cores
      - Memory
      - Storage
      - Subnet
      - Private/Public IP when exposed by the API model
      - Tags
    """

    resources = []

    regions = config.get("regions", [])
    compartments = config.get("compartments", [])

    for region in regions:
        print(f"  Processing PostgreSQL region: {region}")

        try:
            client = oci.psql.PostgresqlClient(
                config,
                region=region,
            )
        except Exception as exc:
            print(
                f"  ERROR initializing PostgreSQL client "
                f"for region {region}: {exc}"
            )
            continue

        for compartment in compartments:
            compartment_id = _get(
                compartment,
                "id",
                compartment if isinstance(compartment, str) else None,
            )

            compartment_name = _get(
                compartment,
                "name",
                "",
            )

            if not compartment_id:
                continue

            try:
                response = oci.pagination.list_call_get_all_results(
                    client.list_db_systems,
                    compartment_id=compartment_id,
                )

                db_systems = response.data

            except Exception as exc:
                print(
                    f"    ERROR collecting PostgreSQL DB Systems "
                    f"from compartment {compartment_name}: {exc}"
                )
                continue

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

                    shape = _get(
                        db_system,
                        "shape",
                        "",
                    )

                    cpu_core_count = _get(
                        db_system,
                        "cpu_core_count",
                        _get(db_system, "cpu_cores", None),
                    )

                    memory_gb = _get(
                        db_system,
                        "memory_size_in_gbs",
                        _get(db_system, "memory_gb", None),
                    )

                    storage_gb = _get(
                        db_system,
                        "storage_size_in_gbs",
                        _get(db_system, "storage_gb", None),
                    )

                    # PostgreSQL API/model naming can vary by SDK release.
                    postgres_version = _get(
                        db_system,
                        "postgres_major_version",
                        _get(
                            db_system,
                            "postgresql_version",
                            _get(
                                db_system,
                                "db_version",
                                _get(db_system, "version", ""),
                            ),
                        ),
                    )

                    subnet_id = _get(
                        db_system,
                        "subnet_id",
                        "",
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

                    availability_domain = _get(
                        db_system,
                        "availability_domain",
                        "",
                    )

                    defined_tags = _get(
                        db_system,
                        "defined_tags",
                        {},
                    ) or {}

                    freeform_tags = _get(
                        db_system,
                        "freeform_tags",
                        {},
                    ) or {}

                    resource = {
                        "service": "PostgreSQL",
                        "resource_type": "PostgreSQL DB System",

                        "id": db_system_id,
                        "ocid": db_system_id,

                        "name": display_name,
                        "display_name": display_name,

                        "region": region,

                        "compartment_id": compartment_id,
                        "compartment_name": compartment_name,

                        "lifecycle_state": lifecycle_state,
                        "state": lifecycle_state,

                        "time_created": _get(
                            db_system,
                            "time_created",
                            None,
                        ),

                        "postgresql_version": postgres_version,
                        "version": postgres_version,
                        "db_version": postgres_version,

                        "shape": shape,

                        "cpu_core_count": cpu_core_count,
                        "cpu_cores": cpu_core_count,

                        "memory_gb": memory_gb,
                        "memory_in_gbs": memory_gb,

                        "storage_gb": storage_gb,
                        "storage_size_gb": storage_gb,

                        "subnet_id": subnet_id,

                        "private_ip": private_ip,
                        "public_ip": public_ip,

                        "availability_domain": availability_domain,

                        "defined_tags": defined_tags,
                        "freeform_tags": freeform_tags,
                    }

                    resources.append(resource)

                except Exception as exc:
                    print(
                        f"    ERROR processing PostgreSQL DB System "
                        f"{_get(db_system, 'display_name', '')}: {exc}"
                    )

    print(
        f"PostgreSQL: {len(resources)} resources found"
    )

    return resources
