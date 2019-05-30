# -*- coding: utf-8 -*-

"""Take notes straight from the command line."""
from tinydb import TinyDB, Query
from datetime import datetime
from uuid import uuid4
from pathlib import Path
import curses
from curses.textpad import Textbox, rectangle
import argparse
import pprint


DB_PATH = Path.home().joinpath(".cache/notes_cli/notes.json")
DB_PATH.parents[0].mkdir(exist_ok=True)
DB_PATH.touch(exist_ok=True)
db = TinyDB(DB_PATH.absolute())


def add_note(title: str, text: str):
    db.insert(
        dict(
            uid=str(uuid4().hex),
            title=title,
            text=text,
            created=datetime.now().isoformat(),
        )
    )


def search_notes(title: str = "", uid=None):
    if uid is None and len(title.strip()) == 0:
        raise TypeError("Please provide title of note")

    # @TODO: Clean up helper functions
    def title_match(val):
        return title.lower() in val.lower()

    def uid_match(val):
        return uid[:7] == val[:7]

    Note = Query()
    if uid:
        return db.search(Note.uid.test(uid_match))
    return db.search(Note.title.test(title_match))


def edit_note(uid: str, text: str):
    def uid_match(val):
        return uid[:7] == val[:7]

    Note = Query()
    db.update(
        {"text": text, "updated": str(datetime.now().isoformat())},
        Note.uid.test(uid_match),
    )


def edit_view(note=None, title=None):
    # @FIXME: Understand how newlines are treated in curses since textbox renders none
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.addstr(curses.LINES - 1, 0, "Hit 'Ctrl-G' to save and exit")

    editwin = curses.newwin(curses.LINES - 2, curses.COLS, 1, 0)
    if note:
        editwin.addstr(note['text'])
    stdscr.noutrefresh()

    box = Textbox(editwin)
    # Let the user edit until Ctrl-G is struck.
    box.edit()
    message = box.gather()
    stdscr.noutrefresh()
    editwin.noutrefresh()
    curses.doupdate()

    curses.endwin()

    if note:
        edit_note(note['uid'], message.strip())
    elif title:
        add_note(title, message.strip())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Take notes now")
    subparsers = parser.add_subparsers(dest='command')

    parser_add_note = subparsers.add_parser('add', help='Add a note')
    parser_add_note.add_argument('title', type=str, help='Set title of note')

    parser_edit_note = subparsers.add_parser('edit', help='Edit a note')
    parser_edit_note.add_argument('uid', type=str, help='Edit note with the uid')

    parser_search_note = subparsers.add_parser('ls', help="List/search notes")
    parser_search_note.add_argument('--title', type=str, help='List notes with matching title')
    parser_search_note.add_argument('--uid', type=str, help='List notes with matching uid')

    # @TODO: Add info argument

    args = parser.parse_args()

    if args.command == 'add':
        edit_view(title=args.title)
    elif args.command == 'edit':
        try:
            note = search_notes(uid=args.uid)[0]
        except IndexError:
            print(f"No note with uid '{args.uid}'")
        else:
            edit_view(note=note)
    elif args.command == 'ls':
        if args.title:
            results = search_notes(title=args.title)
            if len(results) == 0:
                print(f'No notes with title: {args.title}')
            else:
                pprint.pprint(results)
        elif args.uid:
            results = search_notes(uid=args.uid)
            if len(results) == 0:
                print(f'No notes with uid: {args.uid}')
            else:
                pprint.pprint(results)
        else:
            pprint.pprint(db.all())
