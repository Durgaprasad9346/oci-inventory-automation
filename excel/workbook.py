from collections import Counter
from datetime import datetime, date
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo


# ============================================================
# GENERAL HELPERS
# ============================================================

def _safe_get(obj, key, default=""):
    """
    Safely read a value from either a dictionary or an object.
    """

    if obj is None:
        return default

    try:
        if isinstance(obj, dict):
            return obj.get(key, default)

        return getattr(obj, key, default)

    except Exception:
        return default


def _first_value(obj, *keys, default=""):
    """
    Return the first non-empty value from the supplied keys.
    """

    for key in keys:
        value = _safe_get(obj, key, None)

        if value is not None and value != "":
            return value

    return default


def _to_excel_value(value):
    """
    Convert OCI SDK values into Excel-safe values.

    Handles:
      - datetime
      - date
      - dictionaries
      - lists
      - tuples
      - OCI SDK objects
      - primitive values
    """

    if value is None:
        return ""

    if isinstance(value, datetime):
        # Excel does not support timezone-aware datetimes.
        if value.tzinfo is not None:
            value = value.replace(tzinfo=None)

        return value

    if isinstance(value, date):
        return value

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, dict):

        parts = []

        for key, item in value.items():

            converted = _to_excel_value(item)

            if isinstance(converted, (dict, list, tuple)):
                converted = str(converted)

            parts.append(
                f"{key}: {converted}"
            )

        return "\n".join(parts)

    if isinstance(value, (list, tuple, set)):

        converted_items = []

        for item in value:

            converted = _to_excel_value(item)

            if isinstance(converted, (dict, list, tuple)):
                converted = str(converted)

            converted_items.append(
                str(converted)
            )

        return "\n".join(converted_items)

    # OCI SDK model objects
    try:

        if hasattr(value, "to_dict"):

            return _to_excel_value(
                value.to_dict()
            )

    except Exception:
        pass

    try:

        if hasattr(value, "__dict__"):

            data = {}

            for key, item in vars(value).items():

                if key.startswith("_"):
                    continue

                data[key] = item

            return _to_excel_value(data)

    except Exception:
        pass

    return str(value)


def _resource_value(resource, key, default=""):
    """
    Read a resource property.

    Checks:
      1. Direct resource property
      2. details dictionary
      3. details object
    """

    value = _safe_get(
        resource,
        key,
        None,
    )

    if value is not None and value != "":
        return value

    details = _safe_get(
        resource,
        "details",
        None,
    )

    if details is not None:

        value = _safe_get(
            details,
            key,
            None,
        )

        if value is not None and value != "":
            return value

    return default


def _normalize_resource(resource):
    """
    Convert a resource into a standard dictionary.
    """

    if isinstance(resource, dict):

        result = dict(resource)

    else:

        result = {}

        try:

            for key in (
                "service",
                "resource_type",
                "name",
                "display_name",
                "ocid",
                "id",
                "compartment_id",
                "compartment_name",
                "region",
                "state",
                "lifecycle_state",
                "lifecycle_details",
                "time_created",
                "defined_tags",
                "freeform_tags",
                "details",
            ):

                value = _safe_get(
                    resource,
                    key,
                    None,
                )

                if value is not None:
                    result[key] = value

        except Exception:
            pass

    details = result.get(
        "details"
    )

    if details:

        if isinstance(details, dict):
            for key, value in details.items():
                if key not in result or result[key] in (
                    None,
                    "",
                ):
                    result[key] = value

        else:

            try:

                for key, value in vars(details).items():

                    if key.startswith("_"):
                        continue

                    if key not in result or result[key] in (
                        None,
                        "",
                    ):
                        result[key] = value

            except Exception:
                pass

    return result


# ============================================================
# TAG HELPERS
# ============================================================

def _format_tags(resource):
    """
    Return Defined Tags and Freeform Tags separately.
    """

    defined_tags = _resource_value(
        resource,
        "defined_tags",
        {},
    )

    freeform_tags = _resource_value(
        resource,
        "freeform_tags",
        {},
    )

    return (
        _to_excel_value(defined_tags),
        _to_excel_value(freeform_tags),
    )


# ============================================================
# RESOURCE NORMALIZATION
# ============================================================

def _normalize_resources(resources_by_service):
    """
    Flatten resources_by_service into one resource list.

    Supports:

        {
            "Compute": [resource1, resource2],
            "Block Volume": [resource3]
        }

    and also a plain list.
    """

    resources = []

    if resources_by_service is None:
        return resources

    if isinstance(resources_by_service, dict):

        for service_name, service_resources in (
            resources_by_service.items()
        ):

            if service_resources is None:
                continue

            if not isinstance(
                service_resources,
                (list, tuple, set),
            ):
                service_resources = [
                    service_resources
                ]

            for resource in service_resources:

                if resource is None:
                    continue

                normalized = _normalize_resource(
                    resource
                )

                if not normalized.get("service"):
                    normalized["service"] = (
                        service_name
                    )

                resources.append(
                    normalized
                )

        return resources

    if isinstance(
        resources_by_service,
        (list, tuple, set),
    ):

        for resource in resources_by_service:

            if resource is None:
                continue

            resources.append(
                _normalize_resource(resource)
            )

    return resources


# ============================================================
# SERVICE NORMALIZATION
# ============================================================

SERVICE_ALIASES = {

    "Compute": "Compute",
    "Instance": "Compute",
    "Instances": "Compute",

    "Block Volume": "Block Volume",
    "Block Volumes": "Block Volume",

    "Boot Volume": "Boot Volume",
    "Boot Volumes": "Boot Volume",

    "Object Storage": "Object Storage",
    "Bucket": "Object Storage",
    "Buckets": "Object Storage",

    "File Storage": "File Storage",
    "File System": "File Storage",
    "File Systems": "File Storage",

    "VCN": "VCN",
    "Virtual Cloud Network": "VCN",
    "Virtual Cloud Networks": "VCN",

    "Subnet": "Subnet",
    "Subnets": "Subnet",

    "Network Security Group":
        "Network Security Group",
    "Network Security Groups":
        "Network Security Group",
    "NSG": "Network Security Group",

    "Load Balancer": "Load Balancer",
    "Load Balancers": "Load Balancer",

    "Local Peering Gateway":
        "Local Peering Gateway",
    "Local Peering Gateways":
        "Local Peering Gateway",

    "Route Table": "Route Table",
    "Route Tables": "Route Table",

    "DHCP Options": "DHCP Options",

    "DNS Resolver": "DNS Resolver",
    "DNS View": "DNS View",

    "DB System": "DB Systems",
    "DB Systems": "DB Systems",

    "DB Home": "DB Home",
    "DB Homes": "DB Home",

    "DB Node": "DB Node",
    "DB Nodes": "DB Node",

    "ExaCS": "ExaCS",

    "NoSQL Database":
        "NoSQL Database",
    "NoSQL Databases":
        "NoSQL Database",

    "Key Management":
        "Key Management",
    "Key": "Key",

    "Vault": "Vault",
    "Vaults": "Vault",

    "Secret": "Secrets",
    "Secrets": "Secrets",

    "Notification Topic":
        "Notifications",
    "Notification Topics":
        "Notifications",
    "Notifications":
        "Notifications",

    "Stream": "Streaming",
    "Streaming": "Streaming",

    "Log": "Logging",
    "Logs": "Logging",
    "Logging": "Logging",

    "Monitoring": "Monitoring",

    "Alarm": "Alarms",
    "Alarms": "Alarms",

    "DNS": "DNS",

    "Compartment": "Compartment",
    "Compartments": "Compartment",

    "PostgreSQL": "PostgreSQL",

    "Pluggable Database":
        "Pluggable Database",

    "DB System Node":
        "DB Node",

    "Certificate": "Certificates",
    "Certificates": "Certificates",

    "Certificate Authority":
        "Certificate Authorities",
}


def _normalize_service(service, resource_type=""):

    service = str(
        service or ""
    ).strip()

    resource_type = str(
        resource_type or ""
    ).strip()

    normalized = SERVICE_ALIASES.get(
        service
    )

    if normalized:
        return normalized

    normalized = SERVICE_ALIASES.get(
        resource_type
    )

    if normalized:
        return normalized

    return service or resource_type or "Unknown"


# ============================================================
# SERVICE-SPECIFIC COLUMNS
# ============================================================

COMMON_COLUMNS = [

    "S.No",
    "Service",
    "Resource Type",
    "Name",
    "OCID",
    "Region",
    "Compartment Name",
    "Compartment OCID",
    "Lifecycle State",
    "Lifecycle Details",
    "Creation Date",
    "Defined Tags",
    "Freeform Tags",
]


SERVICE_COLUMNS = {

    "Compute": [

        "Shape",
        "OCPU",
        "Memory (GB)",
        "VCPU",

        "Private IP",
        "Public IP",
        "IPv6 Address",

        "VNIC OCID",
        "MAC Address",

        "Subnet Name",
        "Subnet OCID",

        "Hostname",
        "Hostname Label",

        "Image OCID",

        "Availability Domain",
        "Fault Domain",

        "Boot Volume OCID",

        "Launch Mode",
        "Baseline OCPU Utilization",
        "Processor Description",

        "Private DNS Name",
        "VLAN Tag",
        "NIC Index",

    ],

    "Block Volume": [

        "Size (GB)",
        "Volume Type",
        "VPUs/GB",

        "Availability Domain",

        "IS Read Only",
        "Is Shareable",

        "Volume Group OCID",

        "Source Volume OCID",
        "Source Boot Volume OCID",
        "Source Type",

        "KMS Key OCID",

        "Backup Policy OCID",

        "Replica Information",

    ],

    "Boot Volume": [

        "Size (GB)",
        "Volume Type",
        "VPUs/GB",

        "Availability Domain",

        "IS Read Only",
        "Is Shareable",

        "Volume Group OCID",

        "Source Volume OCID",
        "Source Boot Volume OCID",
        "Source Type",

        "KMS Key OCID",

        "Backup Policy OCID",

        "Replica Information",

    ],

    "Object Storage": [

        "Bucket Name",
        "Namespace",

        "Storage Tier",

        "Object Count",
        "Stored Size (Bytes)",
        "Stored Size (GB)",

        "Versioning",
        "Object Events Enabled",

        "Public Access Type",

        "Auto Tiering",
        "ETag",

        "KMS Key OCID",

    ],

    "File Storage": [

        "File System OCID",
        "Size (GB)",
        "Metered Bytes",
        "Metered Size (GB)",

        "Availability Domain",

        "Mount Target OCID",
        "Mount Target Name",

        "Export Set OCID",

        "Filesystem Snapshot Policy",

        "Replication",

        "KMS Key OCID",

        "Is Clone",
        "Source Snapshot OCID",

    ],

    "VCN": [

        "CIDR Block",
        "IPv6 CIDR Block",
        "DNS Label",

        "Default Route Table OCID",
        "Default Security List OCID",
        "Default DHCP Options OCID",

        "IPv6 Enabled",

    ],

    "Subnet": [

        "CIDR Block",
        "IPv6 CIDR Block",

        "Availability Domain",

        "DNS Label",

        "Route Table OCID",
        "Security List OCIDs",
        "DHCP Options OCID",

        "Prohibit Public IP",
        "IPv6 Enabled",

    ],

    "Network Security Group": [

        "VCN OCID",
        "NSG OCID",

        "Security Rules",

    ],

    "Route Table": [

        "VCN OCID",
        "Route Rules",

    ],

    "DHCP Options": [

        "VCN OCID",
        "Domain Name Type",
        "Search Domain",
        "DNS Servers",

    ],

    "DNS Resolver": [

        "VCN OCID",
        "Endpoint Type",
        "Endpoint IP",
        "Subnet OCID",
        "Hostname",

    ],

    "DNS View": [

        "Scope",
        "Is Protected",

    ],

    "Load Balancer": [

        "Shape",
        "Shape Details",

        "IP Address",
        "Private IP",
        "Public IP",

        "Subnet OCIDs",

        "Backend Sets",
        "Listeners",

        "Is Private",
        "Bandwidth",

    ],

    "Local Peering Gateway": [

        "VCN OCID",
        "Peering Status",
        "Peer LPG OCID",

    ],

    "DB Systems": [

        "DB System OCID",
        "Shape",
        "CPU Core Count",

        "Storage Size (GB)",

        "Database Edition",
        "Database Version",

        "DB Home OCID",
        "DB Node Count",

        "Availability Domain",

        "Subnet OCID",
        "VPC User Name",

        "License Model",

    ],

    "DB Home": [

        "DB System OCID",
        "DB Version",
        "DB Home Version",
        "Database Software",

    ],

    "DB Node": [

        "DB System OCID",
        "DB Home OCID",
        "Hostname",
        "IP Address",

        "Availability Domain",

        "CPU Core Count",
        "Memory (GB)",

    ],

    "ExaCS": [

        "Shape",
        "CPU Cores",
        "Storage Size (GB)",

        "Availability Domain",

        "Subnet OCID",

        "DB Nodes",
        "DB Homes",

    ],

    "NoSQL Database": [

        "Table Name",
        "Compartment OCID",

        "Table State",

        "Table Limits",
        "Max Read Units",
        "Max Write Units",
        "Max Storage (GB)",

        "Schema",

        "DDL Statement",

    ],

    "Key Management": [

        "Key OCID",
        "Key State",
        "Key Shape",
        "Algorithm",
        "Length",
        "Protection Mode",

        "Vault OCID",

    ],

    "Vault": [

        "Vault Type",
        "Vault State",
        "Vault Endpoint",
        "Management Endpoint",

    ],

    "Secrets": [

        "Secret OCID",
        "Secret State",

        "Vault OCID",

        "Key OCID",

        "Secret Version",

        "Time of Expiry",
        "Time Of Rotation",

    ],

    "Notifications": [

        "Topic OCID",
        "Topic Name",
        "Endpoint",

        "Protocol",

        "Subscription State",

    ],

    "Streaming": [

        "Stream OCID",
        "Stream Name",

        "Partitions",

        "Retention Hours",

        "Messages Endpoint",

    ],

    "Logging": [

        "Log OCID",
        "Log Group OCID",

        "Log Type",
        "Source",

        "Is Enabled",

        "Retention Duration",

    ],

    "Monitoring": [

        "Metric Namespace",
        "Metric Name",
        "Dimensions",

    ],

    "Alarms": [

        "Alarm OCID",
        "Severity",
        "Metric Namespace",
        "Metric Name",

        "Query",

        "Is Enabled",

        "Destinations",

    ],

    "Certificates": [

        "Certificate OCID",
        "Certificate Authority OCID",

        "Certificate Type",
        "Certificate State",

        "Time Of Expiry",

    ],

    "Certificate Authorities": [

        "Certificate Authority OCID",
        "CA Type",
        "CA State",

        "Time Of Expiry",

    ],

    "PostgreSQL": [

        "PostgreSQL Version",
        "Shape",
        "CPU Cores",
        "Memory (GB)",
        "Storage (GB)",

        "Subnet OCID",

        "Private IP",
        "Public IP",

    ],

    "Pluggable Database": [

        "DB System OCID",
        "Container Database OCID",

        "DB Name",
        "DB Version",

        "State",

    ],
}


# ============================================================
# FIELD ALIASES
# ============================================================

FIELD_ALIASES = {

    "Name": [
        "name",
        "display_name",
        "bucket_name",
        "table_name",
        "stream_name",
    ],

    "OCID": [
        "ocid",
        "id",
    ],

    "Region": [
        "region",
    ],

    "Compartment Name": [
        "compartment_name",
    ],

    "Compartment OCID": [
        "compartment_id",
    ],

    "Lifecycle State": [
        "state",
        "lifecycle_state",
    ],

    "Lifecycle Details": [
        "lifecycle_details",
    ],

    "Creation Date": [
        "time_created",
        "created_time",
        "creation_date",
    ],

    "Shape": [
        "shape",
        "shape_name",
    ],

    "OCPU": [
        "ocpu",
        "ocpus",
    ],

    "Memory (GB)": [
        "memory_gb",
        "memory_in_gbs",
        "memory",
    ],

    "VCPU": [
        "vcpus",
        "vcpu",
    ],

    "Private IP": [
        "private_ip",
        "private_ip_address",
    ],

    "Public IP": [
        "public_ip",
        "public_ip_address",
    ],

    "IPv6 Address": [
        "ipv6_address",
        "ipv6",
    ],

    "VNIC OCID": [
        "vnic_id",
        "vnic_ocid",
    ],

    "MAC Address": [
        "mac_address",
    ],

    "Subnet Name": [
        "subnet_name",
    ],

    "Subnet OCID": [
        "subnet_id",
        "subnet_ocid",
    ],

    "Hostname": [
        "hostname",
        "hostname_label",
    ],

    "Hostname Label": [
        "hostname_label",
    ],

    "Image OCID": [
        "image_id",
        "image_ocid",
    ],

    "Availability Domain": [
        "availability_domain",
    ],

    "Fault Domain": [
        "fault_domain",
    ],

    "Boot Volume OCID": [
        "boot_volume_id",
        "boot_volume_ocid",
    ],

    "Launch Mode": [
        "launch_mode",
    ],

    "Baseline OCPU Utilization": [
        "baseline_ocpu_utilization",
    ],

    "Processor Description": [
        "processor_description",
    ],

    "Private DNS Name": [
        "private_dns_name",
    ],

    "VLAN Tag": [
        "vlan_tag",
    ],

    "NIC Index": [
        "nic_index",
    ],

    "Size (GB)": [
        "size_gb",
        "size_in_gbs",
        "size",
        "volume_size_gb",
    ],

    "Volume Type": [
        "volume_type",
    ],

    "VPUs/GB": [
        "vpus_per_gb",
        "vpus",
    ],

    "Volume Group OCID": [
        "volume_group_id",
        "volume_group_ocid",
    ],

    "Source Volume OCID": [
        "source_volume_id",
        "source_volume_ocid",
    ],

    "Source Boot Volume OCID": [
        "source_boot_volume_id",
        "source_boot_volume_ocid",
    ],

    "Source Type": [
        "source_type",
    ],

    "KMS Key OCID": [
        "kms_key_id",
        "kms_key_ocid",
        "key_id",
    ],

    "Backup Policy OCID": [
        "backup_policy_id",
        "backup_policy_ocid",
    ],

    "Bucket Name": [
        "bucket_name",
        "name",
    ],

    "Namespace": [
        "namespace",
    ],

    "Storage Tier": [
        "storage_tier",
    ],

    "Object Count": [
        "object_count",
        "objects_count",
    ],

    "Stored Size (Bytes)": [
        "stored_size_bytes",
        "size_bytes",
        "approximate_size_in_bytes",
        "total_size_bytes",
    ],

    "Stored Size (GB)": [
        "stored_size_gb",
        "size_gb",
        "approximate_size_in_gb",
    ],

    "Versioning": [
        "versioning",
        "versioning_state",
    ],

    "Object Events Enabled": [
        "object_events_enabled",
    ],

    "Public Access Type": [
        "public_access_type",
    ],

    "Auto Tiering": [
        "auto_tiering",
    ],

    "ETag": [
        "etag",
    ],

    "File System OCID": [
        "file_system_id",
        "file_system_ocid",
    ],

    "Metered Bytes": [
        "metered_bytes",
        "metered_size_bytes",
    ],

    "Metered Size (GB)": [
        "metered_size_gb",
        "metered_gb",
    ],

    "Mount Target OCID": [
        "mount_target_id",
        "mount_target_ocid",
    ],

    "Mount Target Name": [
        "mount_target_name",
    ],

    "Export Set OCID": [
        "export_set_id",
        "export_set_ocid",
    ],

    "CIDR Block": [
        "cidr_block",
        "cidr",
    ],

    "IPv6 CIDR Block": [
        "ipv6_cidr_block",
        "ipv6_cidr_blocks",
    ],

    "DNS Label": [
        "dns_label",
    ],

    "VCN OCID": [
        "vcn_id",
        "vcn_ocid",
    ],

    "Route Table OCID": [
        "route_table_id",
        "route_table_ocid",
    ],

    "Security List OCIDs": [
        "security_list_ids",
        "security_list_ocids",
    ],

    "DHCP Options OCID": [
        "dhcp_options_id",
        "dhcp_options_ocid",
    ],

    "Prohibit Public IP": [
        "prohibit_public_ip",
    ],

    "IPv6 Enabled": [
        "ipv6_enabled",
    ],

    "DB System OCID": [
        "db_system_id",
        "db_system_ocid",
    ],

    "DB Home OCID": [
        "db_home_id",
        "db_home_ocid",
    ],

    "CPU Core Count": [
        "cpu_core_count",
        "cpu_cores",
        "ocpus",
        "ocpu",
    ],

    "Storage Size (GB)": [
        "storage_size_gb",
        "storage_gb",
    ],

    "Database Edition": [
        "database_edition",
        "db_edition",
    ],

    "Database Version": [
        "database_version",
        "db_version",
    ],

    "DB Node Count": [
        "db_node_count",
        "node_count",
    ],

    "License Model": [
        "license_model",
    ],

    "DB Version": [
        "db_version",
        "database_version",
    ],

    "DB Home Version": [
        "db_home_version",
    ],

    "Database Software": [
        "database_software",
    ],

    "Hostname": [
        "hostname",
    ],

    "IP Address": [
        "ip_address",
        "private_ip",
        "public_ip",
    ],

    "Memory (GB)": [
        "memory_gb",
        "memory_in_gbs",
    ],

    "Partitions": [
        "partitions",
    ],

    "Retention Hours": [
        "retention_hours",
    ],

    "Metric Namespace": [
        "metric_namespace",
        "namespace",
    ],

    "Metric Name": [
        "metric_name",
        "name",
    ],

    "Dimensions": [
        "dimensions",
    ],

    "Severity": [
        "severity",
    ],

    "Query": [
        "query",
    ],

    "Is Enabled": [
        "is_enabled",
        "enabled",
    ],

    "Destinations": [
        "destinations",
    ],

    "Certificate OCID": [
        "certificate_id",
        "certificate_ocid",
    ],

    "Certificate Authority OCID": [
        "certificate_authority_id",
        "certificate_authority_ocid",
    ],

    "Certificate Type": [
        "certificate_type",
    ],

    "Certificate State": [
        "certificate_state",
        "state",
    ],

    "Time Of Expiry": [
        "time_of_expiry",
        "expiry_date",
    ],

    "PostgreSQL Version": [
        "postgresql_version",
        "version",
    ],

    "Table Name": [
        "table_name",
        "name",
    ],

    "Table State": [
        "table_state",
        "state",
    ],

    "Max Read Units": [
        "max_read_units",
    ],

    "Max Write Units": [
        "max_write_units",
    ],

    "Max Storage (GB)": [
        "max_storage_gb",
    ],

    "Schema": [
        "schema",
    ],

    "DDL Statement": [
        "ddl_statement",
    ],
}


# ============================================================
# RESOURCE DETAIL VALUE
# ============================================================

def _get_column_value(resource, column):

    aliases = FIELD_ALIASES.get(
        column,
        [],
    )

    if aliases:

        for key in aliases:

            value = _resource_value(
                resource,
                key,
                None,
            )

            if value is not None and value != "":
                return value

    # Generic normalized key
    key = (
        column
        .lower()
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("/", "_")
    )

    value = _resource_value(
        resource,
        key,
        "",
    )

    return value


# ============================================================
# SUMMARY SHEET
# ============================================================

def write_summary_sheet(ws, resources):

    # Clear sheet
    for row in ws.iter_rows():

        for cell in row:
            cell.value = None

    ws.title = "Summary"

    # ---------------------------------------------------------
    # TITLE
    # ---------------------------------------------------------

    ws["A1"] = "OCI Inventory Summary"

    ws["A1"].font = Font(
        bold=True,
        size=16,
    )

    # ---------------------------------------------------------
    # REPORT DATE
    # ---------------------------------------------------------

    ws["A3"] = "Report Generated"

    ws["A3"].font = Font(
        bold=True,
    )

    ws["B3"] = datetime.now().replace(
        tzinfo=None
    )

    ws["B3"].number_format = (
        "yyyy-mm-dd hh:mm:ss"
    )

    # ---------------------------------------------------------
    # NORMALIZE
    # ---------------------------------------------------------

    normalized = []

    for resource in resources:

        service = str(
            resource.get(
                "service",
                ""
            ) or ""
        ).strip()

        resource_type = str(
            resource.get(
                "resource_type",
                ""
            ) or ""
        ).strip()

        normalized_service = _normalize_service(
            service,
            resource_type,
        )

        if normalized_service:

            normalized.append(
                (
                    normalized_service,
                    resource_type,
                )
            )

    # ---------------------------------------------------------
    # COUNTS
    # ---------------------------------------------------------

    service_counts = Counter()

    for service, resource_type in normalized:

        service_counts[service] += 1

    total_resources = sum(
        service_counts.values()
    )

    ws["A5"] = "Total Resources"

    ws["A5"].font = Font(
        bold=True,
    )

    ws["B5"] = total_resources

    ws["B5"].font = Font(
        bold=True,
        size=12,
    )

    # ---------------------------------------------------------
    # TABLE
    # ---------------------------------------------------------

    header_row = 7

    headers = [
        "S.No",
        "Service Name",
        "Description",
        "Resource Count",
    ]

    for col, header in enumerate(
        headers,
        start=1,
    ):

        cell = ws.cell(
            row=header_row,
            column=col,
            value=header,
        )

        cell.font = Font(
            bold=True,
        )

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )

    descriptions = {

        "Compute":
            "Compute instances",

        "Block Volume":
            "Block volumes",

        "Boot Volume":
            "Boot volumes",

        "File Storage":
            "File systems",

        "Object Storage":
            "Object Storage buckets",

        "VCN":
            "Virtual Cloud Networks",

        "Subnet":
            "Subnets",

        "Network Security Group":
            "Network Security Groups",

        "Route Table":
            "Route tables",

        "DHCP Options":
            "DHCP options",

        "DNS Resolver":
            "DNS resolvers",

        "DNS View":
            "DNS views",

        "Local Peering Gateway":
            "Local peering gateways",

        "Load Balancer":
            "Load balancers",

        "DB Systems":
            "Database systems",

        "DB Home":
            "Database homes",

        "DB Node":
            "Database nodes",

        "ExaCS":
            "Exadata Cloud Service",

        "NoSQL Database":
            "NoSQL databases",

        "Key":
            "Encryption keys",

        "Key Management":
            "Key Management",

        "Vault":
            "Vaults",

        "Secrets":
            "Vault secrets",

        "Notifications":
            "Notification topics/subscriptions",

        "Streaming":
            "Streaming resources",

        "Logging":
            "Logging resources",

        "Monitoring":
            "Monitoring resources",

        "Alarms":
            "Monitoring alarms",

        "Certificates":
            "Certificates",

        "Certificate Authorities":
            "Certificate authorities",

        "PostgreSQL":
            "PostgreSQL databases",

        "Pluggable Database":
            "Pluggable databases",
    }

    preferred_order = [

        "Compartment",

        "Compute",
        "Block Volume",
        "Boot Volume",

        "File Storage",
        "Object Storage",

        "VCN",
        "Subnet",
        "Network Security Group",

        "Route Table",
        "DHCP Options",

        "DNS Resolver",
        "DNS View",

        "Local Peering Gateway",
        "Load Balancer",

        "DB Systems",
        "DB Home",
        "DB Node",

        "ExaCS",
        "PostgreSQL",
        "Pluggable Database",

        "NoSQL Database",

        "Key Management",
        "Key",
        "Vault",
        "Secrets",

        "Notifications",
        "Streaming",

        "Logging",
        "Monitoring",
        "Alarms",

        "Certificates",
        "Certificate Authorities",

        "DNS",
    ]

    ordered_services = []

    for service in preferred_order:

        if service in service_counts:
            ordered_services.append(
                service
            )

    for service in sorted(
        service_counts.keys()
    ):

        if service not in ordered_services:
            ordered_services.append(
                service
            )

    row = header_row + 1

    serial = 1

    for service in ordered_services:

        ws.cell(
            row=row,
            column=1,
            value=serial,
        )

        ws.cell(
            row=row,
            column=2,
            value=service,
        )

        ws.cell(
            row=row,
            column=3,
            value=descriptions.get(
                service,
                service,
            ),
        )

        ws.cell(
            row=row,
            column=4,
            value=service_counts[
                service
            ],
        )

        serial += 1
        row += 1

    # ---------------------------------------------------------
    # FORMATTING
    # ---------------------------------------------------------

    ws.column_dimensions["A"].width = 10
    ws.column_dimensions["B"].width = 32
    ws.column_dimensions["C"].width = 42
    ws.column_dimensions["D"].width = 18

    ws.freeze_panes = "A8"

    if row > header_row + 1:

        ws.auto_filter.ref = (
            f"A{header_row}:D{row - 1}"
        )

    return total_resources


# ============================================================
# CREATE RESOURCE SHEET
# ============================================================

def write_resource_sheet(
    ws,
    service,
    resources,
):

    ws.title = service[:31]

    columns = (
        COMMON_COLUMNS
        + SERVICE_COLUMNS.get(
            service,
            [],
        )
    )

    # ---------------------------------------------------------
    # HEADER
    # ---------------------------------------------------------

    for col_index, header in enumerate(
        columns,
        start=1,
    ):

        cell = ws.cell(
            row=1,
            column=col_index,
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

    # ---------------------------------------------------------
    # DATA
    # ---------------------------------------------------------

    for index, resource in enumerate(
        resources,
        start=1,
    ):

        row_number = index + 1

        normalized = _normalize_resource(
            resource
        )

        defined_tags, freeform_tags = (
            _format_tags(normalized)
        )

        for col_index, header in enumerate(
            columns,
            start=1,
        ):

            value = ""

            # -------------------------------------------------
            # COMMON
            # -------------------------------------------------

            if header == "S.No":

                value = index

            elif header == "Service":

                value = _normalize_service(
                    normalized.get(
                        "service",
                        service,
                    ),
                    normalized.get(
                        "resource_type",
                        "",
                    ),
                )

            elif header == "Resource Type":

                value = normalized.get(
                    "resource_type",
                    "",
                )

            elif header == "Name":

                value = _first_value(
                    normalized,
                    "name",
                    "display_name",
                    "bucket_name",
                    "table_name",
                    "stream_name",
                    default="",
                )

            elif header == "OCID":

                value = _first_value(
                    normalized,
                    "ocid",
                    "id",
                    default="",
                )

            elif header == "Region":

                value = normalized.get(
                    "region",
                    "",
                )

            elif header == "Compartment Name":

                value = normalized.get(
                    "compartment_name",
                    "",
                )

            elif header == "Compartment OCID":

                value = normalized.get(
                    "compartment_id",
                    "",
                )

            elif header == "Lifecycle State":

                value = _first_value(
                    normalized,
                    "state",
                    "lifecycle_state",
                    default="",
                )

            elif header == "Lifecycle Details":

                value = normalized.get(
                    "lifecycle_details",
                    "",
                )

            elif header == "Creation Date":

                value = _first_value(
                    normalized,
                    "time_created",
                    "created_time",
                    "creation_date",
                    default="",
                )

            elif header == "Defined Tags":

                value = defined_tags

            elif header == "Freeform Tags":

                value = freeform_tags

            # -------------------------------------------------
            # SERVICE-SPECIFIC
            # -------------------------------------------------

            else:

                value = _get_column_value(
                    normalized,
                    header,
                )

            # -------------------------------------------------
            # SPECIAL CALCULATIONS
            # -------------------------------------------------

            if (
                header == "Stored Size (GB)"
                and (
                    value is None
                    or value == ""
                )
            ):

                bytes_value = _get_column_value(
                    normalized,
                    "Stored Size (Bytes)",
                )

                try:

                    if bytes_value not in (
                        None,
                        "",
                    ):

                        value = (
                            float(bytes_value)
                            / (
                                1024 ** 3
                            )
                        )

                except Exception:
                    value = ""

            if (
                header == "Metered Size (GB)"
                and (
                    value is None
                    or value == ""
                )
            ):

                bytes_value = _get_column_value(
                    normalized,
                    "Metered Bytes",
                )

                try:

                    if bytes_value not in (
                        None,
                        "",
                    ):

                        value = (
                            float(bytes_value)
                            / (
                                1024 ** 3
                            )
                        )

                except Exception:
                    value = ""

            if (
                header == "Memory (GB)"
                and (
                    value is None
                    or value == ""
                )
            ):

                value = _first_value(
                    normalized,
                    "memory_in_gbs",
                    "memory_gb",
                    "memory",
                    default="",
                )

            if (
                header == "OCPU"
                and (
                    value is None
                    or value == ""
                )
            ):

                value = _first_value(
                    normalized,
                    "ocpus",
                    "ocpu",
                    default="",
                )

            if (
                header == "Size (GB)"
                and (
                    value is None
                    or value == ""
                )
            ):

                value = _first_value(
                    normalized,
                    "size_in_gbs",
                    "size_gb",
                    "size",
                    default="",
                )

            # -------------------------------------------------
            # SAFE EXCEL CONVERSION
            # -------------------------------------------------

            value = _to_excel_value(
                value
            )

            # -------------------------------------------------
            # WRITE CELL
            # -------------------------------------------------

            cell = ws.cell(
                row=row_number,
                column=col_index,
                value=value,
            )

            cell.alignment = Alignment(
                vertical="top",
                wrap_text=True,
            )

            # Date formatting
            if header == "Creation Date":

                cell.number_format = (
                    "yyyy-mm-dd hh:mm:ss"
                )

    # ---------------------------------------------------------
    # FREEZE
    # ---------------------------------------------------------

    ws.freeze_panes = "A2"

    # ---------------------------------------------------------
    # FILTER
    # ---------------------------------------------------------

    if len(resources) > 0:

        ws.auto_filter.ref = (
            f"A1:{get_column_letter(len(columns))}"
            f"{len(resources) + 1}"
        )

    # ---------------------------------------------------------
    # WIDTH
    # ---------------------------------------------------------

    for col_index, header in enumerate(
        columns,
        start=1,
    ):

        width = 18

        if header in (
            "Name",
            "OCID",
            "Compartment OCID",
            "Subnet OCID",
            "VNIC OCID",
            "Image OCID",
            "Boot Volume OCID",
            "Defined Tags",
            "Freeform Tags",
            "Security List OCIDs",
            "Route Rules",
            "Backend Sets",
            "Listeners",
            "Security Rules",
        ):

            width = 32

        if header in (
            "Lifecycle Details",
            "Dimensions",
            "Schema",
            "DDL Statement",
            "Replica Information",
            "Filesystem Snapshot Policy",
        ):

            width = 40

        ws.column_dimensions[
            get_column_letter(
                col_index
            )
        ].width = width

    # ---------------------------------------------------------
    # EXCEL TABLE
    # ---------------------------------------------------------

    if len(resources) > 0:

        last_column = get_column_letter(
            len(columns)
        )

        last_row = len(resources) + 1

        table_ref = (
            f"A1:{last_column}{last_row}"
        )

        safe_name = (
            "tbl_"
            + "".join(
                ch
                for ch in service
                if ch.isalnum()
            )
        )

        safe_name = safe_name[:240]

        try:

            table = Table(
                displayName=safe_name,
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

            ws.add_table(table)

        except Exception:
            pass


# ============================================================
# CREATE WORKBOOK
# ============================================================

def create_inventory_workbook(
    resources_by_service,
    output_file,
):

    """
    Create the complete OCI inventory workbook.

    Compatible with main.py:

        create_inventory_workbook(
            resources_by_service=resources_by_service,
            output_file=str(output_file),
        )
    """

    # ---------------------------------------------------------
    # NORMALIZE ALL RESOURCES
    # ---------------------------------------------------------

    all_resources = _normalize_resources(
        resources_by_service
    )

    # ---------------------------------------------------------
    # GROUP BY SERVICE
    # ---------------------------------------------------------

    grouped = {}

    for resource in all_resources:

        service = _normalize_service(
            resource.get(
                "service",
                "",
            ),
            resource.get(
                "resource_type",
                "",
            ),
        )

        resource["service"] = service

        grouped.setdefault(
            service,
            [],
        ).append(resource)

    # ---------------------------------------------------------
    # CREATE WORKBOOK
    # ---------------------------------------------------------

    workbook = Workbook()

    summary_sheet = workbook.active

    summary_sheet.title = "Summary"

    # ---------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------

    write_summary_sheet(
        summary_sheet,
        all_resources,
    )

    # ---------------------------------------------------------
    # SERVICE SHEETS
    # ---------------------------------------------------------

    for service in sorted(
        grouped.keys()
    ):

        resources = grouped[
            service
        ]

        # Excel sheet names max 31 chars
        sheet_name = service[:31]

        # Avoid duplicate sheet names
        if sheet_name in workbook.sheetnames:

            counter = 2

            while (
                f"{service[:28]}_{counter}"
                in workbook.sheetnames
            ):

                counter += 1

            sheet_name = (
                f"{service[:28]}_{counter}"
            )

        ws = workbook.create_sheet(
            title=sheet_name
        )

        write_resource_sheet(
            ws=ws,
            service=service,
            resources=resources,
        )

    # ---------------------------------------------------------
    # ENSURE SUMMARY FIRST
    # ---------------------------------------------------------

    workbook._sheets.remove(
        summary_sheet
    )

    workbook._sheets.insert(
        0,
        summary_sheet
    )

    # ---------------------------------------------------------
    # OUTPUT DIRECTORY
    # ---------------------------------------------------------

    output_path = Path(
        output_file
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------
    # SAVE
    # ---------------------------------------------------------

    workbook.save(
        output_path
    )

    print(
        f"Inventory workbook created: "
        f"{output_path}"
    )

    return str(output_path)
