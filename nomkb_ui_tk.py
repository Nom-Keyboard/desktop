import types
import typing

import tkinter

import nomkb_utils

class TkReadOnlyWidgetModifyHelper:
  def __init__(self, widget: ...):
    self._widget = widget
    self._last_state = ''

  def __enter__(self) -> typing.Any:
    self._last_state = self._widget.cget('state')
    self._widget.config(state=tkinter.NORMAL)

  def __exit__(self, exc_type: typing.Optional[type[BaseException]], exc_value: typing.Optional[BaseException], traceback: types.TracebackType) -> typing.Optional[bool]:
    self._widget.config(state=self._last_state)

class PagedListTk:
  _INVALID_PAGE = -1

  def __init__(self, parent: ..., n: int):
    assert n > 0, 'n must be positive'

    (label := tkinter.Label(container := tkinter.Frame(parent))).pack()
    (listbox := tkinter.Listbox(container, height=n, state=tkinter.DISABLED)).pack(fill=tkinter.BOTH, expand=True)

    self._container = container
    self._label = label
    self._listbox = listbox
    self._listbox_helper = TkReadOnlyWidgetModifyHelper(listbox)

    self._n = n
    self._page_data: list[list[typing.Any]] = []
    self._page = self._INVALID_PAGE
    self._dirty = False

  def _clean(self):
    with self._listbox_helper:
      self._listbox.delete(0, tkinter.END)

  def _populate(self, page_data: list[typing.Any]):
    with self._listbox_helper:
      for i, x in enumerate(page_data, start=1):
        self._listbox.insert(tkinter.END, f'{i} {x}')

  def _update_page_data(self, data: list[typing.Any]):
    self._page_data = [data[i:i + self._n] for i in range(0, len(data), self._n)]

  def _update_label(self):
    self._label.config(text=f'Showing {self.get_page_idx() + 1} of {self.get_page_count()} page(s)')

  def clear(self):
    if not self._dirty:
      return
    self._page_data = []
    self._page = self._INVALID_PAGE
    self._dirty = False
    self._label.config(text='')
    self._clean()

  def get_page_count(self) -> int:
    return len(self._page_data)

  def get_page_idx(self) -> int:
    assert self._page != self._INVALID_PAGE, 'Necessary to call .set_data() first'
    return self._page

  def set_page_idx(self, page: int, _force: bool = False):
    try:
      if page == self.get_page_idx() and not _force:
        return
    except AssertionError:
      pass
    d = self._page_data[page]
    self._clean()
    self._page = nomkb_utils.resolve_idx(page, self.get_page_count())
    self._update_label()
    self._populate(d)

  def set_data(self, data: list[typing.Any]):
    assert len(data) > 0, 'Use .clear() instead of providing an empty list'
    self._update_page_data(data)
    self.set_page_idx(0, _force=True)
    self._dirty = True

  @property
  def tk_listbox(self) -> tkinter.Listbox:
    return self._listbox

  @property
  def tk_label(self) -> tkinter.Label:
    return self._label

  @property
  def tk_container(self) -> tkinter.Frame:
    return self._container

  def get_item_in_page(self, idx: int) -> typing.Any:
    return self._page_data[self.get_page_idx()][idx]
