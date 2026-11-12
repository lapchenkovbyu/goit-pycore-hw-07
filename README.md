# GoIT Python Core, Homework 07 (Topic 10: advanced OOP)

Standard library only, Python 3.10+.

Console assistant bot on top of the address book from homework 06, extended with birthdays.

| File | Description | Run |
|------|-------------|-----|
| main.py | `Field`, `Name`, `Phone`, `Birthday`, `Record`, `AddressBook` and the CLI bot | `python main.py` |

Commands:

| Command | Description |
|---------|-------------|
| `hello` | Greeting |
| `add [name] [phone]` | Add a new contact, or a phone to an existing one |
| `change [name] [old phone] [new phone]` | Replace a phone number |
| `phone [name]` | Show the phones of a contact |
| `all` | Show all contacts |
| `add-birthday [name] [DD.MM.YYYY]` | Set the birthday of a contact |
| `show-birthday [name]` | Show the birthday of a contact |
| `birthdays` | Show who to congratulate in the next 7 days |
| `close` / `exit` | Leave the bot |

Behaviour:
- `Phone`: must be exactly 10 digits, otherwise `ValueError`.
- `Birthday`: parsed with `datetime.strptime` (`DD.MM.YYYY`), stored as a `date`; bad input raises `ValueError("Invalid date format. Use DD.MM.YYYY")`.
- `Record.add_birthday(value)`: sets the only birthday, adding again replaces it.
- `AddressBook.get_upcoming_birthdays(today=None)`: birthdays from today up to and including 7 days ahead; a Saturday or Sunday birthday is congratulated on the next Monday; a birthday already passed this year counts for next year; Feb 29 becomes Mar 1 in non-leap years. Returns `{"name", "congratulation_date": "DD.MM.YYYY"}` items.
- `@input_error` turns `ValueError` (validation messages), `IndexError` (missing arguments) and `KeyError` (unknown contact) into user messages, so the bot never crashes on bad input.
- Empty input is ignored; unknown commands print `Invalid command.`; Ctrl+C or Ctrl+D print `Good bye!` and exit cleanly.
- Contact names are case-sensitive.
