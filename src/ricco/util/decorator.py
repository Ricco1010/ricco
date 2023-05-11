def to_str(func):
  def wrapper(self):
    if self.dst_format:
      return func(self).strftime(self.dst_format)
    else:
      return func(self)

  return wrapper
