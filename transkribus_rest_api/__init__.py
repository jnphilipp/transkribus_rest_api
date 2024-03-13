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
"""Transkribus REST API Client."""

from .api import TranskribusRestApi, transkribus_rest_api

__all__ = ["TranskribusRestApi", "transkribus_rest_api"]

__app_name__ = "transkribus-rest-api"
__author__ = "J. Nathanael Philipp"
__email__ = "nathanael@philipp.land"
__copyright__ = "Copyright 2024 J. Nathanael Philipp (jnphilipp)"
__license__ = "GPLv3"
__version_info__ = (0, 2, 0)
__version__ = ".".join(str(e) for e in __version_info__)
__github__ = "https://github.com/jnphilipp/transkribus-rest-api"
VERSION = (
    f"%(prog)s v{__version__}\n{__copyright__}\n"
    + "License GPLv3+: GNU GPL version 3 or later <https://gnu.org/licenses/gpl.html>."
    + "\nThis is free software: you are free to change and redistribute it.\n"
    + "There is NO WARRANTY, to the extent permitted by law.\n\n"
    + f"Report bugs to {__github__}/issues."
    + f"\nWritten by {__author__} <{__email__}>"
)
