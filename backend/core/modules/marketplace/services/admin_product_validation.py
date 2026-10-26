"""Validate admin form input before product, inventory or image writes."""
from decimal import Decimal, InvalidOperation

from api.models import Product
from .product_images import validate_product_images
from .inventory import validate_stock_quantity


class ProductInputError(ValueError):
    def __init__(self, message, field):
        super().__init__(message)
        self.field = field


def validate_admin_product_input(data):
    if not isinstance(data, dict):
        raise ProductInputError("Send a product object.", "name")
    for field in ("name", "category", "description"):
        value = data.get(field, "")
        if not isinstance(value, str):
            raise ProductInputError(f"{field.title()} must be text.", field)
        value = value.strip()
        limit = 1000 if field == "description" else Product._meta.get_field(field).max_length
        if len(value) > limit or (field != "description" and not value):
            raise ProductInputError(f"Enter {field} with {'0' if field == 'description' else '1'}–{limit} characters.", field)
        data[field] = value
    for field in ("id", "seller_id"):
        value = data.get(field)
        if value not in (None, "") and (isinstance(value, bool) or not isinstance(value, (str, int)) or (field == "id" and not str(value).isdecimal()) or (field == "seller_id" and str(value).startswith("mobile:") and not str(value)[7:].isdecimal())):
            raise ProductInputError("Select a valid product or seller reference.", field)
    for field in ('program_id', 'department_id', 'major_id'):
        value = data.get(field)
        if value not in (None, '') and (isinstance(value, bool) or not isinstance(value, (str, int)) or not str(value).isdecimal()):
            raise ProductInputError("Select a valid program or major.", field)
    if "customization_enabled" in data and not isinstance(data["customization_enabled"], bool):
        raise ProductInputError("Select whether variants are enabled.", "customization_options")

    def amount(value, field):
        try:
            result = Decimal(str(value))
            if not result.is_finite() or result < 0 or result > Decimal("99999999.99") or result != result.quantize(Decimal(".01")):
                raise ValueError
        except (InvalidOperation, ValueError, TypeError):
            raise ProductInputError("Price must be a non-negative amount with at most two decimal places.", field)

    amount(data.get("price"), "price")
    for field in ("stock", "low_stock_threshold"):
        if data.get(field) is not None:
            try:
                value = validate_stock_quantity(data[field])
            except ValueError as error:
                raise ProductInputError(str(error).replace('Stock Quantity', 'Low Stock Threshold') if field == 'low_stock_threshold' else str(error), field) from error
            if value > 2147483647:
                raise ProductInputError("Quantity exceeds the supported inventory limit.", field)
    if data.get("customization_enabled"):
        groups = data.get("customization_options")
        if not isinstance(groups, list) or not groups:
            raise ProductInputError("Add a variation group and at least one named option, or turn variants off.", "customization_options")
        for group in groups:
            if not isinstance(group, dict) or not isinstance(group.get("name"), str) or not group["name"].strip() or not isinstance(group.get("options"), list) or not group["options"]:
                raise ProductInputError("Each variation group needs a name and options.", "customization_options")
            if not isinstance(group.get('selection', 'single'), str) or group.get('selection', 'single') not in {'single', 'multiple'}:
                raise ProductInputError("Choose single or multiple selection for each variation group.", "customization_options")
            for option in group["options"]:
                if not isinstance(option, dict) or not isinstance(option.get("name"), str) or not option["name"].strip():
                    raise ProductInputError("Each variant needs a name.", "customization_options")
                amount(option.get("extra_price", 0), "customization_options")
                for field in ("stock", "low_stock_threshold"):
                    if field in option and validate_stock_quantity(option[field]) > 2147483647:
                        raise ProductInputError("Variant quantity exceeds the supported inventory limit.", "customization_options")
                if option.get("image"):
                    try:
                        validate_product_images([option["image"]])
                    except ValueError as error:
                        raise ProductInputError(str(error), "customization_options") from error
    try:
        if data.get("images") is not None:
            data["images"] = validate_product_images(data["images"])
        if data.get("image_url"):
            data["image_url"] = validate_product_images([data["image_url"]])[0]
    except ValueError as error:
        raise ProductInputError(str(error), "images") from error
    return data
