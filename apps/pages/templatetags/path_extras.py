from django import template

register = template.Library()

@register.filter
def basename(value: str) -> str:
    """Return the base name (file name) from a path-like string."""
    if not value:
        return ""
    # value can be a Storage path like "consultations/1/notas/file.pdf"
    return str(value).split('/')[-1]


@register.filter
def file_ext(value: str) -> str:
    """Return file extension (without dot) in lowercase from a path or filename.
    Examples:
      'foo/bar/file.PDF' -> 'pdf'
      'notes.txt' -> 'txt'
      'noext' -> ''
    """
    if not value:
        return ""
    name = basename(value)
    if '.' not in name:
        return ""
    return name.rsplit('.', 1)[-1].lower()