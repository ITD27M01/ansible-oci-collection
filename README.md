# Oracle Cloud Infrastructure Ansible Collection for missing things

## Purpose

This collection provides missing ansible code for Oracle Cloud Infrastructure. The usable one is oci_secret
`lookup` plugin to retrieve secrets from OCI Vault service.

Unfortunately, Ansible OCI collection doesn't ready for lookup plugins, and I have to maintain myself.  

## Installing collection from Ansible Galaxy

```bash
$ ansible-galaxy collection install itd27m01.oci
```
