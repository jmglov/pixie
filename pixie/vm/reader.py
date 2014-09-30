import pixie.vm.object as object
from pixie.vm.primitives import nil, true, false
import pixie.vm.numbers as numbers
from pixie.vm.cons import cons
from pixie.vm.symbol import symbol, Symbol
from pixie.vm.keyword import keyword
from pixie.vm.protocols import *

class PlatformReader(object.Object):
    _type = object.Type("PlatformReader")

class StringReader(PlatformReader):

    def __init__(self, str):
        self._str = str
        self._idx = 0

    def read(self):
        if self._idx >= len(self._str):
            raise EOFError()
        ch = self._str[self._idx]
        self._idx += 1
        return ch

    def unread(self, ch):
        self._idx -= 1

class StreamReader(PlatformReader):
    def __init__(self, stream):
        self._steam = stream
        self._has_unread = False
        self._unread_ch = None

    def read(self):
        if self._has_unread:
            ch = self._unread_ch
            if ch == "":
                raise EOFError()
            self._has_unread = False
            return ch
        return self._steam.read(0)

    def unread(self, ch):
        assert not self._has_unread
        self._has_unread = True
        self._unread_ch = ch


def is_whitespace(ch):
    return ch in "\r\n\t ," or ch == ""

def is_digit(ch):
    return ch in "0123456789"

def eat_whitespace(rdr):
    while True:
        ch = rdr.read()
        if is_whitespace(ch):
            continue
        rdr.unread(ch)
        return


class ReaderHandler(__builtins__.object):
    def invoke(self, rdr, ch):
        pass

class ListReader(ReaderHandler):
    def invoke(self, rdr, ch):
        lst = []
        while True:
            eat_whitespace(rdr)
            ch = rdr.read()
            if ch == ")":
                acc = nil
                for x in range(len(lst) - 1, -1, -1):
                    acc = cons(lst[x], acc)
                return acc

            rdr.unread(ch)
            lst.append(read(rdr, True))

class UnmachedListReader(ReaderHandler):
    def invoke(self, rdr, ch):
        raise SyntaxError()

class QuoteReader(ReaderHandler):
    def invoke(self, rdr, ch):
        itm = read(rdr, True)
        return cons(symbol("quote"), cons(itm))

class KeywordReader(ReaderHandler):
    def invoke(self, rdr, ch):
        itm = read(rdr, True)
        assert isinstance(itm, Symbol)

        return keyword(itm._str)

handlers = {"(": ListReader(),
            ")": UnmachedListReader(),
            "'": QuoteReader(),
            ":": KeywordReader()}

def read_number(rdr, ch):
    acc = [ch]
    try:
        while True:
            ch = rdr.read()
            if is_whitespace(ch) or ch in handlers:
                rdr.unread(ch)
                break
            acc.append(ch)
    except EOFError:
        pass

    return numbers.Integer(int("".join(acc)))

def read_symbol(rdr, ch):
    acc = [ch]
    try:
        while True:
            ch = rdr.read()
            if is_whitespace(ch) or ch in handlers:
                rdr.unread(ch)
                break
            acc.append(ch)
    except EOFError:
        pass

    sym_str = "".join(acc)
    if sym_str == "true":
        return true
    if sym_str == "false":
        return false
    if sym_str == "nil":
        return nil
    return symbol(sym_str)

class EOF(object.Object):
    _type = object.Type("EOF")


eof = EOF()

def read(rdr, error_on_eof):
    try:
        eat_whitespace(rdr)
    except EOFError as ex:
        if error_on_eof:
            raise ex
        return eof



    ch = rdr.read()

    macro = handlers.get(ch, None)
    if macro is not None:
        return macro.invoke(rdr, ch)

    if is_digit(ch) or ch == "-":
        return read_number(rdr, ch)

    return read_symbol(rdr, ch)



