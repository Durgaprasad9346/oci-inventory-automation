from datetime import datetime, date, time
from pathlib import Path
import json
import re

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.formatting.rule import FormulaRule


# ============================================================
# EXCEL SAFE VALUE
# ============================================================

def excel_safe_value(value):
    """
    Convert OCI SDK values into Excel-compatible values.

    OCI frequently returns timezone-aware datetime objects such as:

        2026-08-31 10:30:00+00:00

    openpyxl does not support timezone-aware datetime values.

    We therefore remove only tzinfo and preserve the actual
    date/time value.
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
# GENERAL HELPERS
# ============================================================

def safe_string(value):
    """
    Convert an arbitrary value to a safe string.
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


def flatten_dict(data, prefix=""):
    """
    Flatten nested dictionaries.

    Example:

        {
            "maxlife": {
                "env": "prod",
                "project": "abc"
            }
        }

    becomes:

        {
            "maxlife.env": "prod",
            "maxlife.project": "abc"
        }
    """

    result = {}

    if not isinstance(data, dict):
        return result

    for key, value in data.items():

        key = str(key)

        new_key = (
            f"{prefix}.{key}"
            if prefix
            else key
        )

        if isinstance(value, dict):

            nested = flatten_dict(
                value,
                new_key,
            )

            result.update(nested)

        elif isinstance(value, (list, tuple)):

            result[new_key] = safe_string(value)

        else:

            result[new_key] = value

    return result


def normalize_header(value):
    """
    Convert a field name into a readable Excel header.
    """

    if value is None:
        return ""

    value = str(value)

    value = value.replace("_", " ")
    value = value.replace("-", " ")

    value = re.sub(
        r"(?<!^)(?=[A-Z])",
        " ",
        value,
    )

    return " ".join(
        value.split()
    ).title()


def sanitize_sheet_name(name):
    """
    Excel worksheet names:
      - max 31 characters
      - cannot contain []:*?/\\
    """

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


def unique_sheet_name(workbook, name):
    """
    Make sure worksheet name is unique.
    """

    base = sanitize_sheet_name(name)

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
# RESOURCE CONVERSION
# ============================================================

def get_value(obj, *names, default=None):
    """
    Read a value from either:
      - object attributes
      - dictionaries
    """

    for name in names:

        if isinstance(obj, dict):

            if name in obj:
                return obj[name]

        else:

            if hasattr(obj, name):
                return getattr(
                    obj,
                    name,
                )

    return default


def resource_to_dict(resource):
    """
    Convert collector Resource object/dict into a dictionary.

    Supports both dictionaries and normal Python objects.
    """

    if isinstance(resource, dict):

        data = dict(resource)

    else:

        data = {}

        # ----------------------------------------------------
        # Known standard fields
        # ----------------------------------------------------

        standard_fields = [
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

        for field in standard_fields:

            if hasattr(resource, field):

                value = getattr(
                    resource,
                    field,
                )

                if value is not None:
                    data[field] = value

        # ----------------------------------------------------
        # Collect object __dict__ values too
        # ----------------------------------------------------

        if hasattr(resource, "__dict__"):

            for key, value in resource.__dict__.items():

                if key.startswith("_"):
                    continue

                if key not in data:
                    data[key] = value

    return data


# ============================================================
# TAG HANDLING
# ============================================================

def extract_defined_tags(data):
    """
    Extract OCI defined tags.

    Nested tags are flattened.

    Example:

        maxlife:
          env: prod
          project: xyz

    becomes:

        maxlife.env
        maxlife.project
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

    return dict(tags)


def should_include_tag(tag_name):
    """
    Include normal OCI tags.

    Schedule tags are excluded from the individual tag
    columns because they are generally backup-policy/system
    scheduling metadata.

    Example excluded:

        Schedule:Monthly
        Schedule:Daily
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
# DATETIME HANDLING
# ============================================================

def get_creation_date(data):
    """
    Get resource creation date from common collector fields.
    """

    value = (
        data.get("time_created")
        or data.get("timeCreated")
        or data.get("creation_date")
        or data.get("created_at")
    )

    return excel_safe_value(value)


# ============================================================
# STANDARD COLUMNS
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


# ============================================================
# BUILD RESOURCE ROW
# ============================================================

def build_resource_row(resource):
    """
    Build a normalized resource dictionary.

    This guarantees that the important inventory fields are
    available for every OCI resource.
    """

    data = resource_to_dict(resource)

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
    # Resource Name
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

        if should_include_tag(tag_name):

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

        if should_include_tag(tag_name):

            row[
                f"Freeform Tag: {tag_name}"
            ] = excel_safe_value(
                tag_value
            )

    # --------------------------------------------------------
    # Additional Details
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

            # Avoid overwriting standard fields
            if key not in row:
                row[key] = excel_safe_value(
                    value
                )

    return row


# ============================================================
# COLLECT ALL COLUMNS
# ============================================================

def collect_columns(rows):
    """
    Create a stable set of columns across all resources.

    Standard columns are always first.
    Tag columns come next.
    Additional resource-specific fields follow.
    """

    columns = list(
        STANDARD_COLUMNS
    )

    discovered = []

    for row in rows:

        for key in row.keys():

            if key not in columns and key not in discovered:
                discovered.append(key)

    # --------------------------------------------------------
    # Put tags before arbitrary details
    # --------------------------------------------------------

    tag_columns = sorted(
        [
            x
            for x in discovered
            if x.startswith("Tag:")
            or x.startswith("Freeform Tag:")
        ]
    )

    other_columns = sorted(
        [
            x
            for x in discovered
            if x not in tag_columns
        ]
    )

    columns.extend(
        tag_columns
    )

    columns.extend(
        other_columns
    )

    return columns


# ============================================================
# WRITE RESOURCE SHEET
# ============================================================

def write_resource_sheet(
    workbook,
    sheet_name,
    resources,
):
    """
    Create one Excel sheet for a resource/service.
    """

    if not resources:
        return None

    sheet_name = unique_sheet_name(
        workbook,
        sheet_name,
    )

    ws = workbook.create_sheet(
        title=sheet_name
    )

    # --------------------------------------------------------
    # Normalize resources
    # --------------------------------------------------------

    rows = [
        build_resource_row(resource)
        for resource in resources
    ]

    columns = collect_columns(
        rows
    )

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

    for col_num, header in enumerate(
        columns,
        start=1,
    ):

        cell = ws.cell(
            row=1,
            column=col_num,
            value=header,
        )

        cell.font = Font(
            bold=True,
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

            # ------------------------------------------------
            # THIS FIXES THE TIMEZONE ERROR
            # ------------------------------------------------

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

            if column == "Creation Date":

                if isinstance(
                    value,
                    datetime,
                ):

                    cell.number_format = (
                        "yyyy-mm-dd hh:mm:ss"
                    )

    # --------------------------------------------------------
    # Freeze header
    # --------------------------------------------------------

    ws.freeze_panes = "A2"

    # --------------------------------------------------------
    # Auto filter
    # --------------------------------------------------------

    ws.auto_filter.ref = (
        ws.dimensions
    )

    # --------------------------------------------------------
    # Excel table
    # --------------------------------------------------------

    if ws.max_row >= 2:

        table_name = re.sub(
            r"[^A-Za-z0-9_]",
            "",
            sheet_name,
        )

        table_name = (
            "tbl_"
            + table_name[:20]
        )

        # Make table name unique
        existing_tables = set()

        for existing_ws in workbook.worksheets:

            existing_tables.update(
                existing_ws.tables.keys()
            )

        original_table_name = table_name
        counter = 2

        while table_name in existing_tables:

            table_name = (
                original_table_name
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

        style = TableStyleInfo(
            name="TableStyleMedium2",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=False,
        )

        table.tableStyleInfo = style

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

        column_letter = get_column_letter(
            col_num
        )

        max_length = 0

        for cell in ws[
            column_letter
        ]:

            if cell.value is None:
                continue

            value_length = len(
                str(cell.value)
            )

            if value_length > max_length:
                max_length = value_length

        width = min(
            max(
                max_length + 2,
                12,
            ),
            60,
        )

        # OCIDs need more space
        if ws.cell(
            row=1,
            column=col_num,
        ).value == "Resource OCID":

            width = 55

        if ws.cell(
            row=1,
            column=col_num,
        ).value == "Compartment OCID":

            width = 55

        ws.column_dimensions[
            column_letter
        ].width = width

    # --------------------------------------------------------
    # Header row height
    # --------------------------------------------------------

    ws.row_dimensions[
        1
    ].height = 30

    return ws


# ============================================================
# SUMMARY SHEET
# ============================================================

def create_summary_sheet(
    workbook,
    resources,
):
    """
    Create inventory summary sheet.
    """

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
        "A1:D1"
    )

    # --------------------------------------------------------
    # Report generated time
    # --------------------------------------------------------

    ws["A3"] = (
        "Report Generated"
    )

    generated_time = datetime.now()

    ws["B3"] = excel_safe_value(
        generated_time
    )

    ws["B3"].number_format = (
        "yyyy-mm-dd hh:mm:ss"
    )

    # --------------------------------------------------------
    # Total resource count
    # --------------------------------------------------------

    ws["A5"] = (
        "Total Resources"
    )

    ws["B5"] = len(
        resources
    )

    # --------------------------------------------------------
    # Resource type counts
    # --------------------------------------------------------

    type_counts = {}

    service_counts = {}

    for resource in resources:

        data = resource_to_dict(
            resource
        )

        resource_type = (
            data.get("resource_type")
            or data.get("resourceType")
            or "Unknown"
        )

        service = (
            data.get("service")
            or data.get("service_name")
            or "Unknown"
        )

        type_counts[
            resource_type
        ] = (
            type_counts.get(
                resource_type,
                0,
            )
            + 1
        )

        service_counts[
            service
        ] = (
            service_counts.get(
                service,
                0,
            )
            + 1
        )

    # --------------------------------------------------------
    # Resource Type table
    # --------------------------------------------------------

    start_row = 7

    ws.cell(
        row=start_row,
        column=1,
        value="Resource Type",
    )

    ws.cell(
        row=start_row,
        column=2,
        value="Count",
    )

    for cell in ws[
        start_row
    ]:

        cell.font = Font(
            bold=True
        )

    row_num = start_row + 1

    for resource_type in sorted(
        type_counts
    ):

        ws.cell(
            row=row_num,
            column=1,
            value=resource_type,
        )

        ws.cell(
            row=row_num,
            column=2,
            value=type_counts[
                resource_type
            ],
        )

        row_num += 1

    # --------------------------------------------------------
    # Service table
    # --------------------------------------------------------

    service_start = (
        start_row
    )

    service_col = 4

    ws.cell(
        row=service_start,
        column=service_col,
        value="Service",
    )

    ws.cell(
        row=service_start,
        column=service_col + 1,
        value="Count",
    )

    ws.cell(
        row=service_start,
        column=service_col,
    ).font = Font(
        bold=True
    )

    ws.cell(
        row=service_start,
        column=service_col + 1,
    ).font = Font(
        bold=True
    )

    row_num = service_start + 1

    for service in sorted(
        service_counts
    ):

        ws.cell(
            row=row_num,
            column=service_col,
            value=service,
        )

        ws.cell(
            row=row_num,
            column=service_col + 1,
            value=service_counts[
                service
            ],
        )

        row_num += 1

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
# GROUP RESOURCES
# ============================================================

def group_resources(resources):
    """
    Group resources by service and resource type.

    Example:

        Compute
          Instance

        Storage
          Volume

    """

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
            service,
            resource_type,
        )

        grouped.setdefault(
            key,
            [],
        ).append(
            resource
        )

    return grouped


# ============================================================
# CREATE INVENTORY WORKBOOK
# ============================================================

def create_inventory_workbook(
    resources,
    output_file=None,
):
    """
    Create the complete OCI inventory workbook.

    Parameters
    ----------
    resources:
        List of Resource objects/dictionaries.

    output_file:
        Optional output XLSX path.

    Returns
    -------
    Workbook
    """

    # --------------------------------------------------------
    # Create workbook
    # --------------------------------------------------------

    workbook = Workbook()

    # Remove default sheet
    default_sheet = workbook.active

    workbook.remove(
        default_sheet
    )

    # --------------------------------------------------------
    # Safety
    # --------------------------------------------------------

    if resources is None:
        resources = []

    resources = list(
        resources
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    create_summary_sheet(
        workbook,
        resources,
    )

    # --------------------------------------------------------
    # Group resources
    # --------------------------------------------------------

    grouped = group_resources(
        resources
    )

    # --------------------------------------------------------
    # Create sheets
    # --------------------------------------------------------

    for (
        service,
        resource_type,
    ), service_resources in sorted(
        grouped.items(),
        key=lambda item: (
            str(item[0][0]),
            str(item[0][1]),
        ),
    ):

        # ----------------------------------------------------
        # Prefer resource type as worksheet name
        # ----------------------------------------------------

        sheet_name = str(
            resource_type
        )

        write_resource_sheet(
            workbook,
            sheet_name,
            service_resources,
        )

    # --------------------------------------------------------
    # Save workbook
    # --------------------------------------------------------

    if output_file:

        output_path = Path(
            output_file
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # ----------------------------------------------------
        # Final safety pass:
        # Remove timezone from every datetime/time cell.
        #
        # This protects us even if a collector puts a datetime
        # inside details/tags.
        # ----------------------------------------------------

        for ws in workbook.worksheets:

            for row in ws.iter_rows():

                for cell in row:

                    if isinstance(
                        cell.value,
                        (
                            datetime,
                            time,
                        ),
                    ):

                        cell.value = (
                            excel_safe_value(
                                cell.value
                            )
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
    resources,
    output_file=None,
):
    """
    Backward-compatible wrapper.
    """

    return create_inventory_workbook(
        resources,
        output_file,
    )
