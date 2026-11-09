"""Prepare the independent cerebral DSA collection; keep source files intact."""
import json
import subprocess

from prepare_videos import ROOT, SOURCE, probe, stream_hash, validate


def main():
    source_dir = SOURCE / '脑血管dsa'
    originals = sorted(p for p in source_dir.iterdir() if p.is_file() and p.suffix.lower() == '.mp4')
    if not originals:
        raise RuntimeError('No DSA MP4 files found.')
    output_dir = ROOT / 'dsa-videos'
    output_dir.mkdir(exist_ok=True)
    entries, report = [], []
    for index, source in enumerate(originals, 1):
        original_info = probe(source)
        output = output_dir / source.name
        temporary = output.with_suffix('.partial.mp4')
        subprocess.run([
            'ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-y',
            '-i', str(source), '-map', '0:v:0', '-map', '0:a?',
            '-c', 'copy', '-movflags', '+faststart', str(temporary),
        ], check=True)
        info = validate(temporary, original_info, source)
        if stream_hash(source) != stream_hash(temporary):
            raise RuntimeError(f'Media packet mismatch: {source.name}')
        temporary.replace(output)
        duration = float(info['format']['duration'])
        entries.append({
            'id': 'dsa-' + source.stem, 'number': f'{index:02}',
            'title': f'DSA 视频 {index:02}',
            'src': output.relative_to(ROOT).as_posix(),
            'duration': duration, 'originalName': source.name,
        })
        report.append({'source': source.name, 'bytes': output.stat().st_size,
                       'duration': duration, 'faststart': True, 'identicalMediaPackets': True})
    catalog = {
        'directoryMode': 'flat', 'totalVideos': len(entries),
        'totalDuration': sum(v['duration'] for v in entries),
        'chapters': [{'id': 'dsa', 'number': None, 'title': '脑血管 DSA',
                      'englishTitle': 'Cerebral Angiography', 'videos': entries}],
    }
    (ROOT / 'dsa-library.js').write_text(
        'window.VIDEO_LIBRARY = ' + json.dumps(catalog, ensure_ascii=False, indent=2) + ';\n',
        encoding='utf-8',
    )
    (ROOT / '.qa').mkdir(exist_ok=True)
    (ROOT / '.qa' / 'dsa-media-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'videos': len(entries), 'bytes': sum(r['bytes'] for r in report),
                      'faststart': True, 'identicalMediaPackets': True}))


if __name__ == '__main__':
    main()
