# Oracle Cloud Infrastructure Ansible Collection for missing things

## Purpose

This collection provides missing ansible code for Oracle Cloud Infrastructure. The usable one is oci_secret
`lookup` plugin to retrieve secrets from OCI Vault service.

### Expand hostvars

As for `openstack` inventory plugin this collection adds `expand_hostvars` inventory option which runs extra commands
on each host to fill in additional information about the host. May interrogate volume and network services
and can be expensive for people with many hosts. At the time of this writing it adds `volume_attachments` and `volumes`
information to help disks configuration.

## Installing collection from Ansible Galaxy

```
$ ansible-galaxy collection install itd27m01.oci
```
