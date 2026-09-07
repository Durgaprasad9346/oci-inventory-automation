import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_pluggable_databases(config):
    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:
        print(f"  Processing Pluggable Databases region: {region}")

        region_config = config.copy()
        region_config["region"] = region

        database_client = oci.database.DatabaseClient(region_config)

        for compartment in compartments:
            compartment_id = compartment["id"]
            compartment_name = compartment["name"]

            try:
                db_systems = oci.pagination.list_call_get_all_results(
                    database_client.list_db_systems,
                    compartment_id=compartment_id,
                )
            except Exception as error:
                print(
                    f"    ERROR collecting DB Systems from compartment "
                    f"{compartment_name}: {error}"
                )
                continue

            for db_system in db_systems.data:
                db_system_id = getattr(db_system, "id", "")
                db_system_name = getattr(db_system, "display_name", "")

                if not db_system_id:
                    continue

                try:
                    db_homes = oci.pagination.list_call_get_all_results(
                        database_client.list_db_homes,
                        compartment_id=compartment_id,
                        db_system_id=db_system_id,
                    )
                except Exception as error:
                    print(
                        f"    ERROR collecting DB Homes from DB System "
                        f"{db_system_name}: {error}"
                    )
                    continue

                for db_home in db_homes.data:
                    db_home_id = getattr(db_home, "id", "")
                    db_home_name = getattr(db_home, "display_name", "")

                    if not db_home_id:
                        continue

                    try:
                        databases = oci.pagination.list_call_get_all_results(
                            database_client.list_databases,
                            compartment_id=compartment_id,
                            db_home_id=db_home_id,
                        )
                    except Exception as error:
                        print(
                            f"    ERROR collecting Databases from DB Home "
                            f"{db_home_name}: {error}"
                        )
                        continue

                    for database in databases.data:
                        database_id = getattr(database, "id", "")
                        database_name = getattr(database, "db_name", "")

                        if not database_id:
                            continue

                        try:
                            pdbs = oci.pagination.list_call_get_all_results(
                                database_client.list_pluggable_databases,
                                compartment_id=compartment_id,
                                database_id=database_id,
                            )
                        except Exception as error:
                            print(
                                f"    ERROR collecting Pluggable Databases "
                                f"from Database {database_name}: {error}"
                            )
                            continue

                        for pdb in pdbs.data:
                            pdb_id = getattr(pdb, "id", "")
                            pdb_name = getattr(pdb, "pdb_name", "")

                            resources.append(
                                Resource(
                                    service="DB Systems",
                                    resource_type="Pluggable Database",
                                    name=pdb_name
                                    or getattr(pdb, "display_name", ""),
                                    ocid=pdb_id,
                                    compartment_id=compartment_id,
                                    compartment_name=compartment_name,
                                    region=region,
                                    state=getattr(
                                        pdb,
                                        "lifecycle_state",
                                        "",
                                    ),
                                    time_created=getattr(
                                        pdb,
                                        "time_created",
                                        None,
                                    ),
                                    defined_tags=getattr(
                                        pdb,
                                        "defined_tags",
                                        None,
                                    ),
                                    freeform_tags=getattr(
                                        pdb,
                                        "freeform_tags",
                                        None,
                                    ),
                                    details={
                                        "db_system_id": db_system_id,
                                        "db_system_name": db_system_name,
                                        "db_home_id": db_home_id,
                                        "db_home_name": db_home_name,
                                        "database_id": database_id,
                                        "database_name": database_name,
                                        "pdb_name": pdb_name,
                                        "open_mode": getattr(
                                            pdb,
                                            "open_mode",
                                            "",
                                        ),
                                        "lifecycle_details": getattr(
                                            pdb,
                                            "lifecycle_details",
                                            "",
                                        ),
                                        "connection_strings": getattr(
                                            pdb,
                                            "connection_strings",
                                            "",
                                        ),
                                    },
                                )
                            )

    return resources
PY


cat > collectors/ons_subscription.py <<'PY'
import oci

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_ons_subscriptions(config):
    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:
        print(f"  Processing ONS Subscriptions region: {region}")

        region_config = config.copy()
        region_config["region"] = region

        control_client = oci.ons.NotificationControlPlaneClient(
            region_config
        )

        data_client = oci.ons.NotificationDataPlaneClient(
            region_config
        )

        for compartment in compartments:
            compartment_id = compartment["id"]
            compartment_name = compartment["name"]

            try:
                topics = oci.pagination.list_call_get_all_results(
                    control_client.list_topics,
                    compartment_id=compartment_id,
                )
            except Exception as error:
                print(
                    f"    ERROR collecting ONS Topics from compartment "
                    f"{compartment_name}: {error}"
                )
                continue

            for topic in topics.data:
                topic_id = getattr(topic, "topic_id", None)

                if not topic_id:
                    topic_id = getattr(topic, "id", "")

                topic_name = getattr(topic, "name", "")

                if not topic_id:
                    continue

                try:
                    subscriptions = oci.pagination.list_call_get_all_results(
                        data_client.list_subscriptions,
                        compartment_id=compartment_id,
                        topic_id=topic_id,
                    )
                except Exception as error:
                    print(
                        f"    ERROR collecting subscriptions for topic "
                        f"{topic_name}: {error}"
                    )
                    continue

                for subscription in subscriptions.data:
                    resources.append(
                        Resource(
                            service="Notifications",
                            resource_type="ONS Subscription",
                            name=getattr(
                                subscription,
                                "endpoint",
                                "",
                            ),
                            ocid=getattr(
                                subscription,
                                "id",
                                "",
                            ),
                            compartment_id=compartment_id,
                            compartment_name=compartment_name,
                            region=region,
                            state=getattr(
                                subscription,
                                "lifecycle_state",
                                "",
                            ),
                            time_created=getattr(
                                subscription,
                                "time_created",
                                None,
                            ),
                            defined_tags=getattr(
                                subscription,
                                "defined_tags",
                                None,
                            ),
                            freeform_tags=getattr(
                                subscription,
                                "freeform_tags",
                                None,
                            ),
                            details={
                                "subscription_id": getattr(
                                    subscription,
                                    "id",
                                    "",
                                ),
                                "topic_id": topic_id,
                                "topic_name": topic_name,
                                "endpoint": getattr(
                                    subscription,
                                    "endpoint",
                                    "",
                                ),
                                "protocol": getattr(
                                    subscription,
                                    "protocol",
                                    "",
                                ),
                                "delivery_policy": getattr(
                                    subscription,
                                    "delivery_policy",
                                    "",
                                ),
                                "filter_rule": getattr(
                                    subscription,
                                    "filter_rule",
                                    "",
                                ),
                            },
                        )
                    )

    return resources
PY


cat > collectors/certificates.py <<'PY'
import oci

from oci.certificates_management import CertificatesManagementClient

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_certificates(config):
    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:
        print(f"  Processing Certificates region: {region}")

        region_config = config.copy()
        region_config["region"] = region

        certificates_client = CertificatesManagementClient(
            region_config
        )

        for compartment in compartments:
            compartment_id = compartment["id"]
            compartment_name = compartment["name"]

            try:
                certificates = (
                    oci.pagination.list_call_get_all_results(
                        certificates_client.list_certificates,
                        compartment_id=compartment_id,
                    )
                )
            except Exception as error:
                print(
                    f"    ERROR collecting Certificates from compartment "
                    f"{compartment_name}: {error}"
                )
                continue

            for certificate in certificates.data:
                resources.append(
                    Resource(
                        service="Certificates",
                        resource_type="Certificate",
                        name=getattr(
                            certificate,
                            "name",
                            "",
                        ),
                        ocid=getattr(
                            certificate,
                            "id",
                            "",
                        ),
                        compartment_id=compartment_id,
                        compartment_name=compartment_name,
                        region=region,
                        state=getattr(
                            certificate,
                            "lifecycle_state",
                            "",
                        ),
                        time_created=getattr(
                            certificate,
                            "time_created",
                            None,
                        ),
                        defined_tags=getattr(
                            certificate,
                            "defined_tags",
                            None,
                        ),
                        freeform_tags=getattr(
                            certificate,
                            "freeform_tags",
                            None,
                        ),
                        details={
                            "certificate_authority_id": getattr(
                                certificate,
                                "certificate_authority_id",
                                "",
                            ),
                            "certificate_type": getattr(
                                certificate,
                                "certificate_type",
                                "",
                            ),
                            "issuer_certificate_authority_id": getattr(
                                certificate,
                                "issuer_certificate_authority_id",
                                "",
                            ),
                            "key_algorithm": getattr(
                                certificate,
                                "key_algorithm",
                                "",
                            ),
                            "signature_algorithm": getattr(
                                certificate,
                                "signature_algorithm",
                                "",
                            ),
                            "validity": getattr(
                                certificate,
                                "validity",
                                "",
                            ),
                            "time_of_deletion": getattr(
                                certificate,
                                "time_of_deletion",
                                None,
                            ),
                            "description": getattr(
                                certificate,
                                "description",
                                "",
                            ),
                        },
                    )
                )

    return resources
PY


cat > collectors/certificate_authority.py <<'PY'
import oci

from oci.certificates_management import CertificatesManagementClient

from collectors.base import Resource
from utils.compartments import get_compartments
from utils.regions import get_regions


def collect_certificate_authorities(config):
    compartments = get_compartments(config)
    regions = get_regions(config)

    resources = []

    for region in regions:
        print(
            f"  Processing Certificate Authorities region: {region}"
        )

        region_config = config.copy()
        region_config["region"] = region

        certificate_client = CertificatesManagementClient(
            region_config
        )

        for compartment in compartments:
            compartment_id = compartment["id"]
            compartment_name = compartment["name"]

            try:
                certificate_authorities = (
                    oci.pagination.list_call_get_all_results(
                        certificate_client.list_certificate_authorities,
                        compartment_id=compartment_id,
                    )
                )
            except Exception as error:
                print(
                    f"    ERROR collecting Certificate Authorities "
                    f"from compartment {compartment_name}: {error}"
                )
                continue

            for certificate_authority in certificate_authorities.data:
                resources.append(
                    Resource(
                        service="Certificates",
                        resource_type="Certificate Authority",
                        name=getattr(
                            certificate_authority,
                            "name",
                            "",
                        ),
                        ocid=getattr(
                            certificate_authority,
                            "id",
                            "",
                        ),
                        compartment_id=compartment_id,
                        compartment_name=compartment_name,
                        region=region,
                        state=getattr(
                            certificate_authority,
                            "lifecycle_state",
                            "",
                        ),
                        time_created=getattr(
                            certificate_authority,
                            "time_created",
                            None,
                        ),
                        defined_tags=getattr(
                            certificate_authority,
                            "defined_tags",
                            None,
                        ),
                        freeform_tags=getattr(
                            certificate_authority,
                            "freeform_tags",
                            None,
                        ),
                        details={
                            "certificate_authority_type": getattr(
                                certificate_authority,
                                "certificate_authority_type",
                                "",
                            ),
                            "certificate_type": getattr(
                                certificate_authority,
                                "certificate_type",
                                "",
                            ),
                            "issuer_certificate_authority_id": getattr(
                                certificate_authority,
                                "issuer_certificate_authority_id",
                                "",
                            ),
                            "key_algorithm": getattr(
                                certificate_authority,
                                "key_algorithm",
                                "",
                            ),
                            "signature_algorithm": getattr(
                                certificate_authority,
                                "signature_algorithm",
                                "",
                            ),
                            "validity": getattr(
                                certificate_authority,
                                "validity",
                                "",
                            ),
                            "time_of_deletion": getattr(
                                certificate_authority,
                                "time_of_deletion",
                                None,
                            ),
                            "description": getattr(
                                certificate_authority,
                                "description",
                                "",
                            ),
                        },
                    )
                )

    return resources
PY


python3 -m py_compile \
collectors/pluggable_database.py \
collectors/ons_subscription.py \
collectors/certificates.py \
collectors/certificate_authority.py
