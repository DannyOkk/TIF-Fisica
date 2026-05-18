#!/usr/bin/env python3
"""Punto de entrada principal del simulador."""

from src.controller.menu import Menu


def main() -> None:
    """Ejecuta el programa."""
    menu = Menu()
    menu.ejecutar()


if __name__ == '__main__':
    main()
