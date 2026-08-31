from datetime import datetime
from pathlib import Path

import yaml

# ============================================================
# COMPUTE / STORAGE
# ============================================================

from collectors.compute import collect_compute
from collectors.block_volume import collect_block_volume
from collectors.boot_volume import collect_boot_volume

# ============================================================
# NETWORKING
# ============================================================

from collectors.vcn import collect_vcn
from collectors.subnet import collect_subnet
from collectors.network_security_group import (
    collect_network_security_groups
)
from collectors.route_table import (
    collect_route_tables
)
from collectors.security_list import (
    collect_security_lists
)
from collectors.dhcp_options import (
    collect_dhcp_options
)
from collectors.service_gateway import (
    collect_service_gateways
)
from collectors.local_peering_gateway import (
    collect_local_peering_gateways
)

# ============================================================
# LOAD BALANCER / FILE / OBJECT STORAGE
# ============================================================

from collectors.load_balancer import (
    collect_load_balancer
)

from collectors.file_storage import (
    collect_file_storage
)

from collectors.object_storage import (
    collect_object_storage
)

# ============================================================
# DATABASE
# ============================================================

from collectors.exacs import collect_exacs

from collectors.db_system import (
    collect_db_systems
)

from collectors.db_home import (
    collect_db_homes
)

from collectors.db_node import (
    collect_db_nodes
)

from collectors.pluggable_database import (
    collect_pluggable_databases
)

from collectors.postgresql import (
    collect_postgresql
)

from collectors.nosql import (
    collect_nosql
)

# ============================================================
# VAULT / KEYS / SECRETS / CERTIFICATES
# ============================================================

from collectors.vault import (
    collect_vault
)

from collectors.keys import (
    collect_key_management
)

from collectors.secrets import (
    collect_secrets
)

from collectors.certificates import (
    collect_certificates
)

from collectors.certificate_authority import (
    collect_certificate_authorities
)

# ============================================================
# NOTIFICATIONS / MONITORING / LOGGING / STREAMING
# ============================================================

from collectors.notifications import (
    collect_notifications
)

from collectors.alarms import (
    collect_alarms
)

from collectors.logging import (
    collect_logging
)

from collectors.streaming import (
    collect_streaming
)

# ============================================================
# NOTIFICATION SERVICE
# ============================================================

from collectors.ons_topic import (
    collect_ons_topics
)

from collectors.ons_subscription import (
    collect_ons_subscriptions
)

# ============================================================
# DNS
# ============================================================

from collectors.dns import (
    collect_dns
)

from collectors.dns_resolver import (
    collect_dns_resolvers
)

from collectors.dns_views import (
    collect_dns_views
)

# ============================================================
# IAM
# ============================================================

from collectors.policies import (
    collect_policies
)

# ============================================================
# DATA SAFE
# ============================================================

from collectors.data_safe_audit_policies import (
    collect_data_safe_audit_policies
)

from collectors.data_safe_audit_profiles import (
    collect_data_safe_audit_profiles
)

from collectors.data_safe_audit_trails import (
    collect_data_safe_audit_trails
)

from collectors.data_safe_private_endpoints import (
    collect_data_safe_private_endpoints
)

from collectors.data_safe_security_assessments import (
    collect_data_safe_security_assessments
)

from collectors.data_safe_sensitive_data_models import (
    collect_data_safe_sensitive_data_models
)

from collectors.data_safe_user_assessments import (
    collect_data_safe_user_assessments
)

# ============================================================
# MANAGER / EXCEL / AUTH
# ============================================================

from collectors.manager import (
    CollectorManager
)

from excel.workbook import (
    create_inventory_workbook
)

from utils.oci_auth import (
    get_oci_config
)


# ============================================================
# LOAD CONFIGURATION
# ============================================================

def load_config():
    """
    Load application configuration from config.yaml.
    """

    config_file = Path(
        "config.yaml"
    )

    with config_file.open(
        "r",
        encoding="utf-8",
    ) as file:

        return yaml.safe_load(
            file
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "=" * 70
    )

    print(
        "OCI Inventory Automation"
    )

    print(
        "=" * 70
    )

    # ========================================================
    # LOAD APPLICATION CONFIG
    # ========================================================

    app_config = load_config()

    # ========================================================
    # OCI AUTHENTICATION
    # ========================================================

    oci_config = get_oci_config()

    print(
        f"OCI Default Region : "
        f"{oci_config['region']}"
    )

    print(
        "Authentication     : OCI config file"
    )

    print()

    # ========================================================
    # COLLECTOR MANAGER
    # ========================================================

    manager = CollectorManager()

    # ========================================================
    # COMPUTE
    # ========================================================

    manager.register(
        "Compute",
        collect_compute,
    )

    # ========================================================
    # STORAGE
    # ========================================================

    manager.register(
        "Block Volume",
        collect_block_volume,
    )

    manager.register(
        "Boot Volume",
        collect_boot_volume,
    )

    # ========================================================
    # NETWORKING
    # ========================================================

    manager.register(
        "VCN",
        collect_vcn,
    )

    manager.register(
        "Subnet",
        collect_subnet,
    )

    manager.register(
        "Network Security Groups",
        collect_network_security_groups,
    )

    manager.register(
        "Route Tables",
        collect_route_tables,
    )

    manager.register(
        "Security Lists",
        collect_security_lists,
    )

    manager.register(
        "DHCP Options",
        collect_dhcp_options,
    )

    manager.register(
        "Service Gateways",
        collect_service_gateways,
    )

    manager.register(
        "Local Peering Gateways",
        collect_local_peering_gateways,
    )

    # ========================================================
    # LOAD BALANCER
    # ========================================================

    manager.register(
        "Load Balancer",
        collect_load_balancer,
    )

    # ========================================================
    # FILE STORAGE
    # ========================================================

    manager.register(
        "File Storage",
        collect_file_storage,
    )

    # ========================================================
    # OBJECT STORAGE
    # ========================================================

    manager.register(
        "Object Storage",
        collect_object_storage,
    )

    # ========================================================
    # EXADATA CLOUD SERVICE
    # ========================================================

    manager.register(
        "ExaCS",
        collect_exacs,
    )

    # ========================================================
    # DATABASE
    # ========================================================

    manager.register(
        "DB Systems",
        collect_db_systems,
    )

    manager.register(
        "DB Homes",
        collect_db_homes,
    )

    manager.register(
        "DB Nodes",
        collect_db_nodes,
    )

    manager.register(
        "Pluggable Databases",
        collect_pluggable_databases,
    )

    manager.register(
        "PostgreSQL",
        collect_postgresql,
    )

    manager.register(
        "NoSQL Database",
        collect_nosql,
    )

    # ========================================================
    # VAULT
    # ========================================================

    manager.register(
        "Vault",
        collect_vault,
    )

    # ========================================================
    # KEY MANAGEMENT
    # ========================================================

    manager.register(
        "Key Management",
        collect_key_management,
    )

    # ========================================================
    # SECRETS
    # ========================================================

    manager.register(
        "Secrets",
        collect_secrets,
    )

    # ========================================================
    # CERTIFICATES
    # ========================================================

    manager.register(
        "Certificates",
        collect_certificates,
    )

    manager.register(
        "Certificate Authorities",
        collect_certificate_authorities,
    )

    # ========================================================
    # NOTIFICATIONS
    # ========================================================

    manager.register(
        "Notifications",
        collect_notifications,
    )

    # ========================================================
    # ONS TOPICS
    # ========================================================

    manager.register(
        "ONS Topics",
        collect_ons_topics,
    )

    # ========================================================
    # ONS SUBSCRIPTIONS
    # ========================================================

    manager.register(
        "ONS Subscriptions",
        collect_ons_subscriptions,
    )

    # ========================================================
    # MONITORING / ALARMS
    # ========================================================

    manager.register(
        "Monitoring",
        collect_alarms,
    )

    # ========================================================
    # LOGGING
    # ========================================================

    manager.register(
        "Logging",
        collect_logging,
    )

    # ========================================================
    # STREAMING
    # ========================================================

    manager.register(
        "Streaming",
        collect_streaming,
    )

    # ========================================================
    # DNS
    # ========================================================

    manager.register(
        "DNS",
        collect_dns,
    )

    manager.register(
        "DNS Resolvers",
        collect_dns_resolvers,
    )

    manager.register(
        "DNS Views",
        collect_dns_views,
    )

    # ========================================================
    # IAM POLICIES
    # ========================================================

    manager.register(
        "Policies",
        collect_policies,
    )

    # ========================================================
    # DATA SAFE
    # ========================================================

    manager.register(
        "Data Safe Audit Policies",
        collect_data_safe_audit_policies,
    )

    manager.register(
        "Data Safe Audit Profiles",
        collect_data_safe_audit_profiles,
    )

    manager.register(
        "Data Safe Audit Trails",
        collect_data_safe_audit_trails,
    )

    manager.register(
        "Data Safe Private Endpoints",
        collect_data_safe_private_endpoints,
    )

    manager.register(
        "Data Safe Security Assessments",
        collect_data_safe_security_assessments,
    )

    manager.register(
        "Data Safe Sensitive Data Models",
        collect_data_safe_sensitive_data_models,
    )

    manager.register(
        "Data Safe User Assessments",
        collect_data_safe_user_assessments,
    )

    # ========================================================
    # RUN ALL COLLECTORS
    # ========================================================

    print(
        "Starting OCI resource collection..."
    )

    print()

    resources_by_service = (
        manager.collect_all(
            oci_config
        )
    )

    # ========================================================
    # OUTPUT DIRECTORY
    # ========================================================

    output_directory = Path(
        app_config[
            "inventory"
        ][
            "output_directory"
        ]
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ========================================================
    # REPORT FILENAME
    # ========================================================

    timestamp = (
        datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )
    )

    output_file = (
        output_directory
        / f"OCI_Inventory_{timestamp}.xlsx"
    )

    # ========================================================
    # CREATE EXCEL WORKBOOK
    # ========================================================

    create_inventory_workbook(
        resources_by_service=(
            resources_by_service
        ),
        output_file=str(
            output_file
        ),
    )

    # ========================================================
    # DISPLAY SUMMARY
    # ========================================================

    print()

    print(
        "=" * 70
    )

    print(
        "OCI INVENTORY SUMMARY"
    )

    print(
        "=" * 70
    )

    total_resources = 0

    for (
        service_name,
        resources,
    ) in resources_by_service.items():

        count = len(
            resources
        )

        total_resources += count

        print(
            f"{service_name:<35} : "
            f"{count}"
        )

    print(
        "-" * 70
    )

    print(
        f"{'TOTAL RESOURCES':<35} : "
        f"{total_resources}"
    )

    print(
        "=" * 70
    )

    print(
        f"Excel Report : "
        f"{output_file}"
    )

    print(
        "=" * 70
    )

    print(
        "Inventory generation completed"
    )

    print(
        "=" * 70
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
