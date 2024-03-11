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

import logging
import requests

from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Final, Generator, Type, TypeVar

from .types import UploadPage
from .utils import parse_xml


class TranskribusRestApi:
    """Transkribus REST API.

    https://readcoop.eu/transkribus/docu/rest-api/
    """

    T = TypeVar("T", bound="TranskribusRestApi")

    BASE_URL: Final[str] = "https://transkribus.eu/TrpServer/rest"
    session_id: "TranskribusRestApi.SessionId"

    class SessionId:
        """Session ID."""

        T = TypeVar("T", bound="TranskribusRestApi.SessionId")

        session_id: str
        expires: datetime

        def __init__(
            self,
            session_id: str,
            expires: datetime,
        ) -> None:
            """Create new session ID."""
            self.session_id = session_id
            self.expires = expires

        def get_auth_header(self) -> Dict[str, str]:
            """Get auth token for Authentication header.

            Auto refreshes if token is expired.
            """
            self.refresh()
            return {"Cookie": f"JSESSIONID={self.session_id}"}

        def is_expired(self) -> bool:
            """Check if the access token is expired."""
            return datetime.now() > self.expires

        def refresh(self, force: bool = False) -> bool:
            """Refresh access token."""
            if force or self.is_expired():
                logging.debug("Refresh access token.")
                r = requests.post(
                    f"{TranskribusRestApi.BASE_URL}/auth/refresh",
                    headers=self.get_auth_header(),
                )
                r.raise_for_status()

                doc = parse_xml(r.text)
                now = datetime.now()
                self.session_id = doc.xpath("//sessionId/text()")[0]
                self.expires = now + timedelta(hours=12)
                return True
            return False

        def logout(self) -> bool:
            """Revoke access token."""
            logging.debug("Revoke access token.")
            r = requests.post(
                f"{TranskribusRestApi.BASE_URL}/auth/logout",
                headers=self.get_auth_header(),
            )
            r.raise_for_status()

            self.session_id = ""
            self.expires = datetime.now()
            return True

        @classmethod
        def login(cls: Type[T], username: str, password: str) -> T:
            """Login.

            Args:
             * username: transkribus user name
             * password: transkribus password
            """
            logging.debug("Login.")
            r = requests.post(
                f"{TranskribusRestApi.BASE_URL}/auth/login",
                data={
                    "user": username,
                    "pw": password,
                },
            )
            r.raise_for_status()
            now = datetime.now()
            doc = parse_xml(r.text)
            return cls(
                session_id=doc.xpath("//sessionId/text()")[0],
                expires=now + timedelta(hours=12),
            )

    def __init__(self, username: str, password: str):
        """Init."""
        self.session_id = TranskribusRestApi.SessionId.login(username, password)

    def close(self) -> bool:
        """Close this API.

        Sends a requests to revoke the access token.

        Returns:
         * `True` if request was successful
        """
        return self.session_id.logout()

    def upload_document(
        self,
        collection_id: str,
        title: str,
        pages: List[UploadPage],
        metadata: Dict = {},
    ):
        """Upload a document.

        Args:
         * collection_id: collection to upload document to
         * title: title of the document
         * pages: pages to upload
         * metadata: extra metadata for the document
        """
        data = {
            "md": {
                "title": title,
            }
            | metadata,
            "pageList": {
                "pages": [
                    {
                        "fileName": page.image.name,
                        "pageXmlName": (
                            None if page.page_xml is None else page.page_xml.name
                        ),
                        "pageNr": page.page_nr,
                        "imgChecksum": page.image_md5,
                        "pageXmlChecksum": page.page_xml_md5,
                    }
                    for page in pages
                ],
            },
        }

        r = requests.post(
            f"{self.BASE_URL}/uploads?collId={collection_id}",
            headers=self.session_id.get_auth_header(),
            json=data,
        )

        r.raise_for_status()
        doc = parse_xml(r.text)
        upload_id = doc.xpath("//uploadId/text()")[0]
        for page in pages:
            files = {
                "img": (
                    page.image.name,
                    open(page.image, "rb"),
                    "application/octet-stream",
                )
            }
            if page.page_xml is not None:
                files["xml"] = (
                    page.page_xml.name,
                    open(page.page_xml, "rb"),
                    "application/octet-stream",
                )
            r = requests.put(
                f"{self.BASE_URL}/uploads/{upload_id}",
                headers=self.session_id.get_auth_header(),
                files=files,
            )
            r.raise_for_status()


@contextmanager
def transkribus_rest_api(username: str, password: str) -> Generator:
    """Context manager for Transkribus rest API.

    Args:
     * username: username for API authentication
     * password: password for API authentication

    Returns:
     * an instance of `TranskribusRestApi`
    """
    api = TranskribusRestApi(username, password)
    yield api
    api.close()
