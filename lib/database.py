from fasthtml.common import *
import peewee as pw
import os


# SQLite database
# Ensure the 'databases' directory exists
if not os.path.exists("databases"):
    os.makedirs("databases")

db = pw.SqliteDatabase("databases/libphonex.db")


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


# Setup
def setup_database(country_code):
    db.connect()
    PhoneNumber = create_phone_number_model(country_code)
    db.create_tables([PhoneNumber, ValidationRule, Issue], safe=True)

    if (
        not ValidationRule.select()
        .where(
            (ValidationRule.country_code == country_code)
            & (ValidationRule.type == "mobile")
            & (ValidationRule.regex == "^6\\d{8}$")
        )
        .exists()
    ):
        ValidationRule.create(
            country_code=country_code,
            type="mobile",
            regex="^6\\d{8}$",
            example="612345678",
            description="Standaard mobiel nummer in Nederland",
        )

    if (
        not PhoneNumber.select()
        .where(
            (PhoneNumber.country_code == country_code)
            & (PhoneNumber.national_number == "612345678")
        )
        .exists()
    ):
        PhoneNumber.create(
            country_code=country_code,
            international_prefix="+31",
            national_number="612345678",
            type="mobile",
            is_valid=True,
            notes="Typisch geldig mobiel nummer",
        )

    if not Issue.select().where(Issue.phone_number == "+31600000000").exists():
        Issue.create(
            phone_number="+31600000000",
            reason="Nummer wordt onterecht als ongeldig gemarkeerd",
        )

    db.close()


setup_database("NL")


db = pw.SqliteDatabase("databases/libphonex.db")


# Models
class BaseModel(pw.Model):
    class Meta:
        database = db


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

