from fasthtml.common import *
from web.pages.main.utils import details_page, CountryOptionList, noinput_card

rt = APIRouter()


# TODO add country and language selection
@rt("/")
def get(req: Request, number: str = "", country: str = "", pagetype: str = "details"):
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
        (details_page(req, number, country=country, pagetype=pagetype) if number else noinput_card()),
        id="main-content",
    )


serve()
