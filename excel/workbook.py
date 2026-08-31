from datetime import datetime, date, time
from pathlib import Path
import json
import re

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter


# ============================================================
# EXCEL VALUE SAFETY
# ============================================================

def excel_safe_value(value):
    """
    Convert OCI SDK values into values supported by Excel.

    OCI commonly returns timezone-aware datetime objects:

        2026-08-31 10:30:00+00:00

    openpyxl cannot write timezone-aware datetime values.

    We remove only the timezone information and preserve the
    date/time itself.
    """

    if isinstance(value, datetime):

        if value.tzinfo is not None:
            return value.replace(tzinfo=None)

        return value

    if isinstance(value, time):

        if value.tzinfo is not None:
            return value.replace(tzinfo=None)

        return value

    if isinstance(value, date):
        return value

    return value


# ============================================================
# SAFE STRING
# ============================================================

def safe_string(value):
    """
    Safely convert complex OCI values to strings.
    """

    if value is None:
        return ""

    if isinstance(value, (dict, list, tuple, set)):

        try:
            return json.dumps(
                value,
                default=str,
                ensure_ascii=False,
            )

        except Exception:
            return str(value)

    return str(value)


# ============================================================
# FLATTEN DICTIONARY
# ============================================================

def flatten_dict(data, prefix=""):
    """
    Flatten nested dictionaries for Excel columns.
    """

    result = {}

    if not isinstance(data, dict):
        return result

    for key, value in data.items():

        key = str(key)

        if prefix:
            new_key = f"{prefix}.{key}"
        else:
            new_key = key

        if isinstance(value, dict):

            result.update(
                flatten_dict(
                    value,
                    new_key,
                )
            )

        elif isinstance(value, (list, tuple, set)):

            result[new_key] = safe_string(
                value
            )

        else:

            result[new_key] = excel_safe_value(
                value
            )

    return result


# ============================================================
# OBJECT / DICTIONARY VALUE
# ============================================================

def get_field(obj, *names, default=None):
    """
    Read a field from either:
        - dictionary
        - Resource object
        - OCI SDK object
    """

    for name in names:

        if isinstance(obj, dict):

            if name in obj:
                return obj[name]

        else:

            if hasattr(obj, name):

                try:

                    value = getattr(
                        obj,
                        name,
                    )

                    if value is not None:
                        return value

                except Exception:
                    pass

    return default


# ============================================================
# CONVERT RESOURCE TO DICT
# ============================================================

def resource_to_dict(resource):
    """
    Convert Resource objects and dictionaries into a dictionary.
    """

    if isinstance(resource, dict):
        return dict(resource)

    data = {}

    # --------------------------------------------------------
    # Standard inventory fields
    # --------------------------------------------------------

    fields = [
        "service",
        "service_name",

        "resource_type",
        "resourceType",

        "name",
        "display_name",
        "displayName",

        "ocid",
        "id",
        "identifier",

        "compartment_id",
        "compartmentId",

        "compartment_name",
        "compartmentName",

        "region",

        "availability_domain",
        "availabilityDomain",

        "state",

        "lifecycle_state",
        "lifecycleState",

        "lifecycle_details",
        "lifecycleDetails",

        "time_created",
        "timeCreated",

        "creation_date",
        "created_at",

        "defined_tags",
        "definedTags",

        "freeform_tags",
        "freeformTags",

        "details",
        "additional_details",
        "additionalDetails",
    ]

    for field in fields:

        if hasattr(resource, field):

            try:

                value = getattr(
                    resource,
                    field,
                )

                if value is not None:
                    data[field] = value

            except Exception:
                pass

    # --------------------------------------------------------
    # Capture any other public Resource attributes
    # --------------------------------------------------------

    if hasattr(resource, "__dict__"):

        for key, value in resource.__dict__.items():

            if key.startswith("_"):
                continue

            if key not in data:
                data[key] = value

    return data


# ============================================================
# TAG EXTRACTION
# ============================================================

def extract_defined_tags(data):
    """
    Extract OCI defined tags and flatten them.

    Example:

        {
            "CostCenter": {
                "Environment": "DEV"
            }
        }

    becomes:

        CostCenter.Environment
    """

    tags = (
        data.get("defined_tags")
        or data.get("definedTags")
        or {}
    )

    if not isinstance(tags, dict):
        return {}

    return flatten_dict(tags)


def extract_freeform_tags(data):
    """
    Extract OCI freeform tags.
    """

    tags = (
        data.get("freeform_tags")
        or data.get("freeformTags")
        or {}
    )

    if not isinstance(tags, dict):
        return {}

    return flatten_dict(tags)


def include_tag(tag_name):
    """
    Exclude Schedule:* tags from individual tag columns.
    """

    if not tag_name:
        return False

    tag_name = str(tag_name)

    if tag_name.lower().startswith(
        "schedule:"
    ):
        return False

    return True


# ============================================================
# CREATION DATE
# ============================================================

def get_creation_date(data):
    """
    Get creation date from common OCI/collector fields.
    """

    value = (
        data.get("time_created")
        or data.get("timeCreated")
        or data.get("creation_date")
        or data.get("created_at")
    )

    return excel_safe_value(
        value
    )


# ============================================================
# BUILD STANDARD RESOURCE ROW
# ============================================================

STANDARD_COLUMNS = [
    "Service",
    "Resource Type",
    "Resource Name",
    "Resource OCID",
    "Compartment Name",
    "Compartment OCID",
    "Region",
    "Availability Domain",
    "Lifecycle State",
    "Lifecycle Details",
    "Creation Date",
]


def build_resource_row(resource):

    data = resource_to_dict(
        resource
    )

    row = {}

    # --------------------------------------------------------
    # Service
    # --------------------------------------------------------

    row["Service"] = (
        data.get("service")
        or data.get("service_name")
        or ""
    )

    # --------------------------------------------------------
    # Resource Type
    # --------------------------------------------------------

    row["Resource Type"] = (
        data.get("resource_type")
        or data.get("resourceType")
        or ""
    )

    # --------------------------------------------------------
    # Name
    # --------------------------------------------------------

    row["Resource Name"] = (
        data.get("name")
        or data.get("display_name")
        or data.get("displayName")
        or ""
    )

    # --------------------------------------------------------
    # OCID
    # --------------------------------------------------------

    row["Resource OCID"] = (
        data.get("ocid")
        or data.get("identifier")
        or data.get("id")
        or ""
    )

    # --------------------------------------------------------
    # Compartment
    # --------------------------------------------------------

    row["Compartment Name"] = (
        data.get("compartment_name")
        or data.get("compartmentName")
        or ""
    )

    row["Compartment OCID"] = (
        data.get("compartment_id")
        or data.get("compartmentId")
        or ""
    )

    # --------------------------------------------------------
    # Region
    # --------------------------------------------------------

    row["Region"] = (
        data.get("region")
        or ""
    )

    # --------------------------------------------------------
    # Availability Domain
    # --------------------------------------------------------

    row["Availability Domain"] = (
        data.get("availability_domain")
        or data.get("availabilityDomain")
        or ""
    )

    # --------------------------------------------------------
    # Lifecycle State
    # --------------------------------------------------------

    row["Lifecycle State"] = (
        data.get("state")
        or data.get("lifecycle_state")
        or data.get("lifecycleState")
        or ""
    )

    # --------------------------------------------------------
    # Lifecycle Details
    # --------------------------------------------------------

    row["Lifecycle Details"] = (
        data.get("lifecycle_details")
        or data.get("lifecycleDetails")
        or ""
    )

    # --------------------------------------------------------
    # Creation Date
    # --------------------------------------------------------

    row["Creation Date"] = get_creation_date(
        data
    )

    # --------------------------------------------------------
    # Defined Tags
    # --------------------------------------------------------

    defined_tags = extract_defined_tags(
        data
    )

    for tag_name, tag_value in defined_tags.items():

        if include_tag(tag_name):

            row[
                f"Tag: {tag_name}"
            ] = excel_safe_value(
                tag_value
            )

    # --------------------------------------------------------
    # Freeform Tags
    # --------------------------------------------------------

    freeform_tags = extract_freeform_tags(
        data
    )

    for tag_name, tag_value in freeform_tags.items():

        if include_tag(tag_name):

            row[
                f"Freeform Tag: {tag_name}"
            ] = excel_safe_value(
                tag_value
            )

    # --------------------------------------------------------
    # Resource-specific details
    # --------------------------------------------------------

    details = (
        data.get("details")
        or data.get("additional_details")
        or data.get("additionalDetails")
        or {}
    )

    if isinstance(details, dict):

        flattened_details = flatten_dict(
            details,
            "Details",
        )

        for key, value in flattened_details.items():

            if key not in row:

                row[key] = excel_safe_value(
                    value
                )

    return row


# ============================================================
# GET COLUMNS
# ============================================================

def get_columns(rows):

    columns = list(
        STANDARD_COLUMNS
    )

    tag_columns = set()
    other_columns = set()

    for row in rows:

        for key in row.keys():

            if key in columns:
                continue

            if (
                str(key).startswith("Tag:")
                or str(key).startswith("Freeform Tag:")
            ):

                tag_columns.add(
                    key
                )

            else:

                other_columns.add(
                    key
                )

    columns.extend(
        sorted(tag_columns)
    )

    columns.extend(
        sorted(other_columns)
    )

    return columns


# ============================================================
# SHEET NAME
# ============================================================

def sanitize_sheet_name(name):

    if not name:
        name = "Resources"

    name = str(name)

    name = re.sub(
        r"[\[\]\:\*\?\/\\]",
        "_",
        name,
    )

    name = name.strip()

    if not name:
        name = "Resources"

    return name[:31]


def get_unique_sheet_name(
    workbook,
    name,
):

    base = sanitize_sheet_name(
        name
    )

    if base not in workbook.sheetnames:
        return base

    counter = 2

    while True:

        suffix = f"_{counter}"

        candidate = (
            base[:31 - len(suffix)]
            + suffix
        )

        if candidate not in workbook.sheetnames:
            return candidate

        counter += 1


# ============================================================
# WRITE RESOURCE SHEET
# ============================================================

def write_resource_sheet(
    workbook,
    sheet_name,
    resources,
):

    if not resources:
        return None

    sheet_name = get_unique_sheet_name(
        workbook,
        sheet_name,
    )

    ws = workbook.create_sheet(
        title=sheet_name
    )

    # --------------------------------------------------------
    # Convert resources
    # --------------------------------------------------------

    rows = []

    for resource in resources:

        try:

            rows.append(
                build_resource_row(
                    resource
                )
            )

        except Exception as error:

            print(
                f"WARNING: Could not process "
                f"resource for Excel: {error}"
            )

    # --------------------------------------------------------
    # No rows
    # --------------------------------------------------------

    if not rows:
        return ws

    columns = get_columns(
        rows
    )

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

    for col_num, column in enumerate(
        columns,
        start=1,
    ):

        cell = ws.cell(
            row=1,
            column=col_num,
            value=column,
        )

        cell.font = Font(
            bold=True
        )

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True,
        )

    # --------------------------------------------------------
    # Data
    # --------------------------------------------------------

    for row_num, row_data in enumerate(
        rows,
        start=2,
    ):

        for col_num, column in enumerate(
            columns,
            start=1,
        ):

            value = row_data.get(
                column,
                "",
            )

            # =================================================
            # IMPORTANT TIMEZONE FIX
            # =================================================

            value = excel_safe_value(
                value
            )

            cell = ws.cell(
                row=row_num,
                column=col_num,
                value=value,
            )

            cell.alignment = Alignment(
                vertical="top",
                wrap_text=True,
            )

            # ------------------------------------------------
            # Creation Date format
            # ------------------------------------------------

            if (
                column == "Creation Date"
                and isinstance(
                    value,
                    datetime,
                )
            ):

                cell.number_format = (
                    "yyyy-mm-dd hh:mm:ss"
                )

    # --------------------------------------------------------
    # Freeze
    # --------------------------------------------------------

    ws.freeze_panes = "A2"

    # --------------------------------------------------------
    # Filter
    # --------------------------------------------------------

    ws.auto_filter.ref = (
        ws.dimensions
    )

    # --------------------------------------------------------
    # Table
    # --------------------------------------------------------

    if ws.max_row >= 2:

        table_base = re.sub(
            r"[^A-Za-z0-9_]",
            "",
            sheet_name,
        )

        if not table_base:
            table_base = "Resources"

        table_name = (
            "tbl_"
            + table_base[:20]
        )

        existing_names = set()

        for existing_ws in workbook.worksheets:

            for existing_table in (
                existing_ws.tables.keys()
            ):

                existing_names.add(
                    existing_table
                )

        original_name = table_name

        counter = 2

        while table_name in existing_names:

            table_name = (
                original_name
                + str(counter)
            )

            counter += 1

        table_ref = (
            f"A1:"
            f"{get_column_letter(ws.max_column)}"
            f"{ws.max_row}"
        )

        table = Table(
            displayName=table_name,
            ref=table_ref,
        )

        table_style = TableStyleInfo(
            name="TableStyleMedium2",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=False,
        )

        table.tableStyleInfo = (
            table_style
        )

        ws.add_table(
            table
        )

    # --------------------------------------------------------
    # Column widths
    # --------------------------------------------------------

    for col_num in range(
        1,
        ws.max_column + 1,
    ):

        letter = get_column_letter(
            col_num
        )

        max_length = 0

        for cell in ws[letter]:

            if cell.value is None:
                continue

            length = len(
                str(cell.value)
            )

            if length > max_length:
                max_length = length

        width = min(
            max(
                max_length + 2,
                12,
            ),
            60,
        )

        header = ws.cell(
            row=1,
            column=col_num,
        ).value

        if header in (
            "Resource OCID",
            "Compartment OCID",
        ):

            width = 55

        ws.column_dimensions[
            letter
        ].width = width

    ws.row_dimensions[
        1
    ].height = 30

    return ws


# ============================================================
# FLATTEN resources_by_service
# ============================================================

def flatten_resources_by_service(
    resources_by_service
):
    """
    Convert the existing main.py structure into one resource list.

    Supports structures such as:

        {
            "Compute": [resource1, resource2]
        }

    and:

        {
            "Compute": {
                "Instance": [resource1, resource2],
                "Volume": [resource3]
            }
        }
    """

    resources = []

    if resources_by_service is None:
        return resources

    if isinstance(
        resources_by_service,
        list,
    ):

        return list(
            resources_by_service
        )

    if not isinstance(
        resources_by_service,
        dict,
    ):

        return [resources_by_service]

    for service_value in (
        resources_by_service.values()
    ):

        if service_value is None:
            continue

        # ----------------------------------------------------
        # Service -> list
        # ----------------------------------------------------

        if isinstance(
            service_value,
            list,
        ):

            resources.extend(
                service_value
            )

            continue

        # ----------------------------------------------------
        # Service -> dict
        # ----------------------------------------------------

        if isinstance(
            service_value,
            dict,
        ):

            for resource_value in (
                service_value.values()
            ):

                if resource_value is None:
                    continue

                if isinstance(
                    resource_value,
                    list,
                ):

                    resources.extend(
                        resource_value
                    )

                else:

                    resources.append(
                        resource_value
                    )

            continue

        # ----------------------------------------------------
        # Single resource
        # ----------------------------------------------------

        resources.append(
            service_value
        )

    return resources


# ============================================================
# GROUP RESOURCES
# ============================================================

def group_resources(
    resources
):

    grouped = {}

    for resource in resources:

        data = resource_to_dict(
            resource
        )

        service = (
            data.get("service")
            or data.get("service_name")
            or "Other"
        )

        resource_type = (
            data.get("resource_type")
            or data.get("resourceType")
            or "Resource"
        )

        key = (
            str(service),
            str(resource_type),
        )

        grouped.setdefault(
            key,
            [],
        ).append(
            resource
        )

    return grouped


# ============================================================
# SUMMARY
# ============================================================

def create_summary_sheet(
    workbook,
    resources,
):

    ws = workbook.create_sheet(
        title="Summary",
        index=0,
    )

    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------

    ws["A1"] = (
        "OCI Tenancy Resource Inventory"
    )

    ws["A1"].font = Font(
        bold=True,
        size=16,
    )

    ws.merge_cells(
        "A1:E1"
    )

    # --------------------------------------------------------
    # Report generated
    # --------------------------------------------------------

    ws["A3"] = (
        "Report Generated"
    )

    ws["B3"] = excel_safe_value(
        datetime.now()
    )

    ws["B3"].number_format = (
        "yyyy-mm-dd hh:mm:ss"
    )

    # --------------------------------------------------------
    # Total
    # --------------------------------------------------------

    ws["A5"] = (
        "Total Resources"
    )

    ws["B5"] = len(
        resources
    )

    # --------------------------------------------------------
    # Counts
    # --------------------------------------------------------

    service_counts = {}
    resource_type_counts = {}

    for resource in resources:

        data = resource_to_dict(
            resource
        )

        service = (
            data.get("service")
            or data.get("service_name")
            or "Unknown"
        )

        resource_type = (
            data.get("resource_type")
            or data.get("resourceType")
            or "Unknown"
        )

        service_counts[
            str(service)
        ] = (
            service_counts.get(
                str(service),
                0,
            )
            + 1
        )

        resource_type_counts[
            str(resource_type)
        ] = (
            resource_type_counts.get(
                str(resource_type),
                0,
            )
            + 1
        )

    # --------------------------------------------------------
    # Resource Type Summary
    # --------------------------------------------------------

    ws["A7"] = (
        "Resource Type"
    )

    ws["B7"] = (
        "Count"
    )

    ws["A7"].font = Font(
        bold=True
    )

    ws["B7"].font = Font(
        bold=True
    )

    row = 8

    for resource_type in sorted(
        resource_type_counts
    ):

        ws.cell(
            row=row,
            column=1,
            value=resource_type,
        )

        ws.cell(
            row=row,
            column=2,
            value=resource_type_counts[
                resource_type
            ],
        )

        row += 1

    # --------------------------------------------------------
    # Service Summary
    # --------------------------------------------------------

    ws["D7"] = (
        "Service"
    )

    ws["E7"] = (
        "Count"
    )

    ws["D7"].font = Font(
        bold=True
    )

    ws["E7"].font = Font(
        bold=True
    )

    row = 8

    for service in sorted(
        service_counts
    ):

        ws.cell(
            row=row,
            column=4,
            value=service,
        )

        ws.cell(
            row=row,
            column=5,
            value=service_counts[
                service
            ],
        )

        row += 1

    # --------------------------------------------------------
    # Formatting
    # --------------------------------------------------------

    ws.freeze_panes = "A8"

    ws.column_dimensions[
        "A"
    ].width = 35

    ws.column_dimensions[
        "B"
    ].width = 15

    ws.column_dimensions[
        "C"
    ].width = 5

    ws.column_dimensions[
        "D"
    ].width = 35

    ws.column_dimensions[
        "E"
    ].width = 15

    return ws


# ============================================================
# CREATE INVENTORY WORKBOOK
# ============================================================

def create_inventory_workbook(
    resources=None,
    resources_by_service=None,
    output_file=None,
    **kwargs,
):
    """
    Main workbook creation function.

    IMPORTANT:
    Supports the existing main.py call:

        create_inventory_workbook(
            resources_by_service=...
        )

    It also supports:

        create_inventory_workbook(
            resources=...
        )

    Additional keyword arguments are accepted through **kwargs
    so the workbook does not fail if main.py passes an existing
    optional parameter.
    """

    # ========================================================
    # HANDLE EXISTING resources_by_service ARGUMENT
    # ========================================================

    if resources_by_service is not None:

        resources = (
            flatten_resources_by_service(
                resources_by_service
            )
        )

    elif resources is None:

        resources = []

    else:

        resources = list(
            resources
        )

    # ========================================================
    # OUTPUT FILE COMPATIBILITY
    # ========================================================

    if output_file is None:

        # Support common existing names if main.py supplies them
        output_file = (
            kwargs.get("output_path")
            or kwargs.get("filename")
            or kwargs.get("file_path")
            or kwargs.get("report_file")
        )

    # ========================================================
    # CREATE WORKBOOK
    # ========================================================

    workbook = Workbook()

    default_sheet = workbook.active

    workbook.remove(
        default_sheet
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    create_summary_sheet(
        workbook,
        resources,
    )

    # ========================================================
    # GROUP
    # ========================================================

    grouped = group_resources(
        resources
    )

    # ========================================================
    # RESOURCE SHEETS
    # ========================================================

    for (
        service,
        resource_type,
    ), resource_list in sorted(
        grouped.items(),
        key=lambda item: (
            str(item[0][0]),
            str(item[0][1]),
        ),
    ):

        # ----------------------------------------------------
        # Use resource type for sheet name.
        #
        # If same resource type occurs under different
        # services, unique_sheet_name() will add _2, _3...
        # ----------------------------------------------------

        sheet_name = (
            resource_type
        )

        write_resource_sheet(
            workbook,
            sheet_name,
            resource_list,
        )

    # ========================================================
    # FINAL EXCEL SAFETY PASS
    # ========================================================

    # This is an additional protection against any timezone
    # aware datetime hidden inside tags/details.
    #
    # This directly prevents:
    #
    # TypeError:
    # Excel does not support timezones in datetimes.
    # ========================================================

    for ws in workbook.worksheets:

        for row in ws.iter_rows():

            for cell in row:

                if isinstance(
                    cell.value,
                    datetime,
                ):

                    cell.value = (
                        excel_safe_value(
                            cell.value
                        )
                    )

                elif isinstance(
                    cell.value,
                    time,
                ):

                    cell.value = (
                        excel_safe_value(
                            cell.value
                        )
                    )

    # ========================================================
    # SAVE
    # ========================================================

    if output_file:

        output_path = Path(
            output_file
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        workbook.save(
            output_path
        )

        print(
            f"Inventory workbook created: "
            f"{output_path}"
        )

    return workbook


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

def create_workbook(
    resources=None,
    resources_by_service=None,
    output_file=None,
    **kwargs,
):
    """
    Backward-compatible wrapper.
    """

    return create_inventory_workbook(
        resources=resources,
        resources_by_service=resources_by_service,
        output_file=output_file,
        **kwargs,
    )
