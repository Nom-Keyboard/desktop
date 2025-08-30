#!/usr/bin/env python
import argparse
import collections
import csv
import dataclasses
import io
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
text_area.bind('<Control-a>', select_all_text)
text_area.bind('<Control-equal>', change_text_size(2))
text_area.bind('<Control-minus>', change_text_size(-2))
text_area.bind('<Control-0>', change_text_size(default_font_size, relative=False))
text_area.focus_set()

(buffer_display := tkinter.Entry(state=tkinter.DISABLED, cursor=TK_CURSOR_ARROW)).pack(fill=tkinter.X)

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

tkinter.mainloop()
