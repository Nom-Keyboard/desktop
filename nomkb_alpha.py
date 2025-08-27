_map: dict[str, str] = {}

for _a, _b in ((('àáạảã', 'ăằắặẳẵ', 'âầấậẩẫ'), 'a'),
               (('đ'    ,                   ), 'd'),
               (('èéẹẻẽ', 'êềếệểễ',         ), 'e'),
               (('ìíịỉĩ',                   ), 'i'),
               (('òóọỏõ', 'ôồốộổỗ', 'ơờớợởỡ'), 'o'),
               (('ùúụủũ', 'ưừứựửữ',         ), 'u'),
               (('ỳýỵỷỹ',                   ), 'y')):
  for _x in _a:
    for _f in (lambda s: s, lambda s: s.upper()):
      _map.update(dict.fromkeys(_f(_x), _f(_b)))

del _a, _b, _x, _f

_tl = str.maketrans(_map)
del _map

def normalize(s: str) -> str:
  return s.translate(_tl)
