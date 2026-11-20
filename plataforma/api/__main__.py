"""Sobe a API: python -m plataforma.api --host 0.0.0.0 --porta 5000"""

from __future__ import annotations

import argparse

from plataforma.api.app import app_do_ambiente


def main() -> None:
    parser = argparse.ArgumentParser(description="API da plataforma de monitoramento")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--porta", type=int, default=5000)
    args = parser.parse_args()
    app_do_ambiente().run(host=args.host, port=args.porta)


if __name__ == "__main__":
    main()
