from datetime import datetime
from pathlib import Path

import yaml

from collectors.compute import collect_compute
from collectors.block_volume import collect_block_volume
from collectors.boot_volume import collect_boot_volume
from collectors.vcn import collect_vcn
from collectors.subnet import collect_subnet
from collectors.load_balancer import collect_load_balancer
from collectors.file_storage import collect_file_storage
from collectors.object_storage import collect_object_storage
from collectors.exacs import collect_exacs
from collectors.db_system import collect_db_system
from collectors.postgresql import collect_postgresql
from collectors.nosql import collect_nosql
from collectors.vault import collect_vault
from collectors.keys import collect_keys
from collectors.secrets import collect_secrets
from collectors.notifications import collect_notifications
from collectors.alarms import collect_alarms
from collectors.logging import collect_logging
from collectors.streaming import collect_streaming
from collectors.dns import collect_dns

from collectors.manager import CollectorManager
from excel.workbook import create_inventory_workbook
from utils.oci_auth import get_oci_config


def load_config():
    """Load application configuration."""

    config_file = Path("config.yaml")

    with config_file.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def main():

    print("=" * 70)
    print("OCI Inventory Automation")
    print("=" * 70)

    # ---------------------------------------------------------
    # Load configuration
    # ---------------------------------------------------------

    app_config = load_config()

    # ---------------------------------------------------------
    # OCI authentication
    # ---------------------------------------------------------

    oci_config = get_oci_config()

    print(f"OCI Default Region : {oci_config['region']}")
    print("Authentication     : OCI config file")
    print()

    # ---------------------------------------------------------
    # Collector Manager
    # ---------------------------------------------------------

    manager = CollectorManager()

    # ---------------------------------------------------------
    # Register collectors
    # ---------------------------------------------------------

    manager.register(
        "Compute",
        collect_compute,
    )

    manager.register(
        "Block Volume",
        collect_block_volume,
    )

    manager.register(
        "Boot Volume",
        collect_boot_volume,
    )

    manager.register(
        "VCN",
        collect_vcn,
    )

    manager.register(
        "Subnet",
        collect_subnet,
    )

    manager.register(
        "Load Balancer",
        collect_load_balancer,
    )

    manager.register(
        "File Storage",
        collect_file_storage,
    )

    manager.register(
        "Object Storage",
        collect_object_storage,
    )

    manager.register(
        "ExaCS",
        collect_exacs,
    )

    manager.register(
        "DB Systems",
        collect_db_system,
    )

    manager.register(
        "PostgreSQL",
        collect_postgresql,
    )

    manager.register(
        "NoSQL Database",
        collect_nosql,
    )

    manager.register(
        "Vault",
        collect_vault,
    )

    manager.register(
        "Key Management",
        collect_keys,
    )

    manager.register(
        "Secrets",
        collect_secrets,
    )

    manager.register(
        "Notifications",
        collect_notifications,
    )

    manager.register(
        "Monitoring",
        collect_alarms,
    )

    manager.register(
        "Logging",
        collect_logging,
    )

    manager.register(
        "Streaming",
        collect_streaming,
    )

    manager.register(
        "DNS",
        collect_dns,
    )

    # ---------------------------------------------------------
    # Run all collectors
    # ---------------------------------------------------------

    print("Starting OCI resource collection...")
    print()

    resources_by_service = manager.collect_all(
        oci_config
    )

    # ---------------------------------------------------------
    # Create output directory
    # ---------------------------------------------------------

    output_directory = Path(
        app_config["inventory"]["output_directory"]
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------
    # Generate report filename
    # ---------------------------------------------------------

    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    output_file = (
        output_directory
        / f"OCI_Inventory_{timestamp}.xlsx"
    )

    # ---------------------------------------------------------
    # Create Excel workbook
    # ---------------------------------------------------------

    create_inventory_workbook(
        resources_by_service=resources_by_service,
        output_file=str(output_file),
    )

    # ---------------------------------------------------------
    # Display summary
    # ---------------------------------------------------------

    print()
    print("=" * 70)
    print("OCI INVENTORY SUMMARY")
    print("=" * 70)

    total_resources = 0

    for service_name, resources in resources_by_service.items():

        count = len(resources)

        total_resources += count

        print(
            f"{service_name:<30} : {count}"
        )

    print("-" * 70)

    print(
        f"{'TOTAL RESOURCES':<30} : "
        f"{total_resources}"
    )

    print("=" * 70)

    print(
        f"Excel Report : {output_file}"
    )

    print("=" * 70)
    print("Inventory generation completed")
    print("=" * 70)


if __name__ == "__main__":
    main()
