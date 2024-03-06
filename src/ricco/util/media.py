import logging


def get_mp3_metadata(file_path):
  """获取MP3文件中的元数据信息"""

  def _get_v(dic, key):
    v = dic.get(key)
    if not v:
      return
    if isinstance(v, list):
      return '、'.join(v)
    return v

  from mutagen.easyid3 import EasyID3  # noqa

  try:
    audio = EasyID3(file_path)
  except Exception as e:
    logging.warning(f'Error: {e}')
    return {
      '标题': None, '艺术家': None, '专辑': None, '发行年份': None,
    }

  return {
    '标题': _get_v(audio, 'title'),
    '艺术家': _get_v(audio, 'artist'),
    '专辑': _get_v(audio, 'album'),
    '发行年份': _get_v(audio, 'date'),
  }
