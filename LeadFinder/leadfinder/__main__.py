"""python -m leadfinder        → dashboard in your browser
   python -m leadfinder cli    → same search in this window"""
import sys


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        from .finder import run_cli
        return run_cli(".env")
    from .web import serve
    return serve(".env")


if __name__ == "__main__":
    sys.exit(main())
