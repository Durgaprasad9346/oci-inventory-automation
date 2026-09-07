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


def collect_nosql(config):
    """
    Collect all OCI NoSQL tables across:

        - All subscribed regions
        - All accessible compartments

    Detailed inventory:

        Basic:
        - Table Name
        - Table OCID
        - Region
        - Compartment
        - Lifecycle State
        - Creation Time

        Capacity:
        - Maximum Read Units
        - Maximum Write Units
        - Maximum Storage in GB
        - Current Read Units
        - Current Write Units
        - Current Storage in GB

        Configuration:
        - Table Limits
        - Table Type
        - Schema
        - DDL Statement
        - Freeform Tags
        - Defined Tags
    """

    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:

        print(
            f"  Processing NoSQL region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        try:

            nosql_client = oci.nosql.NosqlClient(
                region_config
            )

        except Exception as error:

            print(
                f"    ERROR creating NoSQL client "
                f"for region {region}: {error}"
            )

            continue

        for compartment in compartments:

            compartment_id = compartment["id"]
            compartment_name = compartment["name"]

            try:

                tables = (
                    oci.pagination.list_call_get_all_results(
                        nosql_client.list_tables,
                        compartment_id=compartment_id,
                    )
                )

            except Exception as error:

                print(
                    f"    ERROR collecting NoSQL "
                    f"from compartment "
                    f"{compartment_name}: {error}"
                )

                continue

            for table in tables.data:

                try:

                    # =================================================
                    # BASIC INFORMATION
                    # =================================================

                    table_id = _get(
                        table,
                        "id",
                        "",
                    )

                    table_name = _get(
                        table,
                        "name",
                        "",
                    )

                    lifecycle_state = _get(
                        table,
                        "lifecycle_state",
                        "",
                    )

                    lifecycle_details = _get(
                        table,
                        "lifecycle_details",
                        "",
                    )

                    time_created = _get(
                        table,
                        "time_created",
                        None,
                    )

                    table_type = _get(
                        table,
                        "table_type",
                        "",
                    )

                    # =================================================
                    # TABLE LIMITS
                    # =================================================

                    table_limits = _get(
                        table,
                        "table_limits",
                        None,
                    )

                    table_limits_dict = _to_dict(
                        table_limits
                    )

                    # Read capacity

                    max_read_units = _get(
                        table_limits,
                        "max_read_units",
                        None,
                    )

                    if max_read_units is None:
                        max_read_units = table_limits_dict.get(
                            "max_read_units",
                            None,
                        )

                    # Write capacity

                    max_write_units = _get(
                        table_limits,
                        "max_write_units",
                        None,
                    )

                    if max_write_units is None:
                        max_write_units = table_limits_dict.get(
                            "max_write_units",
                            None,
                        )

                    # Storage

                    max_storage_gb = _get(
                        table_limits,
                        "max_storage_in_gbs",
                        None,
                    )

                    if max_storage_gb is None:
                        max_storage_gb = table_limits_dict.get(
                            "max_storage_in_gbs",
                            None,
                        )

                    # =================================================
                    # CURRENT CAPACITY
                    # =================================================

                    read_units = _get(
                        table,
                        "read_units",
                        None,
                    )

                    write_units = _get(
                        table,
                        "write_units",
                        None,
                    )

                    storage_size_in_gbs = _get(
                        table,
                        "storage_size_in_gbs",
                        None,
                    )

                    # =================================================
                    # SCHEMA / DDL
                    # =================================================

                    ddl_statement = _get(
                        table,
                        "ddl_statement",
                        "",
                    )

                    schema = _get(
                        table,
                        "schema",
                        None,
                    )

                    schema_dict = _to_dict(
                        schema
                    )

                    # =================================================
                    # AUTO RECLAIM
                    # =================================================

                    is_auto_reclaimable = _get(
                        table,
                        "is_auto_reclaimable",
                        None,
                    )

                    # =================================================
                    # COMPARTMENT
                    # =================================================

                    resource_compartment_id = _get(
                        table,
                        "compartment_id",
                        compartment_id,
                    )

                    # =================================================
                    # TAGS
                    # =================================================

                    defined_tags = _get(
                        table,
                        "defined_tags",
                        {},
                    )

                    freeform_tags = _get(
                        table,
                        "freeform_tags",
                        {},
                    )

                    # =================================================
                    # DETAILS
                    # =================================================

                    details = {

                        # ---------------------------------------------
                        # TABLE
                        # ---------------------------------------------

                        "table_name":
                            table_name,

                        "table_type":
                            table_type,

                        "lifecycle_state":
                            lifecycle_state,

                        "lifecycle_details":
                            lifecycle_details,

                        # ---------------------------------------------
                        # CAPACITY
                        # ---------------------------------------------

                        "max_read_units":
                            max_read_units,

                        "max_write_units":
                            max_write_units,

                        "max_storage_in_gbs":
                            max_storage_gb,

                        "max_storage_gb":
                            max_storage_gb,

                        "read_units":
                            read_units,

                        "write_units":
                            write_units,

                        "storage_size_in_gbs":
                            storage_size_in_gbs,

                        "storage_size_gb":
                            storage_size_in_gbs,

                        # ---------------------------------------------
                        # TABLE LIMITS
                        # ---------------------------------------------

                        "table_limits":
                            table_limits_dict,

                        # ---------------------------------------------
                        # SCHEMA
                        # ---------------------------------------------

                        "schema":
                            schema_dict,

                        "ddl_statement":
                            ddl_statement,

                        # ---------------------------------------------
                        # AUTO RECLAIM
                        # ---------------------------------------------

                        "is_auto_reclaimable":
                            is_auto_reclaimable,

                        # ---------------------------------------------
                        # COMPARTMENT
                        # ---------------------------------------------

                        "compartment_id":
                            resource_compartment_id,

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

                        service="NoSQL Database",

                        resource_type="NoSQL Table",

                        name=table_name,

                        ocid=table_id,

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
                        f"    ERROR processing NoSQL Table "
                        f"{table_name}: {error}"
                    )

    print(
        f"NoSQL Tables: {len(resources)} resources found"
    )

    return resources
