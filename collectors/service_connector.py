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


def _safe_value(value):
    """
    Convert OCI SDK objects into Excel-safe Python values.

    OCI SDK models can contain nested objects/lists.
    This converts them recursively into dictionaries/lists/scalars.
    """

    if value is None:
        return ""

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, dict):
        result = {}

        for key, item in value.items():
            result[str(key)] = _safe_value(item)

        return result

    if isinstance(value, (list, tuple)):
        return [
            _safe_value(item)
            for item in value
        ]

    try:
        if hasattr(value, "to_dict"):
            return _safe_value(
                value.to_dict()
            )
    except Exception:
        pass

    return str(value)


def _get_model_dict(obj):
    """
    Convert an OCI SDK model object into a dictionary.
    """

    if obj is None:
        return {}

    if isinstance(obj, dict):
        return _safe_value(obj)

    try:
        if hasattr(obj, "to_dict"):
            return _safe_value(
                obj.to_dict()
            )
    except Exception:
        pass

    try:
        if hasattr(obj, "__dict__"):
            return _safe_value(
                vars(obj)
            )
    except Exception:
        pass

    return {}


def collect_service_connectors(config):
    """
    Collect OCI Connector Hub Service Connectors across:

        - All subscribed regions
        - All accessible compartments

    Collected information includes:

        Basic:
        - Connector Name
        - Connector OCID
        - Description
        - Compartment
        - Region
        - Lifecycle State
        - Lifecycle Details
        - Time Created
        - Time Updated

        Configuration:
        - Source
        - Target
        - Tasks
        - Connector configuration
        - Connection details where exposed by OCI

        Tags:
        - Defined Tags
        - Freeform Tags
    """

    resources = []

    compartments = get_compartments(config)
    regions = get_regions(config)

    for region in regions:

        print(
            f"  Processing Service Connector region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        # ========================================================
        # CREATE SERVICE CONNECTOR CLIENT
        # ========================================================

        try:

            service_connector_client = (
                oci.sch.ServiceConnectorClient(
                    region_config
                )
            )

        except Exception as error:

            print(
                f"    ERROR creating Service Connector client "
                f"for region {region}: {error}"
            )

            continue

        # ========================================================
        # PROCESS COMPARTMENTS
        # ========================================================

        for compartment in compartments:

            compartment_id = _get(
                compartment,
                "id",
                "",
            )

            compartment_name = _get(
                compartment,
                "name",
                compartment_id,
            )

            if not compartment_id:
                continue

            # ====================================================
            # LIST SERVICE CONNECTORS
            # ====================================================

            try:

                response = (
                    oci.pagination.list_call_get_all_results(
                        service_connector_client.list_service_connectors,
                        compartment_id=compartment_id,
                    )
                )

                connectors = response.data

            except Exception as error:

                print(
                    f"    ERROR collecting Service Connectors "
                    f"from compartment {compartment_name}: {error}"
                )

                continue

            # ====================================================
            # PROCESS EACH CONNECTOR
            # ====================================================

            for connector in connectors:

                connector_id = _get(
                    connector,
                    "id",
                    "",
                )

                display_name = _get(
                    connector,
                    "display_name",
                    "",
                )

                try:

                    # =================================================
                    # BASIC LIST INFORMATION
                    # =================================================

                    lifecycle_state = _get(
                        connector,
                        "lifecycle_state",
                        "",
                    )

                    lifecycle_details = _get(
                        connector,
                        "lifecycle_details",
                        "",
                    )

                    description = _get(
                        connector,
                        "description",
                        "",
                    )

                    time_created = _get(
                        connector,
                        "time_created",
                        None,
                    )

                    time_updated = _get(
                        connector,
                        "time_updated",
                        None,
                    )

                    freeform_tags = _get(
                        connector,
                        "freeform_tags",
                        {},
                    )

                    defined_tags = _get(
                        connector,
                        "defined_tags",
                        {},
                    )

                    # =================================================
                    # GET FULL CONNECTOR DETAILS
                    # =================================================

                    connector_details = connector

                    if connector_id:

                        try:

                            detail_response = (
                                service_connector_client.get_service_connector(
                                    service_connector_id=connector_id
                                )
                            )

                            connector_details = (
                                detail_response.data
                            )

                        except Exception as detail_error:

                            print(
                                f"    WARNING getting details for "
                                f"Service Connector {display_name}: "
                                f"{detail_error}"
                            )

                    # =================================================
                    # CONVERT FULL CONNECTOR TO DICTIONARY
                    # =================================================

                    connector_dict = _get_model_dict(
                        connector_details
                    )

                    # =================================================
                    # SOURCE
                    # =================================================

                    source = _get(
                        connector_details,
                        "source",
                        None,
                    )

                    source_details = _safe_value(
                        source
                    )

                    # =================================================
                    # TARGET
                    # =================================================

                    target = _get(
                        connector_details,
                        "target",
                        None,
                    )

                    target_details = _safe_value(
                        target
                    )

                    # =================================================
                    # TASKS
                    # =================================================

                    tasks = _get(
                        connector_details,
                        "tasks",
                        None,
                    )

                    tasks_details = _safe_value(
                        tasks
                    )

                    task_count = 0

                    if isinstance(tasks, (list, tuple)):
                        task_count = len(tasks)

                    elif tasks:
                        task_count = 1

                    # =================================================
                    # STATE
                    # =================================================

                    state = _get(
                        connector_details,
                        "state",
                        lifecycle_state,
                    )

                    # =================================================
                    # DETAILS
                    # =================================================

                    details = {

                        # ---------------------------------------------
                        # BASIC
                        # ---------------------------------------------

                        "connector_id":
                            connector_id,

                        "display_name":
                            display_name,

                        "name":
                            display_name,

                        "description":
                            description,

                        "lifecycle_state":
                            lifecycle_state,

                        "lifecycle_details":
                            lifecycle_details,

                        "state":
                            state,

                        "time_created":
                            time_created,

                        "time_updated":
                            time_updated,

                        # ---------------------------------------------
                        # SOURCE
                        # ---------------------------------------------

                        "source":
                            source_details,

                        "source_details":
                            source_details,

                        # ---------------------------------------------
                        # TARGET
                        # ---------------------------------------------

                        "target":
                            target_details,

                        "target_details":
                            target_details,

                        # ---------------------------------------------
                        # TASKS
                        # ---------------------------------------------

                        "tasks":
                            tasks_details,

                        "task_count":
                            task_count,

                        # ---------------------------------------------
                        # COMPLETE OCI CONNECTOR OBJECT
                        # ---------------------------------------------

                        "connector_details":
                            connector_dict,

                        # ---------------------------------------------
                        # TAGS
                        # ---------------------------------------------

                        "defined_tags":
                            _safe_value(
                                defined_tags
                            ),

                        "freeform_tags":
                            _safe_value(
                                freeform_tags
                            ),
                    }

                    # =================================================
                    # RESOURCE OBJECT
                    # =================================================

                    resource = Resource(

                        service="Service Connector",

                        resource_type="Service Connector",

                        name=display_name,

                        ocid=connector_id,

                        compartment_id=compartment_id,

                        compartment_name=compartment_name,

                        region=region,

                        state=lifecycle_state,

                        time_created=time_created,

                        defined_tags=_safe_value(
                            defined_tags
                        ),

                        freeform_tags=_safe_value(
                            freeform_tags
                        ),

                        details=details,
                    )

                    resources.append(
                        resource
                    )

                except Exception as error:

                    print(
                        f"    ERROR processing Service Connector "
                        f"{display_name}: {error}"
                    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print(
        f"Service Connectors: "
        f"{len(resources)} resources found"
    )

    return resources
