def write_summary_sheet(ws, resources):
    """
    Write a single consolidated Summary sheet.

    Summary format:
        S.No | Service Name | Description | Resource Count

    Counts are calculated from the collected inventory resources.
    """

    from collections import Counter
    from datetime import datetime

    # ---------------------------------------------------------
    # CLEAR EXISTING SUMMARY CONTENT
    # ---------------------------------------------------------
    for row in ws.iter_rows():
        for cell in row:
            cell.value = None

    # ---------------------------------------------------------
    # TITLE
    # ---------------------------------------------------------
    ws["A1"] = "OCI Inventory Summary"
    ws["A1"].font = Font(
        bold=True,
        size=16
    )

    # ---------------------------------------------------------
    # REPORT GENERATED
    # ---------------------------------------------------------
    ws["A3"] = "Report Generated"
    ws["A3"].font = Font(bold=True)

    ws["B3"] = datetime.now().replace(tzinfo=None)
    ws["B3"].number_format = "yyyy-mm-dd hh:mm:ss"

    # ---------------------------------------------------------
    # NORMALIZE RESOURCES
    # ---------------------------------------------------------
    normalized_resources = []

    for resource in resources:

        if resource is None:
            continue

        if isinstance(resource, dict):
            service = resource.get("service")
            resource_type = resource.get("resource_type")
        else:
            service = getattr(resource, "service", None)
            resource_type = getattr(resource, "resource_type", None)

        service = str(service or "").strip()
        resource_type = str(resource_type or "").strip()

        if not service:
            continue

        normalized_resources.append(
            {
                "service": service,
                "resource_type": resource_type
            }
        )

    # ---------------------------------------------------------
    # SERVICE NAME NORMALIZATION
    # ---------------------------------------------------------
    # This prevents the same OCI service from appearing twice
    # because collectors used slightly different names.
    # ---------------------------------------------------------
    service_aliases = {
        "Compute": "Compute",
        "Instances": "Compute",
        "Instance": "Compute",

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

        "Virtual Cloud Network": "VCN",
        "Virtual Cloud Networks": "VCN",
        "VCN": "VCN",

        "Subnet": "Subnet",
        "Subnets": "Subnet",

        "Network Security Group": "Network Security Group",
        "Network Security Groups": "Network Security Group",
        "NSG": "Network Security Group",

        "Load Balancer": "Load Balancer",
        "Load Balancers": "Load Balancer",

        "Local Peering Gateway": "Local Peering Gateway",
        "Local Peering Gateways": "Local Peering Gateway",

        "Route Table": "Route Table",
        "Route Tables": "Route Table",

        "DHCP Options": "DHCP Options",

        "DNS Resolver": "DNS Resolver",
        "DNS View": "DNS View",

        "DB Systems": "DB Systems",
        "DB System": "DB Systems",

        "DB Homes": "DB Home",
        "DB Home": "DB Home",

        "DB Nodes": "DB Node",
        "DB Node": "DB Node",

        "ExaCS": "ExaCS",

        "NoSQL Database": "NoSQL Database",
        "NoSQL Databases": "NoSQL Database",

        "Key Management": "Key Management",
        "Key": "Key",

        "Vault": "Vault",
        "Vaults": "Vault",

        "Secrets": "Secrets",
        "Secret": "Secrets",

        "Notifications": "Notifications",
        "Notification Topic": "Notifications",
        "Notification Topics": "Notifications",

        "Streaming": "Streaming",
        "Stream": "Streaming",

        "Logging": "Logging",
        "Log": "Logging",
        "Logs": "Logging",

        "Monitoring": "Monitoring",

        "Alarms": "Alarms",
        "Alarm": "Alarms",

        "DNS": "DNS",

        "Compartment": "Compartment",
        "Compartments": "Compartment",
    }

    # ---------------------------------------------------------
    # DESCRIPTION
    # ---------------------------------------------------------
    descriptions = {
        "Compute": "Compute instances",
        "Block Volume": "Block volumes",
        "Boot Volume": "Boot volumes",
        "Object Storage": "Object Storage buckets",
        "File Storage": "File systems",
        "VCN": "Virtual Cloud Networks",
        "Subnet": "Subnets",
        "Network Security Group": "Network Security Groups",
        "Load Balancer": "Load balancers",
        "Local Peering Gateway": "Local peering gateways",
        "Route Table": "Route tables",
        "DHCP Options": "DHCP options",
        "DNS Resolver": "DNS resolvers",
        "DNS View": "DNS views",
        "DB Systems": "Database systems",
        "DB Home": "Database homes",
        "DB Node": "Database nodes",
        "ExaCS": "Exadata Cloud Service",
        "NoSQL Database": "NoSQL databases",
        "Key Management": "Key Management keys",
        "Key": "Encryption keys",
        "Vault": "Vaults",
        "Secrets": "Vault secrets",
        "Notifications": "Notification topics/subscriptions",
        "Streaming": "Streaming resources",
        "Logging": "Logging resources",
        "Monitoring": "Monitoring resources",
        "Alarms": "Monitoring alarms",
        "DNS": "DNS resources",
        "Compartment": "OCI compartments",
    }

    # ---------------------------------------------------------
    # COUNT BY SERVICE
    # ---------------------------------------------------------
    service_counts = Counter()

    for item in normalized_resources:

        service = item["service"]
        resource_type = item["resource_type"]

        # First try service name
        normalized_service = service_aliases.get(
            service,
            service
        )

        # Some collectors may report generic service names.
        # Use resource type where appropriate.
        if normalized_service in (
            "",
            "OCI"
        ) and resource_type:
            normalized_service = service_aliases.get(
                resource_type,
                resource_type
            )

        service_counts[normalized_service] += 1

    # ---------------------------------------------------------
    # TOTAL RESOURCES
    # ---------------------------------------------------------
    total_resources = sum(service_counts.values())

    ws["A5"] = "Total Resources"
    ws["A5"].font = Font(bold=True)

    ws["B5"] = total_resources
    ws["B5"].font = Font(
        bold=True,
        size=12
    )

    # ---------------------------------------------------------
    # SINGLE SUMMARY TABLE
    # ---------------------------------------------------------
    header_row = 7

    headers = [
        "S.No",
        "Service Name",
        "Description",
        "Resource Count"
    ]

    for col, header in enumerate(headers, start=1):

        cell = ws.cell(
            row=header_row,
            column=col,
            value=header
        )

        cell.font = Font(
            bold=True
        )

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

    # ---------------------------------------------------------
    # SERVICE ORDER
    # ---------------------------------------------------------
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
        "NoSQL Database",
        "Key",
        "Key Management",
        "Vault",
        "Secrets",
        "Notifications",
        "Streaming",
        "Logging",
        "Monitoring",
        "Alarms",
        "DNS",
    ]

    ordered_services = []

    # First add services in desired order
    for service in preferred_order:
        if service in service_counts:
            ordered_services.append(service)

    # Then add any newly discovered services
    # automatically.
    for service in sorted(service_counts.keys()):
        if service not in ordered_services:
            ordered_services.append(service)

    # ---------------------------------------------------------
    # WRITE ROWS
    # ---------------------------------------------------------
    row = header_row + 1
    serial = 1

    for service in ordered_services:

        description = descriptions.get(
            service,
            service
        )

        ws.cell(
            row=row,
            column=1,
            value=serial
        )

        ws.cell(
            row=row,
            column=2,
            value=service
        )

        ws.cell(
            row=row,
            column=3,
            value=description
        )

        ws.cell(
            row=row,
            column=4,
            value=service_counts[service]
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

    for current_row in ws.iter_rows(
        min_row=header_row,
        max_row=row - 1,
        min_col=1,
        max_col=4
    ):
        for cell in current_row:
            cell.alignment = Alignment(
                vertical="center"
            )

    # Header alignment
    for col in range(1, 5):
        ws.cell(
            row=header_row,
            column=col
        ).alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

    # Count column
    for current_row in range(
        header_row + 1,
        row
    ):
        ws.cell(
            row=current_row,
            column=4
        ).alignment = Alignment(
            horizontal="right"
        )

    # ---------------------------------------------------------
    # FREEZE HEADER
    # ---------------------------------------------------------
    ws.freeze_panes = "A8"

    # ---------------------------------------------------------
    # AUTO FILTER
    # ---------------------------------------------------------
    if row > header_row + 1:
        ws.auto_filter.ref = (
            f"A{header_row}:D{row - 1}"
        )

    # ---------------------------------------------------------
    # REMOVE DUPLICATE SUMMARY TABLES
    # ---------------------------------------------------------
    # Nothing else is written to the right side.
    # The Summary sheet intentionally contains only
    # the single consolidated table above.
    # ---------------------------------------------------------

    return total_resources
