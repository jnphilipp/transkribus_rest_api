# Copyright (C) 2023-2024 J. Nathanael Philipp (jnphilipp) <nathanael@philipp.land>
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
"""Transkribus REST API Client types."""

import hashlib

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class UploadPage:
    """Dataclass to upload a page."""

    image: Path
    page_xml: Path | None
    page_nr: int
    image_md5: str | None
    page_xml_md5: str | None

    def __init__(
        self,
        image: Path,
        page_xml: Path | None,
        page_nr: int,
        image_md5: str | None = None,
        page_xml_md5: str | None = None,
    ) -> None:
        """Init."""
        object.__setattr__(self, "image", image)
        object.__setattr__(self, "page_xml", page_xml)
        object.__setattr__(self, "page_nr", page_nr)
        object.__setattr__(
            self,
            "image_md5",
            (
                hashlib.md5(open(self.image, "rb").read()).hexdigest()
                if image_md5 is None
                else image_md5
            ),
        )
        object.__setattr__(
            self,
            "page_xml_md5",
            (
                (
                    hashlib.md5(open(self.page_xml, "rb").read()).hexdigest()
                    if self.page_xml is not None
                    else None
                )
                if page_xml_md5 is None
                else page_xml_md5
            ),
        )
