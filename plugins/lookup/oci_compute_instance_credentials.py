# Copyright: (c) 2020, Igor Tiunov <igortiunov@gmail.com>
# MIT (see LICENSE or https://spdx.org/licenses/MIT.html)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
lookup: compute_instance_credentials
author:
  - Igor Tiunov <igortiunov@gmail.com>
requirements:
  - oci

short_description: Look up credentials for the Windows OCI instances.
description:
  - Look up windows credentials for the instance.
  - Lookup is based on the instance's `OCID` value.
options:
  _terms:
    description: OCID of the instances to look up for credentials.
    required: True
  oci_profile:
    description: OCI credentials profile name.
    required: False
  on_missing:
    description:
        - Action to take if the secret is missing.
        - C(error) will raise a fatal error when the secret is missing.
        - C(skip) will silently ignore the missing secret.
        - C(warn) will skip over the missing secret but issue a warning.
    default: error
    type: string
    choices: ['error', 'skip', 'warn']
  on_denied:
    description:
        - Action to take if access to the secret is denied.
        - C(error) will raise a fatal error when access to the secret is denied.
        - C(skip) will silently ignore the denied secret.
        - C(warn) will skip over the denied secret but issue a warning.
    default: error
    type: string
    choices: ['error', 'skip', 'warn']
'''

EXAMPLES = r'''
- name: Create a new Autonomous Database with secret password
  win_ping:
  vars:
    ansible_user: "{{ lookup('cloud.oci.compute_instance_credentials', 'ocid1.instance.oc1.eu-frankfurt-1.instance_id' }}"
    ansible_password: "{{ lookup('cloud.oci.compute_instance_credentials', 'ocid1.instance.oc1.eu-frankfurt-1.instance_id' }}"
'''

RETURN = r'''
instance_credentials:
    description:
        - InstanceCredentials resource
    returned: on success
    type: complex
    contains:
        password:
            description:
                - The password for the username.
            returned: on success
            type: string
            sample: password_example
        username:
            description:
                - The username.
            returned: on success
            type: string
            sample: username_example
    sample: {
        "password": "password_example",
        "username": "username_example"
    }
'''

from ansible.errors import AnsibleError
from ansible.module_utils.six import string_types

try:
    from oci import config, exceptions, core, auth
except ImportError as import_error:
    raise AnsibleError("The lookup oci_secret requires oci python SDK.") from import_error

from ansible.plugins.lookup import LookupBase
from ansible.module_utils._text import to_native
from ansible_collections.cloud.oci.plugins.module_utils.oci_instance_credentials import get_instance_credentials

from os import path, environ


class LookupModule(LookupBase):
    def _get_oci_config(self):
        oci_config = {}
        oci_config_file = path.join(path.expanduser("~"), ".oci", "config")
        oci_config_profile = 'DEFAULT'

        if "OCI_CONFIG_PROFILE" in environ:
            oci_config_profile = environ.get("OCI_CONFIG_PROFILE")
        elif self.get_option("oci_profile") is not None:
            oci_config_profile = self.get_option('oci_profile')

        return config.from_file(file_location=oci_config_file, profile_name=oci_config_profile)

    def run(self, terms, variables, **kwargs):
        oci_config = {}
        signer = None

        missing = kwargs.get('on_missing', 'error').lower()
        if not isinstance(missing, string_types) or missing not in ['error', 'warn', 'skip']:
            raise AnsibleError('"on_missing" must be a string and one of "error", "warn" or "skip", not %s' % missing)

        denied = kwargs.get('on_denied', 'error').lower()
        if not isinstance(denied, string_types) or denied not in ['error', 'warn', 'skip']:
            raise AnsibleError('"on_denied" must be a string and one of "error", "warn" or "skip", not %s' % denied)

        self.set_options(var_options=variables, direct=kwargs)
        auth_type = environ.get("OCI_CLI_AUTH", "api_key")
        if auth_type == "api_key":
            oci_config = self._get_oci_config()
        elif auth_type == "instance_principal":
            signer = auth.signers.InstancePrincipalsSecurityTokenSigner()

        credentials = []
        for term in terms:
            try:
                credentials.append(get_instance_credentials(oci_config, signer, term))
                if not credentials and missing == 'error':
                    raise AnsibleError("Failed to find instance credentials %s (ResourceNotFound)" % term)
                elif not credentials and missing == 'warn':
                    self._display.warning('Skipping, did not find secret %s' % term)

            except exceptions.ServiceError as e:
                raise AnsibleError("Failed to retrieve instance credentials: %s" % to_native(e)) from e

        if kwargs.get('join'):
            joined_credentials = list()
            joined_credentials.append(''.join(credentials))
            return joined_credentials
        else:
            return credentials
