from fasthtml.common import *
import lib.iso_list as iso_list
from partials.details import details_page, noinput_card
from dotenv import load_dotenv
import os

load_dotenv()


# TODO take a look at this chatgpt chat: https://chatgpt.com/c/684c6e2a-85c4-8008-8d19-73d53d89b78c

hdrs = (Link(rel="stylesheet", href=picocss), Style(":root { --pico-font-size: 90%; }"))

print(os.getenv("DEBUG", "False").lower() in ("true", "1", "t"))
app = FastHTML(
    debug=os.getenv("DEBUG", "False").lower() in ("true", "1", "t"),
    hdrs=hdrs,
    title="LibPhoneX - Every Phone Number",
    description="Lookup and validate phone numbers from around the world using LibPhoneNumber.",
    author="78wesley",
)


def CountryOptionList(country: str) -> list[Option]:
    country_select_list: list[Option] = [
        Option(item, value=item, selected=(item == country))
        for item in iso_list.ISO_3166
    ]
    country_select_list.insert(0, Option("", value="", selected=(country == "")))
    return country_select_list


# TODO add country and language selection
@app.route("/")
def get(req: Request, number: str = "", country: str = ""):
    return Container(
        Form(
            Label("Search Phone Number:", _for="number"),
            Fieldset(
                Input(
                    type="tel",
                    value=number,
                    name="number",
                    id="number",
                    placeholder="Search...",
                    autocomplete="false",
                ),
                Select(
                    *CountryOptionList(country),
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
        (details_page(req, number, country=country) if number else noinput_card()),
        id="main",
    )


serve()
