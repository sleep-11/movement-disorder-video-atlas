"""Prepare a static video library without changing any original files."""
import concurrent.futures
import json
import re
import struct
import subprocess
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent
LIMIT = 100 * 1024 ** 2
CHAPTERS = [
    (1, '帕金森综合征及相关疾病', 'Parkinsonism and Related'),
    (2, '震颤', 'Tremors'),
    (3, '肌张力障碍', 'Dystonias'),
    (4, '舞蹈样运动障碍', 'Choreiform Disorders'),
    (5, '肌阵挛', 'Myoclonus'),
    (6, '小脑性共济失调', 'Cerebellar Ataxia'),
    (7, '抽动障碍', 'Tic Disorders'),
    (None, '补充视频', 'Supplementary Videos'),
]


def probe(file):
    result = subprocess.run(['ffprobe', '-v', 'error', '-show_format', '-show_streams',
                             '-of', 'json', str(file)], capture_output=True, check=True)
    return json.loads(result.stdout)


def video_stream(info):
    return next(s for s in info['streams'] if s['codec_type'] == 'video')


def has_faststart(file):
    with file.open('rb') as stream:
        length = file.stat().st_size
        while stream.tell() + 8 <= length:
            position = stream.tell()
            size, kind = struct.unpack('>I4s', stream.read(8))
            if size == 1:
                size = struct.unpack('>Q', stream.read(8))[0]
            if kind == b'moov':
                return True
            if kind == b'mdat' or size < 8:
                return False
            stream.seek(position + size)
    return False


def stream_hash(file):
    return subprocess.run(['ffmpeg', '-v', 'error', '-i', str(file), '-map', '0:v:0',
                           '-map', '0:a?', '-c', 'copy', '-f', 'streamhash', '-hash',
                           'sha256', '-'], capture_output=True, check=True).stdout


def validate(output, original_info, source):
    info = probe(output)
    original_video, output_video = video_stream(original_info), video_stream(info)
    assert output.stat().st_size < LIMIT, f'File too large: {output.name}'
    assert output_video['codec_name'] == 'h264', output.name
    assert (output_video['width'], output_video['height']) == (original_video['width'], original_video['height']), output.name
    assert abs(float(Fraction(output_video['avg_frame_rate'])) - float(Fraction(original_video['avg_frame_rate']))) < 0.01, output.name
    assert output_video.get('nb_frames') == original_video.get('nb_frames'), output.name
    duration_delta = abs(float(info['format']['duration']) - float(original_info['format']['duration']))
    if duration_delta > 0.1:
        # Some original HE-AAC containers overstate the final audio packet duration.
        # Permit corrected container timing only when every media packet is identical.
        assert duration_delta < 0.25 and stream_hash(source) == stream_hash(output), output.name
    assert [s['codec_name'] for s in info['streams'] if s['codec_type'] == 'audio'] == [s['codec_name'] for s in original_info['streams'] if s['codec_type'] == 'audio'], output.name
    assert has_faststart(output), f'moov is not before mdat: {output.name}'
    return info


def main():
    (ROOT / 'videos').mkdir(exist_ok=True)
    (ROOT / '.qa').mkdir(exist_ok=True)
    originals = sorted(SOURCE.glob('*.mp4'))
    if not originals:
        raise RuntimeError('No original MP4 files found in the parent directory.')
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        metadata = dict(zip(originals, pool.map(probe, originals)))
    chapters = [{'id': str(n) if n else 'supplement', 'number': n, 'title': cn,
                 'englishTitle': en, 'videos': []} for n, cn, en in CHAPTERS]
    jobs = []
    supplements = 0
    for source in originals:
        match = re.match(r'^(\d+)\.(\d+)\.', source.name)
        title = re.sub(r'\s*\[Spring Video Atlas\]\s*$', '', source.stem).strip()
        if match:
            chapter_number, sequence = map(int, match.groups())
            chapter = chapters[chapter_number - 1]
            title = re.sub(r'^\d+\.\d+\.\s*', '', title)
            title = re.sub(r'\s+-\s+' + re.escape(chapter['englishTitle']) + r'\s*$', '', title)
            number = f'{chapter_number}.{sequence}'
            video_id = number
            name = f'{chapter_number:02}-{sequence:02}.mp4'
        else:
            supplements += 1
            chapter = chapters[-1]
            number, video_id = '', f'supplement-{supplements}'
            name = f'supplement-{supplements:02}.mp4'
        duration = float(metadata[source]['format']['duration'])
        entry = {'id': video_id, 'number': number, 'title': title, 'src': f'videos/{name}',
                 'duration': duration, 'originalName': source.name}
        chapter['videos'].append(entry)
        jobs.append((source, ROOT / entry['src']))
    for chapter in chapters:
        chapter['videos'].sort(key=lambda v: tuple(map(int, v['number'].split('.'))) if v['number'] else (99, int(v['id'].split('-')[-1])))
    catalog = {'chapters': chapters, 'totalVideos': len(originals),
               'totalDuration': sum(float(i['format']['duration']) for i in metadata.values())}
    (ROOT / 'library.js').write_text('window.VIDEO_LIBRARY = ' + json.dumps(catalog, ensure_ascii=False, indent=2) + ';\n', encoding='utf-8')
    print(f'Catalog ready: {len(originals)} videos', flush=True)
    report = []
    jobs.sort(key=lambda job: job[0].stat().st_size, reverse=True)
    for index, (source, output) in enumerate(jobs, 1):
        encoded = source.stat().st_size >= LIMIT
        reused = False
        if output.exists() and output.stat().st_mtime_ns >= source.stat().st_mtime_ns:
            try:
                validate(output, metadata[source], source)
                reused = True
            except (AssertionError, subprocess.CalledProcessError, ValueError, KeyError):
                pass
        if not reused:
            temporary = output.with_suffix('.partial.mp4')
            command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-y',
                       '-i', str(source), '-map', '0:v:0', '-map', '0:a?']
            command += ['-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-fps_mode', 'passthrough', '-c:a', 'copy'] if encoded else ['-c', 'copy']
            command += ['-movflags', '+faststart', str(temporary)]
            print(f'[{index}/{len(jobs)}] {"encode" if encoded else "remux"}: {source.name}', flush=True)
            subprocess.run(command, check=True)
            validate(temporary, metadata[source], source)
            temporary.replace(output)
        info = validate(output, metadata[source], source)
        report.append({'source': source.name, 'output': output.relative_to(ROOT).as_posix(),
                       'originalBytes': source.stat().st_size, 'outputBytes': output.stat().st_size,
                       'duration': float(info['format']['duration']),
                       'originalDuration': float(metadata[source]['format']['duration']), 'reencoded': encoded,
                       'reused': reused, 'faststart': True})
    (ROOT / '.qa' / 'media-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'videos': len(report), 'outputBytes': sum(r['outputBytes'] for r in report),
                      'chapters': [len(c['videos']) for c in chapters]}), flush=True)


if __name__ == '__main__':
    main()
