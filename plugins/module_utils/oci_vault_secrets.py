# Copyright: (c) 2020, Igor Tiunov <igortiunov@gmail.com>
# MIT (see LICENSE or https://spdx.org/licenses/MIT.html)

from ansible.errors import AnsibleError
from base64 import b64decode

try:
    from oci import config, secrets, vault, key_management
except ImportError:
    raise AnsibleError("The lookup oci_secret requires oci python SDK.")


def get_secrets_client(oci_config):
    return vault.VaultsClient(config=oci_config)


def get_secret_bundle_client(oci_config):
    return secrets.SecretsClient(config=oci_config)


def get_secret(oci_config, compartment_id, vault_id, secret_name):
    secrets_client = get_secrets_client(oci_config)

    return secrets_client.list_secrets(compartment_id=compartment_id,
                                       vault_id=vault_id,
                                       name=secret_name).data


def get_secret_data(oci_config, secret):
    secret_bundle_client = get_secret_bundle_client(oci_config)

    secret_bundle_response = secret_bundle_client.get_secret_bundle(secret_id=secret.id)
    if secret_bundle_response.status == 200:
        return b64decode(secret_bundle_response.data.secret_bundle_content.content).decode()
    else:
        raise ValueError("Something went wrong during secret data get")
