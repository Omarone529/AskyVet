"""Helpers shared by more than one app."""

from django.utils.text import slugify

FALSE_STRINGS = {"false", "0", "no", "off", ""}


def parse_bool(value, default=True):
    """
    Read a boolean out of a request payload.

    JSON gives a real bool, but multipart and form-encoded requests give the
    string "false" — and ``bool("false")`` is True, which silently turned every
    "unpublish" or "reopen" call into its opposite.
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() not in FALSE_STRINGS
    return bool(value)


def unique_slugify(instance, value, slug_field="slug", max_length=None):
    """
    Build a slug from ``value`` that no other row of the model already uses.

    ``Article`` and ``Thread`` both declare a unique slug generated from a
    user-supplied title. Two items sharing a title would otherwise collide and
    raise IntegrityError, so a numeric suffix is appended until the slug is
    free: "cura-del-gatto", "cura-del-gatto-2", "cura-del-gatto-3", ...

    The instance's own row is excluded from the check, which makes the function
    safe to call on updates as well as on creation.
    """
    model = instance.__class__
    field = model._meta.get_field(slug_field)
    max_length = max_length or field.max_length or 50

    base = slugify(value)[:max_length] or "item"
    slug = base
    suffix = 2

    queryset = model._default_manager.all()
    if instance.pk is not None:
        queryset = queryset.exclude(pk=instance.pk)

    while queryset.filter(**{slug_field: slug}).exists():
        tail = f"-{suffix}"
        slug = f"{base[: max_length - len(tail)]}{tail}"
        suffix += 1

    return slug
