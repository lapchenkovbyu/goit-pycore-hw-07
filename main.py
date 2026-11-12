"""Address book bot: contacts with phones and birthdays, upcoming greetings."""

from collections import UserDict
from datetime import date, datetime, timedelta
from typing import Callable, Optional

DATE_FORMAT = "%d.%m.%Y"
DAYS_AHEAD = 7
NOT_FOUND_ERROR = "Contact not found."
USAGE = {
    "add_contact": "Give me name and phone please.",
    "change_contact": "Give me name, old phone and new phone please.",
    "show_phone": "Give me name please.",
    "add_birthday": "Give me name and birthday (DD.MM.YYYY) please.",
    "show_birthday": "Give me name please.",
}


class Field:
    """Base class for record fields."""

    def __init__(self, value) -> None:
        self.value = value

    def __str__(self) -> str:
        return str(self.value)


class Name(Field):
    """Required contact name. Must not be empty."""

    def __init__(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("Name must not be empty.")
        super().__init__(value.strip())


class Phone(Field):
    """Phone number. Must be exactly 10 digits."""

    def __init__(self, value: str) -> None:
        if not (value.isascii() and value.isdigit() and len(value) == 10):
            raise ValueError("Phone number must contain exactly 10 digits.")
        super().__init__(value)


class Birthday(Field):
    """Birthday given as DD.MM.YYYY and stored as a date."""

    def __init__(self, value: str) -> None:
        try:
            if len(value) != 10:  # strptime also accepts "5.3.2000"
                raise ValueError
            parsed = datetime.strptime(value, DATE_FORMAT).date()
        except (ValueError, TypeError):
            raise ValueError("Invalid date format. Use DD.MM.YYYY") from None
        super().__init__(parsed)

    def __str__(self) -> str:
        return self.value.strftime(DATE_FORMAT)


class Record:
    """Contact record: one name, a list of phones and an optional birthday."""

    def __init__(self, name: str) -> None:
        self.name = Name(name)
        self.phones: list[Phone] = []
        self.birthday: Optional[Birthday] = None

    def add_phone(self, phone: str) -> None:
        """Validate and add a phone number."""
        self.phones.append(Phone(phone))

    def remove_phone(self, phone: str) -> None:
        """Remove a phone number. Raises ValueError if it is not found."""
        found = self.find_phone(phone)
        if found is None:
            raise ValueError(f"Phone {phone} not found.")
        self.phones.remove(found)

    def edit_phone(self, old_phone: str, new_phone: str) -> None:
        """Replace old_phone with new_phone.

        Raises ValueError if old_phone is not found or new_phone is invalid;
        the record is left unchanged in both cases.
        """
        found = self.find_phone(old_phone)
        if found is None:
            raise ValueError(f"Phone {old_phone} not found.")
        new = Phone(new_phone)  # validate before touching the list
        self.phones[self.phones.index(found)] = new

    def find_phone(self, phone: str) -> Optional[Phone]:
        """Return the Phone object with this number, or None."""
        for item in self.phones:
            if item.value == phone:
                return item
        return None

    def add_birthday(self, value: str) -> None:
        """Set the birthday (replaces an existing one). ValueError if invalid."""
        self.birthday = Birthday(value)

    def __str__(self) -> str:
        text = (
            f"Contact name: {self.name.value}, "
            f"phones: {'; '.join(p.value for p in self.phones)}"
        )
        if self.birthday:
            text += f", birthday: {self.birthday}"
        return text


def _birthday_in_year(birthday: date, year: int) -> date:
    """Return the birthday in `year`; Feb 29 becomes Mar 1 in non-leap years."""
    try:
        return birthday.replace(year=year)
    except ValueError:
        return date(year, 3, 1)


class AddressBook(UserDict):
    """Address book: records keyed by contact name."""

    def add_record(self, record: Record) -> None:
        """Add a record (replaces an existing one with the same name)."""
        self.data[record.name.value] = record

    def find(self, name: str) -> Optional[Record]:
        """Return the record for name, or None."""
        return self.data.get(name)

    def delete(self, name: str) -> None:
        """Delete the record for name. Does nothing if it is absent."""
        self.data.pop(name, None)

    def get_upcoming_birthdays(self, today: Optional[date] = None) -> list[dict]:
        """Return who to congratulate from today up to 7 days ahead (inclusive).

        A birthday on Saturday or Sunday is congratulated on the next Monday.
        Result items: {"name": str, "congratulation_date": "DD.MM.YYYY"}.
        """
        today = today or date.today()
        upcoming = []

        for record in self.data.values():
            if record.birthday is None:
                continue

            birthday = _birthday_in_year(record.birthday.value, today.year)
            if birthday < today:
                birthday = _birthday_in_year(record.birthday.value, today.year + 1)

            if (birthday - today).days > DAYS_AHEAD:
                continue

            if birthday.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
                birthday += timedelta(days=7 - birthday.weekday())

            upcoming.append({
                "name": record.name.value,
                "congratulation_date": birthday.strftime(DATE_FORMAT),
            })

        return upcoming


def input_error(func: Callable[..., str]) -> Callable[..., str]:
    """Catch input errors of a command handler and return a user message."""

    def inner(*args, **kwargs) -> str:
        try:
            return func(*args, **kwargs)
        except KeyError:
            return NOT_FOUND_ERROR
        except ValueError as error:
            return str(error)
        except IndexError:
            return USAGE.get(func.__name__, "Not enough arguments.")

    return inner


def parse_input(user_input: str) -> tuple[str, ...]:
    """Split input into a lowercase command and its arguments."""
    parts = user_input.split()
    if not parts:
        return ("",)
    cmd, *args = parts
    return cmd.strip().lower(), *args


def _get_record(name: str, book: AddressBook) -> Record:
    """Return the record for name. Raises KeyError if there is none."""
    record = book.find(name)
    if record is None:
        raise KeyError(name)
    return record


@input_error
def add_contact(args: list[str], book: AddressBook) -> str:
    """add [name] [phone]: add a contact or a phone to an existing one."""
    name, phone = args[0], args[1]  # IndexError if missing
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        message = "Contact added."
    record.add_phone(phone)  # validate before storing a new record
    book.add_record(record)
    return message


@input_error
def change_contact(args: list[str], book: AddressBook) -> str:
    """change [name] [old phone] [new phone]: replace a phone number."""
    name, old_phone, new_phone = args[0], args[1], args[2]
    _get_record(name, book).edit_phone(old_phone, new_phone)
    return "Contact updated."


@input_error
def show_phone(args: list[str], book: AddressBook) -> str:
    """phone [name]: return the phones of a contact."""
    record = _get_record(args[0], book)
    return "; ".join(p.value for p in record.phones) or "No phones saved."


@input_error
def show_all(book: AddressBook) -> str:
    """all: return every saved contact, one per line."""
    if not book.data:
        return "No contacts saved."
    return "\n".join(str(record) for record in book.data.values())


@input_error
def add_birthday(args: list[str], book: AddressBook) -> str:
    """add-birthday [name] [DD.MM.YYYY]: set the birthday of a contact."""
    name, birthday = args[0], args[1]
    _get_record(name, book).add_birthday(birthday)
    return "Birthday added."


@input_error
def show_birthday(args: list[str], book: AddressBook) -> str:
    """show-birthday [name]: return the birthday of a contact."""
    record = _get_record(args[0], book)
    return str(record.birthday) if record.birthday else "Birthday is not set."


@input_error
def birthdays(book: AddressBook) -> str:
    """birthdays: who to congratulate in the next 7 days."""
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No birthdays in the next week."
    return "\n".join(f"{u['name']}: {u['congratulation_date']}" for u in upcoming)


def main() -> None:
    book = AddressBook()
    print("Welcome to the assistant bot!")
    while True:
        try:
            user_input = input("Enter a command: ")
        except (KeyboardInterrupt, EOFError):
            print("\nGood bye!")
            break
        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Good bye!")
            break
        elif command == "":
            continue
        elif command == "hello":
            print("How can I help you?")
        elif command == "add":
            print(add_contact(args, book))
        elif command == "change":
            print(change_contact(args, book))
        elif command == "phone":
            print(show_phone(args, book))
        elif command == "all":
            print(show_all(book))
        elif command == "add-birthday":
            print(add_birthday(args, book))
        elif command == "show-birthday":
            print(show_birthday(args, book))
        elif command == "birthdays":
            print(birthdays(book))
        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()
