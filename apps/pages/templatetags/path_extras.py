from django import template

register = template.Library()

@register.filter
def basename(value: str) -> str:
    """Return the base name (file name) from a path-like string."""
    if not value:
        return ""
    # value can be a Storage path like "consultations/1/notas/file.pdf"
    return str(value).split('/')[-1]