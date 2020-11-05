from argparse import ArgumentParser


SERVER_PARSER = ArgumentParser(add_help=False)
SERVER_PARSER.add_argument(
    "--server",
    help="""Hostname of the openqa instance to be used.
Defaults to openqa.opensuse.org""",
    nargs=1,
    default=["openqa.opensuse.org"],
    type=str,
)
SERVER_PARSER.add_argument(
    "--server-scheme",
    help="URL scheme used by the openqa server. Defaults to 'https'.",
    nargs=1,
    choices=("https", "http"),
    default=["https"],
)
