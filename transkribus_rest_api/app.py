# Copyright (C) 2024-2026 J. Nathanael Philipp (jnphilipp) <nathanael@philipp.land>
#
# Transkribus REST API Client
#
# This file is part of transkribus-rest-api.
#
# transkribus-rest-api is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# transkribus-rest-api is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Foobar. If not, see <http://www.gnu.org/licenses/>
"""Transkribus Metagrapho API Client cmd interface."""

import logging
import sys

from argparse import (
    ArgumentDefaultsHelpFormatter,
    ArgumentParser,
    RawTextHelpFormatter,
)
from pathlib import Path
from typing import List

from . import VERSION
from .api import transkribus_rest_api
from .types import UploadPage


class ArgFormatter(ArgumentDefaultsHelpFormatter, RawTextHelpFormatter):
    """Combination of ArgumentDefaultsHelpFormatter and RawTextHelpFormatter."""

    pass


def filter_info(rec: logging.LogRecord) -> bool:
    """Log record filter for info and lower levels.

    Args:
     * rec: LogRecord object
    """
    return rec.levelno <= logging.INFO


def main():
    """Run the command line interface."""
    parser = ArgumentParser(
        prog="transkribus_metagrapho_api", formatter_class=ArgFormatter
    )
    parser.add_argument("-V", "--version", action="version", version=VERSION)
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="verbosity level; multiple times increases the level, the maximum is 3, "
        + "for debugging.",
    )
    parser.add_argument(
        "--log-format",
        default="%(message)s",
        help="set logging format.",
    )
    parser.add_argument(
        "--log-file",
        type=lambda p: Path(p).absolute(),
        help="log output to a file.",
    )

    parser.add_argument("-u", "--username", required=True, help="transkribus username.")
    parser.add_argument("-p", "--password", required=True, help="transkribus password.")

    subparsers = parser.add_subparsers(dest="subcommand")

    upload_parser = subparsers.add_parser(
        "upload-document", help="upload a document to a collection."
    )
    upload_parser.add_argument(
        "-c",
        "--collection-id",
        type=int,
        required=True,
        help="collection ID to upload to.",
    )
    upload_parser.add_argument("-t", "--title", required=True, help="document title.")
    upload_parser.add_argument(
        "FILES",
        nargs="+",
        type=lambda p: Path(p).absolute(),
        help="either a list of files or a folder, both with images and PAGE-XML files "
        + "to upload.",
    )

    args = parser.parse_args()

    if args.verbose == 0:
        level = logging.WARNING
    elif args.verbose == 1:
        level = logging.INFO
    else:
        level = logging.DEBUG

    handlers: List[logging.Handler] = []
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(level)
    stdout_handler.addFilter(filter_info)
    handlers.append(stdout_handler)

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    if "%(levelname)s" not in args.log_format:
        stderr_handler.setFormatter(
            logging.Formatter(f"[%(levelname)s] {args.log_format}")
        )
    handlers.append(stderr_handler)

    if args.log_file:
        file_handler = logging.FileHandler(args.log_file)
        file_handler.setLevel(level)
        if args.log_file_format:
            file_handler.setFormatter(logging.Formatter(args.log_file_format))
        handlers.append(file_handler)

    logging.basicConfig(
        format=args.log_format,
        level=logging.DEBUG,
        handlers=handlers,
    )

    with transkribus_rest_api(args.username, args.password) as api:
        if args.subcommand == "upload-document":
            files: dict[str, list[Path | None]] = {}
            for path in args.FILES:
                if path.is_file():
                    if path.stem not in files:
                        files[path.stem] = [None, None]
                    if path.suffix == ".xml":
                        files[path.stem][1] = path
                    elif path.suffix in [".jpg", ".jpeg", ".tif", ".tiff", ".png"]:
                        files[path.stem][0] = path
                elif path.is_dir():
                    for p in path.iterdir():
                        if p.stem not in files:
                            files[p.stem] = [None, None]
                        if path.suffix == ".xml":
                            files[p.stem][1] = p
                        if p.suffix in [".jpg", ".jpeg", ".tif", ".tiff", ".png"]:
                            files[p.stem][0] = p
            pages = []
            for i, (k, v) in enumerate(sorted(files.items(), key=lambda x: x[0])):
                if v[0] is not None:
                    pages.append(UploadPage(image=v[0], page_xml=v[1], page_nr=i))
            doc_id = api.upload_document(
                args.collection_id,
                args.title,
                pages,
            )
            print(f"Document uploaded successfully with ID {doc_id}.")
