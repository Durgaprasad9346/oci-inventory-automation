from pathlib import Path
from typing import Dict, List

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from collectors.base import Resource


def create_inventory_workbook(
    resources_by_service: Dict[str, List[Resource]],
    output_file: str,
) -> None:
    """
    Create the OCI inventory Excel workbook.

    The workbook contains:
      1. Summary sheet
      2. One sheet per OCI service
    """

    workbook = Workbook()

    # Remove the default worksheet
    default_sheet = workbook.active
    workbook.remove(default_sheet)

    # Create Summary sheet first
    summary_sheet = workbook.create_sheet("Summary")

    # Summary headers
    summary_headers = [
        "SNo",
        "Service Name",
        "Description",
        "Resource Count",
    ]

    summary_sheet.append(summary_headers)

    # Format summary header
    _format_header(summary_sheet)

    # Create individual service sheets
    summary_row = 2

    for service_name, resources in resources_by_service.items():

        # Excel sheet names have a maximum length of 31 characters
        sheet_name = _safe_sheet_name(service_name)

        service_sheet = workbook.create_sheet(sheet_name)

        service_headers = [
            "SNo",
            "Resource Name",
            "Resource Type",
            "OCID",
            "Compartment OCID",
            "Region",
            "State",
        ]

        service_sheet.append(service_headers)

        _format_header(service_sheet)

        # Add every resource to the service sheet
        for index, resource in enumerate(resources, start=1):

            service_sheet.append(
                [
                    index,
                    resource.name,
                    resource.resource_type,
                    resource.ocid,
                    resource.compartment_id,
                    resource.region,
                    resource.state,
                ]
            )

        # Add filter and freeze header
        service_sheet.freeze_panes = "A2"

        if resources:
            service_sheet.auto_filter.ref = service_sheet.dimensions

        # Format service sheet
        _format_sheet(service_sheet)

        # Add information to Summary
        description = f"{service_name} resources"
        resource_count = len(resources)

        summary_sheet.cell(summary_row, 1, summary_row - 1)
        summary_sheet.cell(summary_row, 2, service_name)
        summary_sheet.cell(summary_row, 3, description)
        summary_sheet.cell(summary_row, 4, resource_count)

        summary_row += 1

    # Format summary
    summary_sheet.freeze_panes = "A2"

    if summary_row > 2:
        summary_sheet.auto_filter.ref = summary_sheet.dimensions

    _format_sheet(summary_sheet)

    # Create output directory
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save workbook
    workbook.save(output_path)


def _format_header(sheet) -> None:
    """Format the first row of a worksheet."""

    for cell in sheet[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    sheet.freeze_panes = "A2"


def _format_sheet(sheet) -> None:
    """Apply common formatting to a worksheet."""

    for row in sheet.iter_rows():

        for cell in row:
            cell.alignment = Alignment(
                vertical="center",
                wrap_text=True,
            )

    # Automatically size columns
    for column_cells in sheet.columns:

        max_length = 0
        column_letter = get_column_letter(column_cells[0].column)

        for cell in column_cells:

            if cell.value is not None:
                max_length = max(
                    max_length,
                    len(str(cell.value)),
                )

        # Keep columns from becoming excessively wide
        adjusted_width = min(max(max_length + 2, 12), 50)

        sheet.column_dimensions[column_letter].width = adjusted_width


def _safe_sheet_name(name: str) -> str:
    """
    Convert a service name into a valid Excel worksheet name.
    """

    invalid_characters = [
        "\\",
        "/",
        "*",
        "?",
        ":",
        "[",
        "]",
    ]

    sheet_name = name

    for character in invalid_characters:
        sheet_name = sheet_name.replace(character, "_")

    return sheet_name[:31]
