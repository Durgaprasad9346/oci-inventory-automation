from datetime import datetime
from pathlib import Path

import yaml

from collectors.compute import collect_compute
from collectors.manager import CollectorManager
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

    # ---------------------------------------------------------
    # Load application configuration
    # ---------------------------------------------------------

    app_config = load_config()

    # ---------------------------------------------------------
    # Load OCI authentication configuration
    # ---------------------------------------------------------

    oci_config = get_oci_config()

    print(f"OCI Region       : {oci_config['region']}")
    print("Authentication   : OCI config file")
    print()

    # ---------------------------------------------------------
    # Create collector manager
    # ---------------------------------------------------------

    manager = CollectorManager()

    # Register OCI service collectors
    manager.register(
        "Compute",
        collect_compute,
    )

    # ---------------------------------------------------------
    # Collect all registered services
    # ---------------------------------------------------------

    resources_by_service = manager.collect_all(
        oci_config
    )

    # ---------------------------------------------------------
    # Generate Excel report
    # ---------------------------------------------------------

    output_directory = app_config["inventory"]["output_directory"]

    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    output_file = (
        Path(output_directory)
        / f"OCI_Inventory_{timestamp}.xlsx"
    )

    create_inventory_workbook(
        resources_by_service=resources_by_service,
        output_file=str(output_file),
    )

    # ---------------------------------------------------------
    # Display summary
    # ---------------------------------------------------------

    print()
    print("-" * 60)
    print("Inventory Summary")
    print("-" * 60)

    for service_name, resources in resources_by_service.items():
        print(
            f"{service_name:<30} {len(resources):>6}"
        )

    print("-" * 60)

    print(f"Report created: {output_file}")

    print("=" * 60)
    print("Inventory generation completed")
    print("=" * 60)


if __name__ == "__main__":
    main()
