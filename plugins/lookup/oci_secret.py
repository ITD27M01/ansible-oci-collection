# Copyright: (c) 2020, Igor Tiunov <igortiunov@gmail.com>
# MIT (see LICENSE or https://spdx.org/licenses/MIT.html)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
lookup: oci_secret
author:
  - Igor Tiunov <igortiunov@gmail.com>
requirements:
  - oci

short_description: Look up secrets stored in OCI Vault.
description:
  - Look up secrets stored in OCI Vault provided the caller
    has the appropriate permissions to read the secret.
  - Lookup is based on the secret's `Name` value.
  - Optional parameters can be passed into this lookup; `version_id` and `version_stage`
options:
  _terms:
    description: Name of the secret to look up in OCI Vault.
    required: True
  oci_profile:
    description: OCI credentials profile name.
    required: False
  compartment_id:
    description: Compartment OCID of vault store.
    required: False
  vault_id:
    description: Vault OCID of secret store.
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

EXAMPLES = r"""
- name: Create a new Autonomous Database with secret password
  oci_autonomous_database:
      compartment_id: "{{ compartment_ocid }}"
      cpu_core_count: "{{ cpu_core_count }}"
      display_name: "{{ display_name }}"
      admin_password: "{{ lookup('oci_secret', 'db_admin_password', compartment_id=compartment_id,
                                                                    vault_id=vault_id,
                                                                    on_missing='error') }}"
      db_name: "{{ db_name }}"
      data_storage_size_in_tbs: "{{ data_storage_size_in_tbs }}"
      is_free_tier: true
      state: 'present'

 - name: skip if secret does not exist
   debug: msg="{{ lookup('oci_secret', 'secret-not-exist', on_missing='skip')}}"

 - name: warn if access to the secret is denied
   debug: msg="{{ lookup('oci_secret', 'secret-denied', on_denied='warn')}}"
"""

RETURN = r"""
_raw:
  description:
    Returns the value of the secret stored in in OCI Vault.
"""

from ansible.errors import AnsibleError
from ansible.module_utils.six import string_types

try:
    from oci import config, exceptions
except ImportError:
    raise AnsibleError("The lookup oci_secret requires oci python SDK.")

from ansible.plugins.lookup import LookupBase
from ansible.module_utils._text import to_native
from ansible_collections.itd27m01.oci.plugins.module_utils.oci_vault_secrets import get_secret, get_secret_data

from os import path, environ


class LookupModule(LookupBase):
    def _get_oci_config(self):
        oci_config_file = path.join(path.expanduser("~"), ".oci", "config")
        oci_config_profile = 'DEFAULT'

        if "OCI_CONFIG_PROFILE" in environ:
            oci_config_profile = environ.get("OCI_CONFIG_PROFILE")
        elif self.get_option("oci_profile") is not None:
            oci_config_profile = self.get_option('oci_profile')

        return config.from_file(file_location=oci_config_file, profile_name=oci_config_profile)


    def run(self, terms, variables, **kwargs):

        missing = kwargs.get('on_missing', 'error').lower()
        if not isinstance(missing, string_types) or missing not in ['error', 'warn', 'skip']:
            raise AnsibleError('"on_missing" must be a string and one of "error", "warn" or "skip", not %s' % missing)

        denied = kwargs.get('on_denied', 'error').lower()
        if not isinstance(denied, string_types) or denied not in ['error', 'warn', 'skip']:
            raise AnsibleError('"on_denied" must be a string and one of "error", "warn" or "skip", not %s' % denied)

        self.set_options(var_options=variables, direct=kwargs)
        oci_config = self._get_oci_config()

        compartment_id = self.get_option('compartment_id')
        vault_id = self.get_option('vault_id')

        secrets = []
        for term in terms:
            try:
                secrets_list = get_secret(oci_config, compartment_id, vault_id, term)
                if not secrets_list and missing == 'error':
                    raise AnsibleError("Failed to find secret %s (ResourceNotFound)" % term)
                elif not secrets_list and missing == 'warn':
                    self._display.warning('Skipping, did not find secret %s' % term)

                if len(secrets_list) > 1:
                    self._display.warning('More than one secrets found with name %s' % term)

                for secret in secrets_list:
                    secrets.append(get_secret_data(oci_config, secret))

            except exceptions.ServiceError as e:
                raise AnsibleError("Failed to retrieve secret: %s" % to_native(e))


        if kwargs.get('join'):
            joined_secret = []
            joined_secret.append(''.join(secrets))
            return joined_secret
        else:
            return secrets
