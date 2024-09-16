# Transkribus Rest API Client

![Tests](https://github.com/jnphilipp/transkribus_rest_api/actions/workflows/tests.yml/badge.svg)
[![pypi Version](https://img.shields.io/pypi/v/transkribus_rest_api.svg?logo=pypi&logoColor=white)](https://pypi.org/project/transkribus_rest_api/)

Python bindings for the [Transkribus REST API](https://readcoop.eu/transkribus/docu/rest-api/).

## Usage

```python
from transkribus_rest_api import transkribus_rest_api
from transkribus_rest_api.types import UploadPage

with transkribus_rest_api(USERNAME, PASSWORD) as api:
    api.upload_document(COLLECTION_ID,
    "Test title",
    pages=[
        UploadPage(image=IMAGE_PATH, page_xml=PAGE_XML_PATH, page_nr=1)
        UploadPage(image=IMAGE_PATH, page_xml=PAGE_XML_PATH, page_nr=2)
    ],
```
