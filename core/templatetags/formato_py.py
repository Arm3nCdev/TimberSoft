from decimal import Decimal

from django import template

register = template.Library()


def _miles(valor):
    """1234567 -> '1.234.567' (separador de miles paraguayo)."""
    return f'{int(valor):,}'.replace(',', '.')


@register.filter
def guaranies(valor):
    if valor in (None, ''):
        return '₲ 0'
    return f'₲ {_miles(round(Decimal(valor)))}'


@register.filter
def cantidad(valor):
    """Muestra 12.00 como '12' y 3.50 como '3,5'."""
    valor = Decimal(valor).normalize()
    if valor == valor.to_integral():
        return _miles(valor)
    entero, decimales = f'{valor:f}'.split('.')
    return f'{_miles(entero)},{decimales}'
