"""Deteccion controlada de CAPTCHA compartida por navegador y portal."""


class CaptchaRequiredError(RuntimeError):
    """Indica que TICA exige intervencion por CAPTCHA."""


def contiene_captcha(text: str) -> bool:
    """Reconoce las pistas de CAPTCHA confirmadas durante la PoC."""

    normalized = text.lower()
    clues = ("captcha", "no soy un robot", "recaptcha", "verificacion")
    return any(clue in normalized for clue in clues)

