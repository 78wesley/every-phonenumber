from fasthtml.common import *
import phonenumbers
import peewee as pw
import os
import urllib.parse
import phonenumbers.carrier
import phonenumbers.geocoder
import phonenumbers.timezone
import iso_list
from collections import OrderedDict


# TODO take a look at this chatgpt chat: https://chatgpt.com/c/684c6e2a-85c4-8008-8d19-73d53d89b78c


app = FastHTML(debug=True, hdrs=picolink, title="LibPhoneX - Every Phone Number")
rt = app.route

# SQLite database
# Ensure the 'databases' directory exists
if not os.path.exists("databases"):
    os.makedirs("databases")
db = pw.SqliteDatabase("databases/libphonex.db")


# Models
class BaseModel(pw.Model):
    class Meta:
        database = db


def create_phone_number_model(country_code):
    class Meta:
        database = db
        table_name = f"phone_numbers_{country_code.lower()}"

    attrs = {
        "country_code": pw.CharField(),
        "international_prefix": pw.CharField(null=True),
        "national_number": pw.CharField(),
        "type": pw.CharField(null=True),
        "is_valid": pw.BooleanField(),
        "notes": pw.TextField(null=True),
        "Meta": Meta,
    }

    PhoneNumber = type("PhoneNumber", (BaseModel,), attrs)
    return PhoneNumber


class ValidationRule(BaseModel):
    country_code = pw.CharField()
    type = pw.CharField()
    regex = pw.CharField()
    example = pw.CharField(null=True)
    description = pw.TextField(null=True)


class Issue(BaseModel):
    phone_number = pw.CharField()
    reason = pw.TextField()
    reported_at = pw.DateTimeField(constraints=[pw.SQL("DEFAULT CURRENT_TIMESTAMP")])
    status = pw.CharField(default="open")
    resolution_notes = pw.TextField(null=True)


# Setup
def setup_database(country_code):
    db.connect()
    PhoneNumber = create_phone_number_model(country_code)
    db.create_tables([PhoneNumber, ValidationRule, Issue], safe=True)

    if not ValidationRule.select().where((ValidationRule.country_code == country_code) & (ValidationRule.type == "mobile") & (ValidationRule.regex == "^6\\d{8}$")).exists():
        ValidationRule.create(country_code=country_code, type="mobile", regex="^6\\d{8}$", example="612345678", description="Standaard mobiel nummer in Nederland")

    if not PhoneNumber.select().where((PhoneNumber.country_code == country_code) & (PhoneNumber.national_number == "612345678")).exists():
        PhoneNumber.create(country_code=country_code, international_prefix="+31", national_number="612345678", type="mobile", is_valid=True, notes="Typisch geldig mobiel nummer")

    if not Issue.select().where(Issue.phone_number == "+31600000000").exists():
        Issue.create(phone_number="+31600000000", reason="Nummer wordt onterecht als ongeldig gemarkeerd")

    db.close()


setup_database("NL")


# TODO add country and language selection
@rt("/")
def get(number: str = "", country: str = ""):
    country_select_list = [Option(item, value=item, selected=False) for item in iso_list.ISO_3166]
    country_select_list.insert(0, Option("", value="", selected=not country))
    for item in country_select_list:
        if item.value == country:
            item.selected = True

    return Title("Every Phone Number"), Container(
        Div(
            H1("Every Phone Number"),
            Form(
                Label("Search Phone Number:", _for="number"),
                Fieldset(
                    Input(type="tel", value=number, name="number", id="number", placeholder="Search phone number in E164 format...", autocomplete="false"),
                    Select(
                        *country_select_list,
                        name="country",
                        id="country",
                        autocomplete="false",
                    ),
                    Input(
                        type="submit",
                        value="Search",
                        hx_get="/",
                        hx_include="[name='number'], [name='country']",
                        hx_target="body",
                        hx_swap="innerHTML",
                        hx_push_url="true",
                    ),
                    role="group",
                ),
                action="/",
                method="get",
                style="margin-bottom: 1rem;",
            ),
            get_phone_number_details(number, country=country) if number else P("Enter a phone number to see details."),
            id="main",
        ),
    )


def get_phone_number_details(number: str, country: str):
    try:
        # TODO see
        # https://github.com/google/libphonenumber/blob/1febc82e196b089be64de8cbde6075ebc7cedceb/java/demo/src/main/java/com/google/phonenumbers/demo/ResultServlet.java
        # search country 2 chars for the phone number

        numobj = phonenumbers.parse(number, region=country)

        country_code = phonenumbers.region_code_for_number(numobj)
        numobj = phonenumbers.parse(number=number, region=country_code, keep_raw_input=True)

        # Get metadata
        is_valid_number = phonenumbers.is_valid_number(numobj)

        # Format number in different formats
        format_e164 = phonenumbers.format_number(numobj, phonenumbers.PhoneNumberFormat.E164)
        format_international = phonenumbers.format_number(numobj, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        format_national = phonenumbers.format_number(numobj, phonenumbers.PhoneNumberFormat.NATIONAL)
        format_rfc3966 = phonenumbers.format_number(numobj, phonenumbers.PhoneNumberFormat.RFC3966)

        # Get additional metadata
        region = phonenumbers.region_code_for_number(numobj)
        is_possible_number = phonenumbers.is_possible_number(numobj)
        is_possible_number_with_reason = phonenumbers.ValidationResult.to_string(phonenumbers.is_possible_number_with_reason(numobj))
        get_number_type = phonenumbers.PhoneNumberType.to_string(phonenumbers.number_type(numobj))

        country_code_source = phonenumbers.CountryCodeSource.to_string(numobj.country_code_source)

        # as you type formatter
        as_you_type_formatter = phonenumbers.AsYouTypeFormatter(country_code)

        # Data for the tables
        parsing_data = {
            "Country Code": numobj.country_code,
            "National Number": numobj.national_number,
            "Extension": numobj.extension,
            "Country Code Source": country_code_source,
            "Italian Leading Zero": "true " if numobj.italian_leading_zero else "false",
            "Number of Leading Zeros": numobj.number_of_leading_zeros or "1",
            "Raw Input": str(numobj.raw_input),
            "Preferred Domestic Carrier Code": numobj.preferred_domestic_carrier_code,
        }
        validation_data = {
            "Result from isPossibleNumber()": "true" if is_possible_number else "false",
            "Result from isPossibleNumberWithReason()": str(is_possible_number_with_reason),
            "Result from isValidNumber()": "true" if is_valid_number else "false",
            "Phone Number region": region,
            "Result from getNumberType()": get_number_type,
        }

        # Insert "Result from isValidNumberForRegion()" just below "Result from isValidNumber()"
        if country:
            # Create a new ordered dict to preserve order
            new_validation_data = OrderedDict()
            for k, v in validation_data.items():
                new_validation_data[k] = v
                if k == "Result from isValidNumber()":
                    new_validation_data["Result from isValidNumberForRegion()"] = "true" if phonenumbers.is_valid_number_for_region(numobj, country) else "false"
            validation_data = new_validation_data

        formatting_data = {
            "E164 format": format_e164,
            "Original format": format_e164,
            "National format": format_national,
            "International format": format_international,
            "RFC3966 format": format_rfc3966,
            "Out-of-country format from US": phonenumbers.format_out_of_country_calling_number(numobj, region_calling_from="US"),
            "Out-of-country format from CH": phonenumbers.format_out_of_country_calling_number(numobj, region_calling_from="CH"),
            "Format for mobile dialing (calling from US)": phonenumbers.format_number_for_mobile_dialing(numobj, "US", with_formatting=True),
            "Format for national dialing with preferred carrier code and empty fallback carrier code": phonenumbers.format_national_number_with_carrier_code(numobj, ""),
        }

        geocoder_result = phonenumbers.geocoder.description_for_number(numobj, "en") or "Unknown"
        timezone_result = ", ".join(phonenumbers.timezone.time_zones_for_number(numobj)) or "Unknown"
        carrier_result = phonenumbers.carrier.name_for_number(numobj, "en") or "Unknown"

        # Helper function to create table rows
        td_width = "50%"

        def create_rows(data):
            return [Tr(Td(key, width=td_width), Td(value)) for key, value in data.items()]

        # Generate AsYouTypeFormatter results
        as_you_type_results = [
            Tr(Td(1 + i, width="1%"), Td(f"Char entered: '{char}' Output: ", width=td_width), Td(as_you_type_formatter.input_digit(char))) for i, char in enumerate(number)
        ]

        libphonenumber_link = Small(A("LibPhoneNumber", href="https://libphonenumber.appspot.com/phonenumberparser?number=" + urllib.parse.quote(number), target="_blank"))

        return Card(
            H3(f"Parsing Result (parseAndKeepRawInput()) ", libphonenumber_link),
            Table(*create_rows(parsing_data)),
            H3("Validation Results"),
            Table(*create_rows(validation_data)),
            H3("Formatting Results"),
            Table(*create_rows(formatting_data)),
            H3("AsYouTypeFormatter Results"),
            Table(*as_you_type_results),
            H3("PhoneNumberOfflineGeocoder Results"),
            Table(Tr(Td("Location", width=td_width), Td(geocoder_result))),
            H3("PhoneNumberToTimeZonesMapper Results"),
            Table(Tr(Td("Time zone(s)", width=td_width), Td(timezone_result))),
            H3("PhoneNumberToCarrierMapper Results"),
            Table(Tr(Td("Carrier", width=td_width), Td(carrier_result))),
        )
    except phonenumbers.NumberParseException:
        return Card(H3("Invalid Phone Number"), P("The provided number could not be parsed."))


serve()
