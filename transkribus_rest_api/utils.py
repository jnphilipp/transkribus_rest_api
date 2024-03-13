# Copyright (C) 2024 J. Nathanael Philipp (jnphilipp) <nathanael@philipp.land>
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
"""Transkribus REST API Client utils."""

from lxml import etree


def parse_xml(text: bytes) -> etree._Element:
    """Parse string to XML."""
    parser = etree.XMLParser(ns_clean=True, remove_blank_text=True)
    return etree.fromstring(text, parser=parser)
