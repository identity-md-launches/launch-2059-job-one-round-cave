#!/usr/bin/env python3
"""Replay shipped public API bytes under a shared whole-ZIP input budget."""
import hashlib
import json
from pathlib import Path
import tempfile
import zipfile

from zipmerge import Rejected, local_path, process


def main():
    sources = Path(__file__).resolve().parents[1] / 'safezip'
    capture = (sources / 'imd-openapi.json').read_bytes()
    provenance = (sources / 'sample-source.json').read_bytes()
    assert hashlib.sha256(capture).hexdigest() == (
        'be142840c010710cb2a5b9e5c73e71d8e79ec4054c15661699d60bfa627be96a')
    scratch = local_path('test/scratch')
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch, prefix='merge-input-demo-') as temporary:
        root = Path(temporary)
        specs = []
        for name, data in [('openapi.json', capture), ('source.json', provenance)]:
            archive = root / (name + '.zip')
            with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as writer:
                writer.writestr('docs/' + name, data)
                writer.comment = b'Illustrative archive envelope. ' * 100
            specs.append(dict(archive=archive,
                              sha256=hashlib.sha256(archive.read_bytes()).hexdigest()))
        total = sum(s['archive'].stat().st_size for s in specs)
        try:
            process(specs, root / 'refused', merge_archive_bytes=total - 1)
        except Rejected as error:
            refusal = str(error)
        else:
            raise AssertionError('shared input overrun accepted')
        assert not (root / 'refused').exists()
        output = root / 'combined'
        report = process(specs, output, merge_archive_bytes=total)
        assert (output / 'docs/openapi.json').read_bytes() == capture
        assert (output / 'docs/source.json').read_bytes() == provenance
        assert report['input']['archive_bytes'] == total
        print(json.dumps(dict(ok=True, network_used=False,
                              historical_public_source='https://api.imd.fun/openapi.json',
                              capture_bytes=len(capture), byte_identical=True,
                              one_byte_under_refused=refusal, report=report), indent=2))


if __name__ == '__main__':
    main()
