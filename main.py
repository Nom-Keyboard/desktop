#!/usr/bin/env python
import argparse
import typing

import tkinter
import tkinter.scrolledtext
import tkinter.font

TK_OVERRIDE_OLD_BEHAVIOR = 'break'
TK_TEXT_START = '1.0'

def select_all_text(event: typing.Optional[tkinter.Event] = None) -> str:
  text_area.tag_add(tkinter.SEL, TK_TEXT_START, tkinter.END)
  # move cursor to beginning and go to it
  text_area.mark_set(tkinter.INSERT, TK_TEXT_START)
  text_area.see(tkinter.INSERT)

  return TK_OVERRIDE_OLD_BEHAVIOR

def change_text_size(val: int, relative: bool = True) -> ...:
  def inner(event: typing.Optional[tkinter.Event] = None) -> str:
    text_font.config(size=(text_font.cget('size') if relative else 0) + val)
    return TK_OVERRIDE_OLD_BEHAVIOR
  return inner

ap = argparse.ArgumentParser()
ap.add_argument('-d', '--dict_file', required=True, type=argparse.FileType('rb'), help='path to the dictionary file to use')
args = ap.parse_args()

(root := tkinter.Tk()).title('Nôm Keyboard')

(text_area := tkinter.scrolledtext.ScrolledText(font=(text_font := tkinter.font.Font(family='Nom Na Tong', size=24)), undo=True)).pack(expand=True, fill=tkinter.BOTH)
text_area.bind('<Control-a>', select_all_text)
text_area.bind('<Control-equal>', change_text_size(2))
text_area.bind('<Control-minus>', change_text_size(-2))
text_area.bind('<Control-0>', change_text_size(text_font.cget('size'), relative=False))
text_area.focus_set()

# make window size explicit
root.update()
root.geometry(f'{root.winfo_width()}x{root.winfo_height()}')

tkinter.mainloop()
