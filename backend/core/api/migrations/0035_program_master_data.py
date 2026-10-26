"""Normalize known program/major assignments without deleting legacy records."""
from django.db import migrations


def normalize_programs(apps, schema_editor):
    db = schema_editor.connection.alias
    Department = apps.get_model("accounts", "Department")
    Major = apps.get_model("accounts", "ProgramMajor")
    User = apps.get_model("accounts", "User")
    Product = apps.get_model("api", "Product")
    programs = {}
    for code, name in (("BSIT", "Bachelor of Information Technology"),
                       ("BFPT", "Bachelor of Food Processing and Technology"),
                       ("BTLED", "Bachelor of Technology and Livelihood Education")):
        program, _ = Department.objects.using(db).get_or_create(code=code, defaults={"name": name})
        Department.objects.using(db).filter(pk=program.pk).update(is_program=True)
        programs[code] = program
    majors = {}
    for code, name in (("IA", "Industrial Arts"), ("HE", "Home Economics"), ("ICT", "Information and Communication Technology")):
        majors[code], _ = Major.objects.using(db).get_or_create(program=programs["BTLED"], code=code, defaults={"name": name})
    mobile_exists = "campushub_user" in schema_editor.connection.introspection.table_names()
    if mobile_exists:
        schema_editor.execute("ALTER TABLE campushub_user ADD COLUMN IF NOT EXISTS major_id bigint NULL")
    for old in Department.objects.using(db).exclude(pk__in=[row.pk for row in programs.values()]):
        token = (old.code or "").upper().replace("_", "-")
        major_code = token.removeprefix("BTLED-")
        if major_code not in majors:
            text = old.name.casefold()
            major_code = next((code for code, major in majors.items() if text == major.name.casefold() or
                              ("major in " + major.name.casefold()) in text), None)
        if major_code not in majors:
            continue  # Unknown departments are preserved, never guessed into a program.
        major = majors[major_code]
        User.objects.using(db).filter(department_id=old.pk).update(department_id=programs["BTLED"].pk, major_id=major.pk)
        Product.objects.using(db).filter(department_id=old.pk).update(department_id=programs["BTLED"].pk, major_id=major.pk)
        if mobile_exists:
            schema_editor.execute("UPDATE campushub_user SET department_id=%s, major_id=%s WHERE department_id=%s",
                                  [programs["BTLED"].pk, major.pk, old.pk])
    # Reliable owner assignments fill legacy listings; unrelated/unknown rows stay explicit.
    for product in Product.objects.using(db).filter(department__isnull=True).select_related("seller__department"):
        owner = product.seller
        if owner.department_id and owner.department.is_program:
            Product.objects.using(db).filter(pk=product.pk).update(department_id=owner.department_id, major_id=owner.major_id)


class Migration(migrations.Migration):
    dependencies = [("api", "0034_program_major_structure")]
    operations = [migrations.RunPython(normalize_programs, migrations.RunPython.noop)]
