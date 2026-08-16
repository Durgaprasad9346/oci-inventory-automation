import oci


def get_oci_config():
    """
    Load OCI configuration from the default OCI config file.

    The config file is expected to exist on the machine where
    the inventory script is executed, typically:

        ~/.oci/config
    """
    return oci.config.from_file()
