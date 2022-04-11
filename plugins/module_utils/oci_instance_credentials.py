# Copyright: (c) 2020, Igor Tiunov <igortiunov@gmail.com>
# MIT (see LICENSE or https://spdx.org/licenses/MIT.html)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

try:
    from oci.core import ComputeClient
except ImportError as import_error:
    raise ImportError("The lookup oci_compute_instance_credentials requires oci python SDK.") from import_error


def get_core_client(oci_config, signer):
    return ComputeClient(config=oci_config, signer=signer)


def get_instance_credentials(config, signer, instance_id):
    core_client = get_core_client(config, signer)
    return core_client.get_windows_instance_initial_credentials(instance_id=instance_id).data
