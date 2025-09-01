def resolve_idx(idx: int, length: int) -> int:
  return idx + length if idx < 0 else idx

def capitalize_1st(s: str) -> str:
  return s[0].upper() + s[1:]
