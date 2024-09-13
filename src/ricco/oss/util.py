import sys


def ensure_osspath_valid(_path: str):
  if _path.startswith('oss://') and not _path.startswith('oss:///'):
    _path = _path.replace('oss://', 'oss:///')
  return _path


def ensure_dir(_path: str):
  if _path == '' or not _path:
    return ''
  if _path.endswith('/'):
    return _path
  return f'{_path}/'


def bucket_from_path(_path):
  _path = ensure_osspath_valid(_path)
  _path = _path.lstrip('oss:///')
  return _path.split('/')[0]


def progress_bar(consumed, total):
  """进度条"""
  if total:
    rate = str(round(100 * (float(consumed) / float(total)), 2))
    print(f'\r传输中: {rate}% ', end='')
    sys.stdout.flush()
