#!/usr/bin/env python
import argparse
import collections
import csv
import dataclasses
import io
import string
import sys
import traceback
import typing

import tkinter
import tkinter.scrolledtext
import tkinter.font

import nomkb_alpha
import nomkb_appres
import nomkb_dict
import nomkb_ui_tk

TK_COLOR_GREEN = 'green'
TK_COLOR_RED = 'red'
TK_CURSOR_ARROW = 'arrow'
TK_CURSOR_HAND = 'hand2'
TK_KEY_0 = '0'
TK_KEY_BACKSPACE = 'BackSpace'
TK_KEY_ENTER = 'Return'
TK_KEY_ESC = 'Escape'
TK_KEY_HYPHEN = 'minus'
TK_KEY_SPACE = 'space'
TK_OVERRIDE_OLD_BEHAVIOR = 'break'
TK_TEXT_START = '1.0'

@dataclasses.dataclass(frozen=True)
class Word:
  nom_representation: str
  standard_representation: str

  def __str__(self) -> str:
    return f'{self.nom_representation} {self.standard_representation}'

def select_all_text(event: typing.Optional[tkinter.Event] = None) -> typing.Optional[str]:
  text_area.tag_add(tkinter.SEL, TK_TEXT_START, tkinter.END)
  # move cursor to beginning and go to it
  text_area.mark_set(tkinter.INSERT, TK_TEXT_START)
  text_area.see(tkinter.INSERT)

  return TK_OVERRIDE_OLD_BEHAVIOR

def change_text_size(val: int, relative: bool = True) -> ...:
  def inner(event: typing.Optional[tkinter.Event] = None) -> typing.Optional[str]:
    if (new_size := (text_font.cget('size') if relative else 0) + val) > 0:
      text_font.config(size=new_size)
    return TK_OVERRIDE_OLD_BEHAVIOR
  return inner

def toggle_kb(event: typing.Optional[tkinter.Event]) -> typing.Optional[str]:
  global kb_enabled

  if kb_enabled := not kb_enabled:
    pretty = 'On'
    color = TK_COLOR_GREEN
  else:
    pretty = 'Off'
    color = TK_COLOR_RED

  status_label.config(text=f'Keyboard {pretty}', fg=color)
  return TK_OVERRIDE_OLD_BEHAVIOR

def on_key(event: typing.Optional[tkinter.Event]) -> typing.Optional[str]:
  global buffer_size

  if not kb_enabled or event is None or event.type != tkinter.EventType.KeyPress:
    return

  has_buffer = buffer_size > 0
  if has_buffer and event.keysym == TK_KEY_ENTER:
    if list_view.get_page_count() == 0:
      text_area.insert(tkinter.INSERT, buffer_display.get())
      cleanup()
    else:
      try_select_completion(0)
    return TK_OVERRIDE_OLD_BEHAVIOR
  if event.keysym == TK_KEY_SPACE:
    if has_buffer:
      add_to_buffer_no_repeat(' ', extra_blacklist='-')
    else:
      text_area.insert(tkinter.INSERT, '　')
    return TK_OVERRIDE_OLD_BEHAVIOR
  if has_buffer and event.keysym == TK_KEY_BACKSPACE:
    with buffer_display_helper:
      buffer_display.delete(buffer_size - 1, tkinter.END)
    buffer_size -= 1
    update_completion_list()
    return TK_OVERRIDE_OLD_BEHAVIOR
  if has_buffer and event.keysym == TK_KEY_ESC:
    cleanup()
    return TK_OVERRIDE_OLD_BEHAVIOR
  if has_buffer and event.keysym == TK_KEY_HYPHEN:
    add_to_buffer_no_repeat('-', extra_blacklist=' ')
    return TK_OVERRIDE_OLD_BEHAVIOR
  if len(event.keysym) == 1:
    if event.keysym in string.ascii_letters:
      add_to_buffer(event.keysym)
      return TK_OVERRIDE_OLD_BEHAVIOR
    if has_buffer and event.keysym != TK_KEY_0 and event.keysym in string.digits:
      try_select_completion(int(event.keysym) - 1)
      return TK_OVERRIDE_OLD_BEHAVIOR

def change_completion_page(direction: int) -> ...:
  def inner(event: typing.Optional[tkinter.Event]) -> typing.Optional[str]:
    if (page_count := list_view.get_page_count()) < 1:
      return
    if (new_idx := list_view.get_page_idx() + direction) < 0 or not new_idx < page_count:
      return
    list_view.set_page_idx(new_idx)
    return TK_OVERRIDE_OLD_BEHAVIOR
  return inner

def try_select_completion(idx: int):
  if list_view.get_page_count() < 1:
    return
  try:
    word: Word = list_view.get_item_in_page(idx)
  except IndexError:
    return
  text_area.insert(tkinter.INSERT, word.nom_representation)
  cleanup()

def cleanup():
  global buffer_size
  with buffer_display_helper:
    buffer_display.delete(0, tkinter.END)
  buffer_size = 0
  list_view.clear()

def add_to_buffer(s: str):
  global buffer_size
  with buffer_display_helper:
    buffer_display.insert(tkinter.END, s)
  buffer_size += 1
  update_completion_list()

def update_completion_list():
  res = reverse_lookup_table.get(buffer_display.get(), None)
  if res is None:
    list_view.clear()
  else:
    list_view.set_data(list(res))

def add_to_buffer_no_repeat(s: str, extra_blacklist: str = ''):
  if not (last_char := buffer_display.get()[-1]) == s and last_char not in extra_blacklist:
    add_to_buffer(s)

def handle_punc(s: str) -> ...:
  def inner(event: typing.Optional[tkinter.Event]) -> typing.Optional[str]:
    if not kb_enabled:
      return
    text_area.insert(tkinter.INSERT, s)
    return TK_OVERRIDE_OLD_BEHAVIOR
  return inner

def handle_quotes(event: typing.Optional[tkinter.Event]) -> typing.Optional[str]:
  global in_quote
  if not kb_enabled:
    return
  text_area.insert(tkinter.INSERT, '”' if in_quote else '“')
  in_quote = not in_quote
  return TK_OVERRIDE_OLD_BEHAVIOR

ap = argparse.ArgumentParser()
ap.add_argument('-d', '--dict_file', required=True, type=argparse.FileType('rb'), help='path to the dictionary file to use')
args = ap.parse_args()

reverse_lookup_table: collections.defaultdict[str, set[Word]] = collections.defaultdict(set)
try:
  for nom_representation, standard_representation in csv.reader(io.TextIOWrapper(getattr(args, 'dict_file'), newline='', encoding='utf-8'), dialect=nomkb_dict.excel_tab_strict):
    reverse_lookup_table[nomkb_alpha.normalize(standard_representation)].add(Word(nom_representation, standard_representation))
except (csv.Error, UnicodeDecodeError, ValueError) as exc:
  traceback.print_exception(exc)
  print('Error parsing dictionary file, Bailing out.', file=sys.stderr)
  sys.exit(1)

(root := tkinter.Tk()).title('Nôm Keyboard')
root.iconphoto(True, tkinter.PhotoImage(data=nomkb_appres.ICON_DATA))

(status_label := tkinter.Label(cursor=TK_CURSOR_HAND)).pack(fill=tkinter.X)
status_label.bind('<Button-1>', toggle_kb)

(text_font := tkinter.font.Font(family='Nom Na Tong')).config(size=(default_font_size := text_font.actual()['size']))

(text_area := tkinter.scrolledtext.ScrolledText(font=text_font, undo=True)).pack(expand=True, fill=tkinter.BOTH)
text_area.bind('<comma>', handle_punc('，'))
text_area.bind('<period>', handle_punc('。'))
text_area.bind('<question>', handle_punc('？'))
text_area.bind('<exclam>', handle_punc('！'))
text_area.bind('<parenleft>', handle_punc('（'))
text_area.bind('<parenright>', handle_punc('）'))
text_area.bind('<colon>', handle_punc('：'))
text_area.bind('<semicolon>', handle_punc('；'))
text_area.bind('<quotedbl>', handle_quotes)
text_area.bind('<Tab>', toggle_kb)
text_area.bind('<Key>', on_key)
text_area.bind('<Control-a>', select_all_text)
text_area.bind('<Control-equal>', change_text_size(2))
text_area.bind('<Control-minus>', change_text_size(-2))
text_area.bind('<Control-0>', change_text_size(default_font_size, relative=False))
text_area.bind('<Control-Page_Up>', change_completion_page(-1))
text_area.bind('<Control-Page_Down>', change_completion_page(1))
text_area.focus_set()

(buffer_display := tkinter.Entry(state=tkinter.DISABLED, cursor=TK_CURSOR_ARROW)).pack(fill=tkinter.X)
buffer_display_helper = nomkb_ui_tk.TkReadOnlyWidgetModifyHelper(buffer_display)

(list_view := nomkb_ui_tk.PagedListTk(root, 9)).tk_container.pack(fill=tkinter.X)
list_view.tk_listbox.config(font=text_font)

# make window size explicit
root.update()
root.geometry(f'{root.winfo_width()}x{root.winfo_height()}')

# allow widget to auto-shrink
text_area.config(width=0, height=0)

root.minsize(root.winfo_width(), root.winfo_height())

kb_enabled = False
toggle_kb(None)

buffer_size = 0
in_quote = False

tkinter.mainloop()
