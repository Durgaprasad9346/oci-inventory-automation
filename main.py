from datetime import datetime
from pathlib import Path

import yaml

from collectors.compute import collect_compute
from excel.workbook import create_inventory_workbook
from utils.oci_auth import get_oci_config


def load_config():
    """Load application configuration from config.yaml."""

    config_file = Path("config.yaml")

    with config_file.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def main():
    print("=" * 60)
    print("OCI Inventory Automation")
    print("=" * 60)

    # Load application configuration
    app_config = load_config()

    # Load OCI authentication configuration
    oci_config = get_oci_config()

    print(f"OCI Region : {oci_config['region']}")
    print("Authentication : OCI config file")
    print()

    # ---------------------------------------------------------
    # Collect Compute resources
    # ---------------------------------------------------------

    print("Collecting Compute resources...")

    compute_resources = collect_compute(oci_config)

    print(f"Compute resources found: {len(compute_resources)}")

    # ---------------------------------------------------------
    # Prepare inventory data
    # ---------------------------------------------------------

    resources_by_service = {
        "Compute": compute_resources,
    }

    # ---------------------------------------------------------
    # Generate Excel report
    # ---------------------------------------------------------

    output_directory = app_config["inventory"]["output_directory"]

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    output_file = (
        Path(output_directory)
        / f"OCI_Inventory_{timestamp}.xlsx"
    )

    create_inventory_workbook(
        resources_by_service=resources_by_service,
        output_file=str(output_file),
    )

    print()
    print(f"Inventory report created:")
    print(output_file)

    print("=" * 60)
    print("Inventory generation completed")
    print("=" * 60)


if __name__ == "__main__":
    main()
