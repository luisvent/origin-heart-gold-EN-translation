# Candidate/receipt publication

`install.execute` uses the shipping `publication.publish_pair` helper. Public
interfaces remain `candidate.nds` and `receipt.json`; no reader migration is
required. Publication does not change ROM construction or native gameplay.

The installer recovers any pending journal **before** input validation/building.
The helper also recovers before a new publication. Writers and recovery serialize
through `.publication.lock` (`flock`). The lock file is intentionally retained;
process exit releases the OS lock. This is a single-machine local-filesystem
protocol, not a distributed publication service.

1. Verify staged and existing pairs by receipt SHA-256 and byte count. Reject an
   existing incomplete/mismatched pair without a journal rather than guessing.
2. Prepare both new files and copies of both previous files in a unique
   `publication-*` directory. Verify the copied pairs; sync files and directory.
   The caller's staged files remain intact. Receipt preparation failure leaves
   the public pair unchanged.
3. Atomically install `.publication.json`, naming the recovery directory and
   whether a previous pair existed; sync the output directory.
4. Replace the public candidate, then receipt, and sync the output directory.
5. Unlink the journal: this is the commit point. No fallible cleanup follows it.
   The new coherent pair is now published. A closed stdout after publication does
   not make `build.py` claim the committed build was rejected.

Before commit, a normal exception triggers rollback using retained previous
copies (or removes both public files if this was the first publication). The
command returns nonzero and reports `REJECTED` only after successful rollback.
If rollback fails, it instead reports `RECOVERY REQUIRED`, returns nonzero and
retains the journal and backups. **Do not use either public file in that state.**
Fix the underlying I/O problem and rerun the installer; it recovers first.
Recovery can also be called without compiling via
`publication.recover_publication(output_directory)` using the existing Python
environment with `work/research/difficulty-armips` on its import path.

Recovery always rolls back a journaled transaction, even if both new files had
been renamed before interruption. It copies from backups into fresh restoration
files before replacing public paths, so interruption during recovery is retryable.
After a crash following journal unlink, the new pair is committed; the caller may
not have received success output. Absence of terminal output is not proof of a
rejected publication.

Limits: the two public renames are **not an atomic reader snapshot**. Concurrent
readers can observe a mixed pair, and abrupt process termination can leave one
until recovery. Readers must wait for successful publication/recovery and retain
their candidate/receipt hash checks. Sync operations improve ordering, but this
protocol does **not** promise power-loss durability, network-filesystem behavior,
or recovery from damaged/missing backups or external edits. In particular, journal
unlink has no subsequent directory sync; post-power-loss commit state is not
guaranteed. Writers outside this helper do not honor its lock.

Unique transaction directories are deliberately retained, including failed
preparations, to avoid turning cleanup failure into a misleading build outcome.
They consume disk space and are ignored build data, never release artifacts.
Do not remove recovery material while a journal exists. Cleanup is manual after
publication/recovery, with no writer active; the helper performs no garbage
collection.

`test_installer.PublicationTests` exercises this actual helper with small text
payloads: receipt-write, first/second-rename and rollback failures; interrupted
publication before each public rename and commit; interrupted/retried recovery;
first-publication absence; truthful CLI outcomes and committed-output failure.
These are host failure-injection tests, not filesystem power-loss experiments.
