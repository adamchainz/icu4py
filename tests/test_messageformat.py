from __future__ import annotations

from icu import MessageFormat


class TestMessageFormat:
    def test_simple_string_substitution(self):
        pattern = "Hello, {name}!"
        fmt = MessageFormat(pattern, "en_US")

        assert fmt.format({"name": "World"}) == "Hello, World!"
        assert fmt.format({"name": "Alice"}) == "Hello, Alice!"

    def test_multiple_string_substitution(self):
        pattern = "{greeting}, {name}! Welcome to {place}."
        fmt = MessageFormat(pattern, "en_US")

        result = fmt.format({"greeting": "Hello", "name": "Bob", "place": "Earth"})
        assert result == "Hello, Bob! Welcome to Earth."

    def test_string_with_special_characters(self):
        pattern = "Message: {text}"
        fmt = MessageFormat(pattern, "en_US")

        assert fmt.format({"text": "Hello's world"}) == "Message: Hello's world"
        assert fmt.format({"text": 'Quote: "test"'}) == 'Message: Quote: "test"'

    def test_simple_integer_substitution(self):
        pattern = "You have {count} messages."
        fmt = MessageFormat(pattern, "en_US")

        assert fmt.format({"count": 0}) == "You have 0 messages."
        assert fmt.format({"count": 42}) == "You have 42 messages."
        assert fmt.format({"count": -5}) == "You have -5 messages."

    def test_integer_number_formatting(self):
        pattern = "Total: {amount, number}"
        fmt = MessageFormat(pattern, "en_US")

        assert fmt.format({"amount": 1000}) == "Total: 1,000"
        assert fmt.format({"amount": 1234567}) == "Total: 1,234,567"

    def test_integer_number_formatting_locales(self):
        pattern = "Amount: {value, number}"

        # US uses comma as thousands separator
        fmt_us = MessageFormat(pattern, "en_US")
        assert fmt_us.format({"value": 1234567}) == "Amount: 1,234,567"

        # French uses non-breaking space as thousands separator
        fmt_fr = MessageFormat(pattern, "fr_FR")
        result_fr = fmt_fr.format({"value": 1234567})
        assert result_fr == "Amount: 1\u202f234\u202f567"

    def test_large_integers(self):
        pattern = "Big number: {num}"
        fmt = MessageFormat(pattern, "en_US")

        assert (
            fmt.format({"num": 9223372036854775807})
            == "Big number: 9,223,372,036,854,775,807"
        )

    def test_simple_float_substitution(self):
        pattern = "Price: {price}"
        fmt = MessageFormat(pattern, "en_US")

        assert fmt.format({"price": 19.99}) == "Price: 19.99"
        assert fmt.format({"price": 0.5}) == "Price: 0.5"
        assert fmt.format({"price": -3.14}) == "Price: -3.14"

    def test_float_number_formatting(self):
        pattern = "Value: {amount, number}"
        fmt = MessageFormat(pattern, "en_US")

        result = fmt.format({"amount": 1234.56})
        assert result == "Value: 1,234.56"

    def test_float_with_many_decimals(self):
        pattern = "Pi: {pi}"
        fmt = MessageFormat(pattern, "en_US")

        result = fmt.format({"pi": 3.14159265359})
        assert result == "Pi: 3.142"

    def test_float_zero_and_negative(self):
        pattern = "Temperature: {temp}"
        fmt = MessageFormat(pattern, "en_US")

        assert fmt.format({"temp": 0.0}) == "Temperature: 0"
        assert fmt.format({"temp": -0.5}) == "Temperature: -0.5"

    def test_simple_plural(self):
        """Test basic plural formatting."""
        pattern = "{count, plural, =0 {no items} =1 {one item} other {# items}}"
        fmt = MessageFormat(pattern, "en_US")

        assert fmt.format({"count": 0}) == "no items"
        assert fmt.format({"count": 1}) == "one item"
        assert fmt.format({"count": 5}) == "5 items"

    def test_plural_with_offset(self):
        pattern = (
            "{num_guests, plural, offset:1 "
            "=0 {{host} does not give a party.}"
            "=1 {{host} invites {guest} to the party.}"
            "=2 {{host} invites {guest} and one other person to the party.}"
            "other {{host} invites {guest} and # other people to the party.}}"
        )
        fmt = MessageFormat(pattern, "en_US")

        result = fmt.format({"num_guests": 0, "host": "Alice", "guest": "Bob"})
        assert result == "Alice does not give a party."

        result = fmt.format({"num_guests": 1, "host": "Alice", "guest": "Bob"})
        assert result == "Alice invites Bob to the party."

        result = fmt.format({"num_guests": 5, "host": "Alice", "guest": "Bob"})
        assert result == "Alice invites Bob and 4 other people to the party."

    def test_plural_categories(self):
        pattern = "{count, plural, one {# item} other {# items}}"
        fmt = MessageFormat(pattern, "en_US")

        assert fmt.format({"count": 1}) == "1 item"
        assert fmt.format({"count": 0}) == "0 items"
        assert fmt.format({"count": 2}) == "2 items"
        assert fmt.format({"count": 100}) == "100 items"

    def test_plural_with_floats(self):
        pattern = "{count, plural, =1 {one item} other {# items}}"
        fmt = MessageFormat(pattern, "en_US")

        assert fmt.format({"count": 1.0}) == "one item"
        assert fmt.format({"count": 2.5}) == "2.5 items"

    def test_plural_different_locale(self):
        pattern = (
            "{count, plural, one {# день} few {# дня} many {# дней} other {# дня}}"
        )
        fmt = MessageFormat(pattern, "ru_RU")

        result = fmt.format({"count": 1})
        assert result == "1 день"

        result = fmt.format({"count": 2})
        assert result == "2 дня"

    def test_simple_select(self):
        pattern = "{gender, select, male {He} female {She} other {They}} said hello."
        fmt = MessageFormat(pattern, "en_US")

        assert fmt.format({"gender": "male"}) == "He said hello."
        assert fmt.format({"gender": "female"}) == "She said hello."
        assert fmt.format({"gender": "other"}) == "They said hello."
        assert fmt.format({"gender": "unknown"}) == "They said hello."

    def test_select_with_variable_substitution(self):
        pattern = "{gender, select, male {{name} is a man} female {{name} is a woman} other {{name} is a person}}."
        fmt = MessageFormat(pattern, "en_US")

        assert fmt.format({"gender": "male", "name": "John"}) == "John is a man."
        assert fmt.format({"gender": "female", "name": "Jane"}) == "Jane is a woman."
        assert fmt.format({"gender": "other", "name": "Alex"}) == "Alex is a person."

    def test_select_case_sensitive(self):
        pattern = (
            "{status, select, active {Active} inactive {Inactive} other {Unknown}}"
        )
        fmt = MessageFormat(pattern, "en_US")

        assert fmt.format({"status": "active"}) == "Active"
        assert fmt.format({"status": "Active"}) == "Unknown"
        assert fmt.format({"status": "ACTIVE"}) == "Unknown"

    def test_selectordinal_english(self):
        pattern = "You came in {place, selectordinal, one {#st} two {#nd} few {#rd} other {#th}} place!"
        fmt = MessageFormat(pattern, "en_US")

        assert fmt.format({"place": 1}) == "You came in 1st place!"
        assert fmt.format({"place": 2}) == "You came in 2nd place!"
        assert fmt.format({"place": 3}) == "You came in 3rd place!"
        assert fmt.format({"place": 4}) == "You came in 4th place!"
        assert fmt.format({"place": 11}) == "You came in 11th place!"
        assert fmt.format({"place": 21}) == "You came in 21st place!"
        assert fmt.format({"place": 22}) == "You came in 22nd place!"
        assert fmt.format({"place": 23}) == "You came in 23rd place!"

    def test_selectordinal_with_offset(self):
        pattern = "{rank, selectordinal, offset:1 one {You're #st after the winner!} two {You're #nd after the winner!} few {You're #rd after the winner!} other {You're #th after the winner!}}"
        fmt = MessageFormat(pattern, "en_US")

        result = fmt.format({"rank": 2})
        assert result == "You're 1st after the winner!"

        result = fmt.format({"rank": 3})
        assert result == "You're 2nd after the winner!"

    def test_nested_plural_and_select(self):
        pattern = (
            "{gender, select, "
            "male {{count, plural, one {He has # item} other {He has # items}}} "
            "female {{count, plural, one {She has # item} other {She has # items}}} "
            "other {{count, plural, one {They have # item} other {They have # items}}}}"
        )
        fmt = MessageFormat(pattern, "en_US")

        assert fmt.format({"gender": "male", "count": 1}) == "He has 1 item"
        assert fmt.format({"gender": "male", "count": 5}) == "He has 5 items"
        assert fmt.format({"gender": "female", "count": 1}) == "She has 1 item"
        assert fmt.format({"gender": "female", "count": 5}) == "She has 5 items"
        assert fmt.format({"gender": "other", "count": 1}) == "They have 1 item"

    def test_multiple_plurals(self):
        pattern = "{apples, plural, one {# apple} other {# apples}} and {oranges, plural, one {# orange} other {# oranges}}"
        fmt = MessageFormat(pattern, "en_US")

        assert fmt.format({"apples": 1, "oranges": 1}) == "1 apple and 1 orange"
        assert fmt.format({"apples": 1, "oranges": 5}) == "1 apple and 5 oranges"
        assert fmt.format({"apples": 3, "oranges": 1}) == "3 apples and 1 orange"
        assert fmt.format({"apples": 3, "oranges": 5}) == "3 apples and 5 oranges"

    def test_mixed_types_in_pattern(self):
        pattern = "{name} scored {points, number} points with an average of {average} per game."
        fmt = MessageFormat(pattern, "en_US")

        result = fmt.format({"name": "Alice", "points": 1250, "average": 25.5})
        assert result == "Alice scored 1,250 points with an average of 25.5 per game."

    def test_complex_nested_structure(self):
        pattern = (
            "{name} {action, select, "
            "bought {bought {count, plural, one {# item} other {# items}}} "
            "sold {sold {count, plural, one {# item} other {# items}}} "
            "other {processed {count} items}} "
            "for {price, number} dollars."
        )
        fmt = MessageFormat(pattern, "en_US")

        result = fmt.format(
            {"name": "John", "action": "bought", "count": 1, "price": 50}
        )
        assert result == "John bought 1 item for 50 dollars."

        result = fmt.format(
            {"name": "Jane", "action": "sold", "count": 10, "price": 500}
        )
        assert result == "Jane sold 10 items for 500 dollars."

    def test_empty_pattern(self):
        pattern = ""
        fmt = MessageFormat(pattern, "en_US")

        assert fmt.format({}) == ""

    def test_pattern_with_no_variables(self):
        pattern = "This is a static message."
        fmt = MessageFormat(pattern, "en_US")

        assert fmt.format({}) == "This is a static message."

    def test_escaped_braces(self):
        pattern = "Use '{' and '}' to denote variables like {var}."
        fmt = MessageFormat(pattern, "en_US")

        result = fmt.format({"var": "test"})
        assert "test" in result
        assert "{" in result
        assert "}" in result

    def test_unicode_characters(self):
        pattern = "{greeting} {name}! 你好 {chinese_name}!"
        fmt = MessageFormat(pattern, "en_US")

        result = fmt.format(
            {"greeting": "Hello", "name": "Alice", "chinese_name": "李明"}
        )
        assert result == "Hello Alice! 你好 李明!"

    def test_emoji_in_strings(self):
        pattern = "Status: {status} {emoji}"
        fmt = MessageFormat(pattern, "en_US")

        result = fmt.format({"status": "Happy", "emoji": "😊"})
        assert result == "Status: Happy 😊"

    def test_different_locales_number_formatting(self):
        pattern = "Price: {price, number}"

        fmt_us = MessageFormat(pattern, "en_US")
        result_us = fmt_us.format({"price": 1234.56})
        assert "1,234" in result_us  # US uses comma

        fmt_de = MessageFormat(pattern, "de_DE")
        result_de = fmt_de.format({"price": 1234.56})
        assert result_de == "Price: 1.234,56"

    def test_locale_plural_rules(self):
        # English: one vs other
        pattern = "{n, plural, one {# book} other {# books}}"
        fmt_en = MessageFormat(pattern, "en_US")

        assert fmt_en.format({"n": 1}) == "1 book"
        assert fmt_en.format({"n": 2}) == "2 books"

    def test_integer_in_float_context(self):
        pattern = "Value: {val, number}"
        fmt = MessageFormat(pattern, "en_US")

        assert fmt.format({"val": 100}) == "Value: 100"
        assert fmt.format({"val": 100.5}) == "Value: 100.5"

    def test_float_in_plural(self):
        pattern = "{hours, plural, one {# hour} other {# hours}}"
        fmt = MessageFormat(pattern, "en_US")

        assert fmt.format({"hours": 1.0}) == "1 hour"
        assert fmt.format({"hours": 1.5}) == "1.5 hours"
        assert fmt.format({"hours": 2.5}) == "2.5 hours"
