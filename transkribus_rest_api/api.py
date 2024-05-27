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
from lxml import etree
from pathlib import Path
from typing import Final, Generator, TypeVar

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

        def get_auth_header(self) -> dict[str, str]:
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

                doc = parse_xml(r.content)
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
        def login(cls: type[T], username: str, password: str) -> T:
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
            doc = parse_xml(r.content)
            return cls(
                session_id=doc.xpath("//sessionId/text()")[0],
                expires=now + timedelta(hours=12),
            )

    class Collections:
        """Group all collections requests together."""

        def __init__(self, api: "TranskribusRestApi"):
            """Create a new collections.

            Args:
             * api: transkribus rest api
            """
            self.api = api

        def get_doc_md_by_id(self, collection_id: int, document_id: int) -> dict:
            """Get the metadata of a document.

            Args:
             * collection_id: collection ID
             * document_id: document ID
            """
            return self.api._get(
                f"collections/{collection_id}/{document_id}/metadata"
            ).json()

        def get_mets(self, collection_id: int, document_id: int) -> etree._Element:
            """Get mets file for a document.

            Args:
             * collection_id: collection ID
             * document_id: document ID
            """
            return parse_xml(
                self.api._get(f"collections/{collection_id}/{document_id}/mets").content
            )

        def get_pages_from_pages_str(
            self,
            collection_id: int,
            document_id: int,
            pages: str | None = None,
            status: str | None = None,
            skip_pages_with_missing_status: bool = False,
        ) -> list:
            """Get pages in a document.

            Args:
             * collection_id: collection ID
             * document_id: document ID
             * query params: pages, status, skip_pages_with_missing_status
            """
            params: dict[str, str | bool] = {
                "skipPagesWithMissingStatus": skip_pages_with_missing_status
            }
            if pages is not None:
                params["pages"] = pages
            if status is not None:
                params["status"] = status
            return self.api._get(
                f"collections/{collection_id}/{document_id}/pages", params=params
            ).json()

        def get_transcript(
            self, collection_id: int, document_id: int, page_id: int
        ) -> etree._Element:
            """Get transcript of a page.

            Args:
             * collection_id: collection ID
             * document_id: document ID
             * page_id: page ID
            """
            return parse_xml(
                self.api._get(
                    f"collections/{collection_id}/{document_id}/{page_id}/text"
                ).content
            )

        def list(
            self,
            index: int = 0,
            n_values: int = 0,
            sort_column: str | None = None,
            sort_direction: str | None = None,
            exclude_empty: bool = False,
            filter: str | None = None,
            role: str | None = None,
            user_id: int | None = None,
        ) -> dict:
            """Get a list of collections.

            Args:
             * index: default 0
             * nValues: default 0
             * sort_column
             * sort_direction
             * exclude_empty: default False
            """
            return self.api._get(
                "collections",
                params={
                    "index": index,
                    "nValues": n_values,
                    "sortColumn": sort_column,
                    "sortDirection": sort_direction,
                    "excludeEmpty": exclude_empty,
                    "filter": filter,
                    "role": role,
                    "userid": user_id,
                },
            ).json()

        def list_docs_by_collection_id(
            self,
            collection_id: int,
            index: int = 0,
            n_values: int = 0,
            sort_column: str | None = None,
            sort_direction: str | None = None,
            is_deleted: bool = False,
        ):
            """Get a list of documents in a collection.

            Args:
             * index: default 0
             * nValues: default 0
             * sort_column
             * sort_direction
             * is_deleted: default False
            """
            return self.api._get(
                f"collections/{collection_id}/list",
                params={
                    "index": index,
                    "nValues": n_values,
                    "sortColumn": sort_column,
                    "sortDirection": sort_direction,
                    "isDeleted": is_deleted,
                },
            ).json()

    class Job:
        """Group all job requests together."""

        def __init__(self, api: "TranskribusRestApi"):
            """Create a new job.

            Args:
             * api: transkribus rest api
            """
            self.api = api

        def get_jobs(
            self,
            user_id: int | None = None,
            filter_by_user: bool | None = None,
            status: str | None = None,
            collection_id: int | None = None,
            job_id: int | None = None,
            type: str | None = None,
            job_impl: str | None = None,
            index: int = 0,
            n_values: int = 50,
            sort_column: str | None = None,
            sort_direction: str | None = None,
        ):
            """List jobs.

            Args:
             * user_id
             * filter_by_user
             * status
             * collection_id
             * job_id
             * type
             * job_impl
             * index: default 0
             * n_values: default 50
             * sort_column
             * sort_direction
            """
            return self.api._get(
                "jobs/list",
                params={
                    "userid": user_id,
                    "filterByUser": filter_by_user,
                    "status": status,
                    "collId": collection_id,
                    "id": job_id,
                    "type": type,
                    "jobImpl": job_impl,
                    "index": index,
                    "nValues": n_values,
                    "sortColumn": sort_column,
                    "sortDirection": sort_direction,
                },
            ).json()

        def get_job_by_id(self, job_id: int | str) -> dict:
            """Get a job by ID.

            Args:
             * job_id: job ID
            """
            return self.api._get(f"jobs/{job_id}").json()

    class Uploads:
        """Group all uploads requests together."""

        def __init__(self, api: "TranskribusRestApi"):
            """Create a new uploads.

            Args:
             * api: transkribus rest api
            """
            self.api = api

        def create_upload_mets(self, collection_id: int, mets: str) -> etree._Element:
            """Create a new upload from a mets file.

            Args:
             * collection_id: collection ID
             * mets: mets XML
            """
            return parse_xml(
                self.api._post(
                    "uploads",
                    params={"collId": collection_id},
                    data={"mets": mets},
                ).content
            )

        def create_upload_doc_structure(
            self, collection_id: int, json: dict
        ) -> etree._Element:
            """Create a new upload from JSON data.

            Args:
             * collection_id: collection ID
             * json: JSON data
            """
            return parse_xml(
                self.api._post(
                    "uploads", params={"collId": collection_id}, json=json
                ).content
            )

        def get_status(self, upload_id: int) -> dict:
            """Get status.

            Args:
             * upload_id
            """
            return self.api._get(f"uploads/{upload_id}").json()

        def upload_page(
            self,
            upload_id: int,
            image: str | Path,
            xml: str | Path | None = None,
        ) -> None:
            """Upload a single page.

            Args:
             * upload_id: upload ID
             * image: path to image
             * xml: optionally path to PAGE-XML
            """
            if isinstance(image, str):
                image = Path(image)

            files = {"img": (image.name, open(image, "rb"), "application/octet-stream")}
            if xml is not None:
                if isinstance(xml, str):
                    xml = Path(xml)
                files["xml"] = (xml.name, open(xml, "rb"), "application/octet-stream")
            self.api._put(f"uploads/{upload_id}", files=files)

    def __init__(self, username: str, password: str):
        """Init."""
        self.collections = TranskribusRestApi.Collections(self)
        self.job = TranskribusRestApi.Job(self)
        self.session_id = TranskribusRestApi.SessionId.login(username, password)
        self.uploads = TranskribusRestApi.Uploads(self)

    def _get(self, path: str, params: dict = {}) -> requests.models.Response:
        r = requests.get(
            f"{self.BASE_URL}/{path}",
            headers=self.session_id.get_auth_header(),
            params=params,
        )
        r.raise_for_status()
        return r

    def _post(
        self,
        path: str,
        params: dict = {},
        data: dict = {},
        json: dict = {},
    ) -> requests.models.Response:
        r = requests.post(
            f"{self.BASE_URL}/{path}",
            headers=self.session_id.get_auth_header(),
            params=params,
            data=data,
            json=json,
        )
        r.raise_for_status()
        return r

    def _put(self, path: str, files: dict[str, tuple]) -> requests.models.Response:
        r = requests.put(
            f"{self.BASE_URL}/{path}",
            headers=self.session_id.get_auth_header(),
            files=files,
        )
        r.raise_for_status()
        return r

    def close(self) -> bool:
        """Close this API.

        Sends a requests to revoke the access token.

        Returns:
         * `True` if request was successful
        """
        return self.session_id.logout()

    def upload_document(
        self,
        collection_id: int,
        title: str,
        pages: list[UploadPage],
        metadata: dict = {},
    ) -> int:
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

        doc = self.uploads.create_upload_doc_structure(collection_id, data)
        upload_id = int(doc.xpath("//uploadId/text()")[0])

        for page in pages:
            self.uploads.upload_page(upload_id, page.image, page.page_xml)
        job_id = self.uploads.get_status(upload_id)["jobId"]
        return self.job.get_job_by_id(job_id)["docId"]

    def download_document(
        self,
        collection_id: int,
        document_id: int,
        target: str | Path,
    ) -> None:
        """Download a whole document as PAGE-XML.

        Args:
         * collection_id: collection ID
         * document_id: document ID
         * target: target folder to save to
        """
        if isinstance(target, str):
            target = Path(target)
        mets = self.collections.get_mets(collection_id, document_id)
        pages = self.collections.get_pages_from_pages_str(collection_id, document_id)
        for i, e in enumerate(
            mets.xpath(
                '//ns3:fileGrp[@ID="PAGEXML"]//ns3:FLocat',
                namespaces={
                    "ns2": "http://www.w3.org/1999/xlink",
                    "ns3": "http://www.loc.gov/METS/",
                },
            )
        ):
            e.attrib["LOCTYPE"] = "OTHER"
            e.attrib["OTHERLOCTYPE"] = "FILE"
            e.attrib["{http://www.w3.org/1999/xlink}href"] = pages[i]["tsList"][
                "transcripts"
            ][0]["fileName"]

        etree.indent(mets, space=" " * 4)
        with open(target / "mets.xml", "wb") as f:
            f.write(etree.tostring(mets, xml_declaration=True, pretty_print=True))

        for page in pages:
            doc = self.collections.get_transcript(
                collection_id, document_id, page["pageNr"]
            )
            etree.indent(doc, space=" " * 4)
            with open(target / page["tsList"]["transcripts"][0]["fileName"], "wb") as f:
                f.write(
                    etree.tostring(
                        doc,
                        encoding="utf-8",
                        xml_declaration=True,
                        pretty_print=True,
                        standalone=True,
                    )
                )


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
