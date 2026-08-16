from pathlib import Path
from typing import Dict, List

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter

from collectors.base import Resource


def create_inventory_workbook(
    resources_by_service: Dict[str, List[Resource]],
    output_file: str,
) -> None:
    """
    Create the OCI inventory Excel workbook.

    Creates:
        1. Summary sheet
        2. One detailed sheet per service
    """

    workbook = Workbook()

    # Remove default worksheet
    default_sheet = workbook.active
    workbook.remove(default_sheet)

    # ---------------------------------------------------------
    # Summary sheet
    # ---------------------------------------------------------

    summary_sheet = workbook.create_sheet("Summary")

    summary_headers = [
        "SNo",
        "Service Name",
        "Description",
        "Resource Count",
    ]

    summary_sheet.append(summary_headers)
    _format_header(summary_sheet)

    summary_row = 2

    # ---------------------------------------------------------
    # Service sheets
    # ---------------------------------------------------------

    for service_name, resources in resources_by_service.items():

        sheet_name = _safe_sheet_name(service_name)

        service_sheet = workbook.create_sheet(sheet_name)

        service_headers = [
            "SNo",
            "Resource Name",
            "Resource Type",
            "OCID",
            "Compartment Name",
            "Compartment OCID",
            "Region",
            "State",
        ]

        service_sheet.append(service_headers)
        _format_header(service_sheet)

        # Add resources
        for index, resource in enumerate(resources, start=1):

            service_sheet.append(
                [
                    index,
                    resource.name,
                    resource.resource_type,
                    resource.ocid,
                    resource.compartment_name,
                    resource.compartment_id,
                    resource.region,
                    resource.state,
                ]
            )

        # Freeze header
        service_sheet.freeze_panes = "A2"

        # Enable filtering
        if resources:
            service_sheet.auto_filter.ref = service_sheet.dimensions

        _format_sheet(service_sheet)

        # -----------------------------------------------------
        # Add service to Summary
        # -----------------------------------------------------

        summary_sheet.cell(
            summary_row,
            1,
            summary_row - 1,
        )

        summary_sheet.cell(
            summary_row,
            2,
            service_name,
        )

        summary_sheet.cell(
            summary_row,
            3,
            f"{service_name} resources",
        )

        summary_sheet.cell(
            summary_row,
            4,
            len(resources),
        )

        summary_row += 1

    # ---------------------------------------------------------
    # Format Summary
    # ---------------------------------------------------------

    summary_sheet.freeze_panes = "A2"

    if summary_row > 2:
        summary_sheet.auto_filter.ref = summary_sheet.dimensions

    _format_sheet(summary_sheet)

    # ---------------------------------------------------------
    # Save workbook
    # ---------------------------------------------------------

    output_path = Path(output_file)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    workbook.save(output_path)


def _format_header(sheet) -> None:
    """Format worksheet header."""

    for cell in sheet[1]:

        cell.font = Font(bold=True)

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )


def _format_sheet(sheet) -> None:
    """Apply common worksheet formatting."""

    for row in sheet.iter_rows():

        for cell in row:

            cell.alignment = Alignment(
                vertical="center",
                wrap_text=True,
            )

    # Auto-size columns
    for column_cells in sheet.columns:

        max_length = 0

        column_letter = get_column_letter(
            column_cells[0].column
        )

        for cell in column_cells:

            if cell.value is not None:

                max_length = max(
                    max_length,
                    len(str(cell.value)),
                )

        adjusted_width = min(
            max(max_length + 2, 12),
            50,
        )

        sheet.column_dimensions[
            column_letter
        ].width = adjusted_width


def _safe_sheet_name(name: str) -> str:
    """
    Convert a service name into a valid Excel
    worksheet name.
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

        sheet_name = sheet_name.replace(
            character,
            "_",
        )

    return sheet_name[:31]
