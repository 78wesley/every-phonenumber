from fasthtml.common import *
import phonenumbers
from phonenumbers import geocoder, carrier, timezone
from fastlite import *
import os

app, rt = fast_app(debug=True)

database_path = "databases"

path_db_country_codes = f"{database_path}/country_codes.db"

db_country_codes = database(path_db_country_codes)
db_country_codes_table = db_country_codes.t.country_codes


@dataclass
class CountryCodes:
    id: int
    iso_numeric: str
    country_name: str
    iso2: str
    iso3: str
    top_level_domain: str
    fips: str
    e164: str
    continent: str
    capital: str
    time_zone_in_capital: str


if "country_codes" not in db_country_codes_table:
    create_table_db_country_codes = db_country_codes.create(CountryCodes, pk="id")

print(db_country_codes_table[0])

# TODO take a look at this chatgpt chat: https://chatgpt.com/c/684c6e2a-85c4-8008-8d19-73d53d89b78c

# if db_country_codes_table.lookup({"iso_numeric": "528"}) is None:
#     create_table_db_country_codes.insert(
#         CountryCodes(
#             iso_numeric="528",
#             country_name="Netherlands",
#             iso2="NL",
#             iso3="NLD",
#             top_level_domain=".nl",
#             fips="NL",
#             e164="+31",
#             continent="Europe",
#             capital="Amsterdam",
#             time_zone_in_capital="Europe/Amsterdam",
#         )
#     )


# Main route with search bar and infinite scroll
@rt("/")
def get():
    return Title("Every Phone Number (Global)"), Container(
        Div(
            H1("Every Phone Number"),
            # 🔍 Search form
            Form(
                Input(id="search", name="number", placeholder="Search any phone number...", type="tel"),
                Button("Search"),
                action="/search",
                method="get",
                style="margin-bottom: 1rem;",
            ),
            Ul(id="phone-list"),
            Div("Loading...", id="loading"),
            id="main",
        ),
        Script(
            """
        let index = 1000000000000n;
        const batchSize = 100n;
        let loading = false;

        async function loadMore() {
            if (loading) return;
            loading = true;
            const response = await fetch(`/batch/${index}`);
            const html = await response.text();
            document.getElementById("phone-list").insertAdjacentHTML("beforeend", html);
            index += batchSize;
            loading = false;
        }

        window.addEventListener('scroll', () => {
            if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 100) {
                loadMore();
            }
        });

        loadMore();
        """
        ),
    )


# 🔎 Search handler redirects to detail page
@rt("/search")
def get(number: str = ""):
    number = number.strip().lstrip("+")
    if not number.isdigit():
        return RedirectResponse("/", status_code=303)
    return RedirectResponse(f"/phone/{number}", status_code=303)


# Load a batch of numbers
@rt("/batch/{start:str}")
def get(start: str):
    try:
        start_n = int(start)
    except ValueError:
        return Response("Invalid start", status_code=400)

    items = []
    for i in range(start_n, start_n + 100):
        num = f"+{i}"
        items.append(f"<li><a href='/phone/{i}' hx-get='/phone/{i}' hx-target='#phone-detail'>{num}</a></li>")

    return "\n".join(items)


# Detail view for a phone number
@rt("/phone/{n:str}")
def get(n: str):

    try:
        # Parse number with country code
        pn = phonenumbers.parse("+" + n)

        # Get metadata
        country = geocoder.description_for_number(pn, "en")
        carrier_name = carrier.name_for_number(pn, "en")
        time_zones = timezone.time_zones_for_number(pn)
        is_valid = phonenumbers.is_valid_number(pn)
        number_type = phonenumbers.number_type(pn)
        type_names = {
            phonenumbers.PhoneNumberType.FIXED_LINE: "Fixed Line",
            phonenumbers.PhoneNumberType.MOBILE: "Mobile",
            phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "Fixed Line or Mobile",
            phonenumbers.PhoneNumberType.TOLL_FREE: "Toll Free",
            phonenumbers.PhoneNumberType.PREMIUM_RATE: "Premium Rate",
            phonenumbers.PhoneNumberType.SHARED_COST: "Shared Cost",
            phonenumbers.PhoneNumberType.VOIP: "VoIP",
            phonenumbers.PhoneNumberType.PERSONAL_NUMBER: "Personal Number",
            phonenumbers.PhoneNumberType.PAGER: "Pager",
            phonenumbers.PhoneNumberType.UAN: "UAN",
            phonenumbers.PhoneNumberType.UNKNOWN: "Unknown",
        }

        # Format number in different formats
        e164 = phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.E164)
        international = phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        national = phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.NATIONAL)
        rfc3966 = phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.RFC3966)

        # Get additional metadata
        region = phonenumbers.region_code_for_number(pn)
        possible = phonenumbers.is_possible_number(pn)
        possible_reason = phonenumbers.is_possible_number_with_reason(pn)

        return Card(
            A("Back to list", href="/"),
            H3(f"Phone Number: +{n}"),
            Table(
                Tr(Td("E164 Format:"), Td(e164)),
                Tr(Td("International Format:"), Td(international)),
                Tr(Td("National Format:"), Td(national)),
                Tr(Td("RFC3966 Format:"), Td(rfc3966)),
                Tr(Td("Country:"), Td(country or "Unknown")),
                Tr(Td("Region Code:"), Td(region or "Unknown")),
                Tr(Td("Carrier:"), Td(carrier_name or "Unknown")),
                Tr(Td("Timezone(s):"), Td(", ".join(time_zones) or "Unknown")),
                Tr(Td("Valid Number:"), Td("Yes" if is_valid else "No")),
                Tr(Td("Possible Number:"), Td("Yes" if possible else "No")),
                Tr(Td("Possibility Reason:"), Td(str(possible_reason))),
                Tr(Td("Number Type:"), Td(type_names.get(number_type, "Unknown"))),
            ),
        )
    except phonenumbers.NumberParseException:
        return Card(H3("Invalid Phone Number"), A("Back to list", href="/"), P("The provided number could not be parsed."))


serve()
