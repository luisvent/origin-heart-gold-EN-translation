"""Recoverable two-file publication; see research/publication.md for limits.

Only the journal unlink commits. Until then recovery restores the previous pair
from retained copies, including after both public renames have completed.
"""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile


NAMES = ('candidate.nds', 'receipt.json')
JOURNAL = '.publication.json'


class PublicationRejected(RuntimeError):
    """No publication committed; the previous pair (or absence) is restored."""


class PublicationRecoveryRequired(RuntimeError):
    """Public paths must not be used until journal recovery succeeds."""


@contextmanager
def _locked(output):
    output.mkdir(parents=True, exist_ok=True)
    with (output/'.publication.lock').open('a+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def _sync(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _verify_pair(candidate, receipt):
    data = candidate.read_bytes()
    row = json.loads(receipt.read_text())['output']
    if row['sha256'] != hashlib.sha256(data).hexdigest() or row['bytes'] != len(data):
        raise ValueError('publication candidate/receipt mismatch')


def _recover(output):
    journal = output/JOURNAL
    if not journal.exists():
        return False
    try:
        record = json.loads(journal.read_text())
        name = record['transaction']
        if Path(name).name != name or not name.startswith('publication-'):
            raise ValueError('invalid publication recovery directory')
        transaction = output/name
        if record['previous'] is True:
            _verify_pair(transaction/'old-candidate.nds', transaction/'old-receipt.json')
            for name in NAMES:
                restore = transaction/('restore-'+name)
                shutil.copyfile(transaction/('old-'+name), restore)
                _sync(restore)
                os.replace(restore, output/name)
            _verify_pair(output/NAMES[0], output/NAMES[1])
        elif record['previous'] is False:
            for name in NAMES:
                (output/name).unlink(missing_ok=True)
        else:
            raise ValueError('invalid publication previous-pair state')
        _sync(output)
        journal.unlink()
        return True
    except Exception as exc:
        raise PublicationRecoveryRequired(
            f'publication recovery required: {journal}; do not use public pair: {exc}') from exc


def recover_publication(output):
    """Idempotently roll back an interrupted transaction before a new build."""
    output = Path(output)
    with _locked(output):
        return _recover(output)


def publish_pair(candidate, receipt, output):
    """Return only after commit; reject with rollback or explicit recovery state.

    Inputs are verified staged files and remain untouched. No ROM construction
    takes place here, so the real shipping path can be failure-tested cheaply.
    """
    candidate, receipt, output = Path(candidate), Path(receipt), Path(output)
    with _locked(output):
        _recover(output)
        _verify_pair(candidate, receipt)
        present = [(output/name).exists() for name in NAMES]
        if any(present) != all(present):
            raise ValueError('incomplete existing public pair without recovery journal')
        previous = all(present)
        if previous:
            _verify_pair(output/NAMES[0], output/NAMES[1])
        transaction = Path(tempfile.mkdtemp(prefix='publication-', dir=output))
        try:
            # Prepare every byte, including receipt, before touching public paths.
            shutil.copyfile(candidate, transaction/NAMES[0])
            (transaction/NAMES[1]).write_bytes(receipt.read_bytes())
            if previous:
                for name in NAMES:
                    shutil.copyfile(output/name, transaction/('old-'+name))
                _verify_pair(transaction/'old-candidate.nds', transaction/'old-receipt.json')
            _verify_pair(transaction/NAMES[0], transaction/NAMES[1])
            pending = transaction/'journal.pending.json'
            pending.write_text(json.dumps(dict(transaction=transaction.name, previous=previous))+'\n')
            for path in transaction.iterdir():
                _sync(path)
            _sync(transaction)
            os.replace(pending, output/JOURNAL)
            _sync(output)
            os.replace(transaction/NAMES[0], output/NAMES[0])
            os.replace(transaction/NAMES[1], output/NAMES[1])
            _sync(output)
            # Commit point. No fallible cleanup after this operation. Retained
            # transaction directories are intentional recovery/audit material.
            (output/JOURNAL).unlink()
        except Exception as exc:
            _recover(output)  # Raises RecoveryRequired if rollback itself fails.
            raise PublicationRejected(
                f'publication rejected; previous pair unchanged/restored: {exc}') from exc
