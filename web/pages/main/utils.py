from fasthtml.common import *
import lib.iso_list as iso_list


def CountryOptionList(country: str) -> list[Option]:
    country_select_list: list[Option] = [Option(item, value=item, selected=(item == country)) for item in iso_list.ISO_3166]
    country_select_list.insert(0, Option("", value="", selected=(country == "")))
    return country_select_list


from fasthtml.common import *
from collections import OrderedDict
import phonenumbers as pn
import phonenumbers.carrier as pn_carrier
import phonenumbers.geocoder as pn_geocoder
import phonenumbers.timezone as pn_timezone
from urllib import parse as urllib_parse


def recommandation_message(number: str, country: str):
    if number:
        num = f"+{number}"
        return H6(
            "Do you mean: ",
            I(
                A(
                    num,
                    href=f"?number={urllib_parse.quote(num)}&country={urllib_parse.quote(country)}",
                    target="_self",
                )
            ),
            " ?",
            style="display:inline",
        )


def invalid_number_card(number: str = "", country: str = ""):
    num = "".join(n for n in number if n.isdigit())
    return Card(
        H5("Invalid Phone Number"),
        P(f"The provided number '{number}' could not be parsed."),
        recommandation_message(num, country),
    )


def noinput_card():
    return Card(H5("Enter a phone number to see details."))


def libphonenumber_link(number_e164: str, country: str = ""):
    return Small(
        A(
            "LibPhoneNumber",
            href="https://libphonenumber.appspot.com/phonenumberparser?number=" + urllib_parse.quote(number_e164) + (f"&country={urllib_parse.quote(country)}" if country else ""),
            target="_blank",
        )
    )


def details_page(req: Request, number: str, country: str, pagetype: str = "details"):
    try:
        # TODO see
        # https://github.com/google/libphonenumber/blob/1febc82e196b089be64de8cbde6075ebc7cedceb/java/demo/src/main/java/com/google/pn/demo/ResultServlet.java
        # search country 2 chars for the phone number

        numobj = pn.parse(number, region=country)

        country_code = pn.region_code_for_number(numobj)
        numobj = pn.parse(number=number, region=country_code, keep_raw_input=True)

        # Get metadata
        is_valid_number = pn.is_valid_number(numobj)

        # Format number in different formats
        format_e164 = pn.format_number(numobj, pn.PhoneNumberFormat.E164)
        format_international = pn.format_number(numobj, pn.PhoneNumberFormat.INTERNATIONAL)
        format_national = pn.format_number(numobj, pn.PhoneNumberFormat.NATIONAL)
        format_rfc3966 = pn.format_number(numobj, pn.PhoneNumberFormat.RFC3966)

        # Get additional metadata
        region = pn.region_code_for_number(numobj)
        is_possible_number = pn.is_possible_number(numobj)
        is_possible_number_with_reason = pn.ValidationResult.to_string(pn.is_possible_number_with_reason(numobj))
        get_number_type = pn.PhoneNumberType.to_string(pn.number_type(numobj))

        country_code_source = pn.CountryCodeSource.to_string(numobj.country_code_source)

        # as you type formatter
        as_you_type_formatter = pn.AsYouTypeFormatter(country_code)

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
                    new_validation_data["Result from isValidNumberForRegion()"] = "true" if pn.is_valid_number_for_region(numobj, country) else "false"
            validation_data = new_validation_data

        formatting_data = {
            "E164 format": format_e164,
            "Original format": format_e164,
            "National format": format_national,
            "International format": format_international,
            "RFC3966 format": format_rfc3966,
            "Out-of-country format from US": pn.format_out_of_country_calling_number(numobj, region_calling_from="US"),
            "Out-of-country format from CH": pn.format_out_of_country_calling_number(numobj, region_calling_from="CH"),
            "Format for mobile dialing (calling from US)": pn.format_number_for_mobile_dialing(numobj, "US", with_formatting=True),
            "Format for national dialing with preferred carrier code and empty fallback carrier code": pn.format_national_number_with_carrier_code(numobj, ""),
        }

        geocoder_result = pn_geocoder.description_for_number(numobj, "en") or "Unknown"
        timezone_result = ", ".join(pn_timezone.time_zones_for_number(numobj)) or "Unknown"
        carrier_result = pn_carrier.name_for_number(numobj, "en") or "Unknown"

        # Helper function to create table rows
        td_width = "50%"

        def create_rows(data):
            return [Tr(Td(key, width=td_width), Td(value)) for key, value in data.items()]

        # Generate AsYouTypeFormatter results
        as_you_type_results = [
            Tr(
                Td(1 + i, width="1%"),
                Td(f"Char entered: '{char}' Output: ", width=td_width),
                Td(as_you_type_formatter.input_digit(char)),
            )
            for i, char in enumerate(number)
        ]

        return Div(
            # Group(
            #     Button(
            #         "Details",
            #         hx_get=f"?number={urllib_parse.quote(number)}&country={urllib_parse.quote(country)}?pagetype=details",
            #         hx_target="#main-content",
            #         hx_swap="outerHTML",
            #     ),
            #     Button(
            #         "LibPhoneNumber",
            #         hx_get=f"?number={urllib_parse.quote(number)}&country={urllib_parse.quote(country)}?pagetype=libphonenumber",
            #         hx_target="#main-content",
            #         hx_swap="outerHTML",
            #     ),
            # ),
            (
                Card(
                    (recommandation_message(number, country) if not numobj.country_code_source == pn.CountryCodeSource.FROM_NUMBER_WITH_PLUS_SIGN else ""),
                    H5(
                        f"Parsing Result (parseAndKeepRawInput()) ",
                        libphonenumber_link(format_e164, country),
                    ),
                    Table(*create_rows(parsing_data)),
                    H5("Validation Results"),
                    Table(*create_rows(validation_data)),
                    H5("Formatting Results"),
                    Table(*create_rows(formatting_data)),
                    H5("AsYouTypeFormatter Results"),
                    Table(*as_you_type_results),
                    H5("PhoneNumberOfflineGeocoder Results"),
                    Table(Tr(Td("Location", width=td_width), Td(geocoder_result))),
                    H5("PhoneNumberToTimeZonesMapper Results"),
                    Table(Tr(Td("Time zone(s)", width=td_width), Td(timezone_result))),
                    H5("PhoneNumberToCarrierMapper Results"),
                    Table(Tr(Td("Carrier", width=td_width), Td(carrier_result))),
                )
                if pagetype == "details"
                else Card(
                    H5("LibPhoneNumber Result"),
                    P("Below are the details as provided by the LibPhoneNumber library:"),
                    Table(*create_rows(parsing_data)),
                    Table(*create_rows(validation_data)),
                    Table(*create_rows(formatting_data)),
                    H5("AsYouTypeFormatter Results"),
                    Table(*as_you_type_results),
                    H5("PhoneNumberOfflineGeocoder Results"),
                    Table(Tr(Td("Location", width=td_width), Td(geocoder_result))),
                    H5("PhoneNumberToTimeZonesMapper Results"),
                    Table(Tr(Td("Time zone(s)", width=td_width), Td(timezone_result))),
                    H5("PhoneNumberToCarrierMapper Results"),
                    Table(Tr(Td("Carrier", width=td_width), Td(carrier_result))),
                )
            ),
            id="details-content",
        )
    except pn.NumberParseException:
        return invalid_number_card(number, country)
