def plural_form(value: int, forms: tuple[str, str, str]) -> str:
    value = abs(value) % 100
    if 11 <= value <= 19:
        return forms[2]
    i = value % 10
    if i == 1:
        return forms[0]
    elif 2 <= i <= 4:
        return forms[1]
    else:
        return forms[2]


def humanize_timedelta(delta) -> str:
    """Возвращает человекочитаемую строку вроде '2 дня и 3 часа'."""
    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60

    parts = []
    if days > 0:
        parts.append(f"{days} {plural_form(days, ('день', 'дня', 'дней'))}")
    if hours > 0:
        parts.append(f"{hours} {plural_form(hours, ('час', 'часа', 'часов'))}")
    if minutes > 0:
        parts.append(f"{minutes} {plural_form(minutes, ('минута', 'минуты', 'минут'))}")

    if len(parts) > 1:
        return " и ".join([", ".join(parts[:-1]), parts[-1]]) if len(parts) > 2 else " и ".join(parts)
    return parts[0] if parts else "меньше минуты"
