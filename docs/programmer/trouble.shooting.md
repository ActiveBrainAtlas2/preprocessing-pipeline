## Trouble shooting problems
### Files get corrupted
1. This is very often

Proposed solution for workflow:
-As files are generated (czi), we also generate sha256 hash checksum.  Each text output file will be stored in same folder as raw czi files.  Python or other programmatic access can validate files are not corrupted prior to processing. Size benefit is we will be able to also ensure we are working on correct source file, rather than assuming filename is accurate.

Proposed solution for file system:
-Implement zfs or btrfs on backend block storage.  This configuration will automaticaly generate checksums for files and compensate to avoid file corruption issues.

There may be additional places in operational activities where checksums make sense as well
