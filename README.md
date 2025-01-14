# This project is currently still in development!

We are testing the project internally and finishing some loose ends. Once we are done, the project will be released for public usage.


# HPC Eval

Evaluation tool for HPC and parallel-programming coding assignments.



### Adding sandbox user under which the evaluations will take place

```
#> adduser -u 2001 sandboxuser01
```

Assuming the teachers account is `teacher` (with the same group), the following lines need to be added in `/etc/sudoers`:
```
teacher        ALL=(ALL)       NOPASSWD:       /bin/chown -R sandboxuser*\:sandboxuser* *
teacher        ALL=(ALL)       NOPASSWD:       /bin/su -l -c * sandboxuser*
sandboxuser01  ALL=(ALL)       NOPASSWD:       /bin/chown -R teacher\:teacher *
```

The lines are partially ready for having multiple sandbox users with different numeric suffixes ready. The last line needs to be either replicated, or the *sandboxusers* need to have a common group (then `%group` syntax can be used).

**Pitfall:** All the directories on the path to a `box` directory (working directory of the evaluation) **must** be accessible by the sandbox users. For instance, if the `hpc-eval` root directory is `/home/teacher/hpc`, the `teacher` and `hpc` directories must have either `o+x` permission, or ACLs set for sandboxuser01, for instance:

```
$> setfacl -m u:sandboxuser01:x /home/teacher
$> setfacl -m u:sandboxuser01:x /home/teacher/hpc
```
