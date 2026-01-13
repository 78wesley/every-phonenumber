from fasthtml.common import *
from web.pages import register_routes

# TODO take a look at this chatgpt chat: https://chatgpt.com/c/684c6e2a-85c4-8008-8d19-73d53d89b78c

ENV_DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

app = FastHTML(
    debug=ENV_DEBUG,
    hdrs=picolink,
    title="LibPhoneX - Every Phone Number",
    description="Lookup and validate phone numbers from around the world using LibPhoneNumber.",
    author="78wesley",
)


app.devtools_json()


register_routes(app, debug=ENV_DEBUG)
