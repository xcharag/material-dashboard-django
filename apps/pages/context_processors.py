from .models import Professional

_PSYCHOLOGIST_ROLES = ('psychologist', 'psychiatrist')


def role_flags(request):
    if not request.user.is_authenticated:
        return {'is_secretary': False, 'is_psychologist': False}
    # Reuse the per-request cached lookup (avoids a duplicate remote-DB query)
    from .views import _get_professional
    prof = _get_professional(request.user)
    if prof is None:
        return {'is_secretary': False, 'is_psychologist': False}
    return {
        'is_secretary': prof.role == 'secretary',
        'is_psychologist': prof.role in _PSYCHOLOGIST_ROLES,
    }
