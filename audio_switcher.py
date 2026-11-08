"""Compatibility entry point for the desktop application."""
from application import ApplicationController


def main():
    ApplicationController().run()


if __name__ == "__main__":
    main()
