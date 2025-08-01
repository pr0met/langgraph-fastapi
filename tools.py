import httpx
import os
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Dict
import json

def _get_auth_headers() -> dict:
    """
    A helper function to get the authentication headers.
    """
    token = os.environ.get("LUMAPPS_TOKEN")
    if not token:
        raise ValueError("LUMAPPS_TOKEN environment variable not set")
    return {"Authorization": f"Bearer {token}"}

async def _make_http_request(url: str, method: str = "GET", **kwargs) -> dict:
    """
    A helper function to make asynchronous HTTP requests.
    """
    async with httpx.AsyncClient() as client:
        response = await client.request(method, url, **kwargs)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()

@tool
async def get_content_types() -> dict:
    """
    Retrieve the list of available content types that are used to create and categorize content on the platform.
    Each content type has a name and a description which should inform about what they are for, along with their id.
    """
    print("Calling tool get_content_types")
    url = "https://master.ms-cell-001.dev.api.lumapps.com/_ah/api/lumsites/v1/customcontenttype/list?maxResults=100&instance=4259137396864449&fields=items(id,name,description)"
    headers = _get_auth_headers()
    result = await _make_http_request(url, headers=headers)
    print(f"Tool returned {result}")
    return result


@tool
async def get_content_type_templates(customcontenttype: str) -> dict:
    """
    Retrieve the templates of a given content type. A template can be used to create a piece of content.
    Each template has a name and a description that should inform about its use.
    The id of the content type must be passed as a parameter.
    """
    print(f"Calling tool get_content_type_templates with customcontenttype={customcontenttype}")
    url = f"https://master.ms-cell-001.dev.api.lumapps.com/_ah/api/lumsites/v1/template/list?instance=4259137396864449&fields=items(id,name,description)&customcontenttype={customcontenttype}"
    headers = _get_auth_headers()
    result = await _make_http_request(url, headers=headers)
    print(f"Tool returned {result}")
    return result


@tool
async def get_template_details(uid: str) -> dict:
    """
    Get the full details of a given template.
    """
    print(f"Calling tool get_template_details with uid={uid}")
    url = f"https://master.ms-cell-001.dev.api.lumapps.com/_ah/api/lumsites/v1/template/get?uid={uid}"
    headers = _get_auth_headers()
    result = await _make_http_request(url, headers=headers)
    print(f"Tool returned {result}")
    return result

class CreateContentParameters(BaseModel):
    template: Dict = Field(..., description="The template to use to create the piece of content. This is the full template object as returned by the tool get_template_details.")
    customContentTypeId: str = Field(..., description="The id of the content type to use.", example="6497125405818880")
    title: str = Field(..., description="The content title.", example="A great pizza place in Lyon.")
    slug: str = Field(..., description="The content slug. This is used to display a human-readable bit of text in the URL when viewing the web page in a browser. A slug can only contain alphabetical characters and dashes. It must be unique accross all contents in the instance.", example="great-pizza-lyon")
    html_text: str = Field(..., description="The content text, formatted as HTML. This is the whole information contained in the piece of content, in HTML form.")


@tool("create_content", args_schema=CreateContentParameters)
async def create_content(template: Dict, customContentTypeId: str, title: str, slug: str, html_text: str) -> dict:
    """
    Call this tool to create a piece of content in a content type, from a template, a title, a slug, and the actual html text.
    When creating a piece of content, make sure to use nice formatting in the HTML text to ensure a visually appealing experience. Examples: use headings, line breaks, bold, emojis, etc.
    """
    print(f"Calling tool create_content with customContentTypeId='{customContentTypeId}', title='{title}' and slug='{slug}'")
    url = "https://master.ms-cell-001.dev.api.lumapps.com/_ah/api/lumsites/v1/content/save"
    headers = _get_auth_headers()
    body = {
        "type": "custom",
        "customer": "5663677907730432",
        "instance": "4259137396864449",
        "template": _fill_html_widget_in_template(template, html_text),
        "customContentType": customContentTypeId,
        "feedKeys": template.get("feedKeys"),
        "title": {"en": title},
        "slug": {"en": slug},
        "status": "DRAFT"
    }
    print(f"Request body:\n\n{json.dumps(body)}")
    result = await _make_http_request(url, method="POST", headers=headers, json=body)
    print(f"Tool returned {result}")
    return result


def _fill_html_widget_in_template(template, html_string):
    """
    Recursively finds the first 'html' widget in a template and fills it.

    Args:
        template: The template to search through.
        html_string: The HTML content to add.

    Returns:
        The modified template.
    """
    def _find_and_update(data):
        """
        Inner recursive function to find and update the widget.
        Returns True if the widget was found and updated, False otherwise.
        """
        if isinstance(data, dict):
            # Check if the current dictionary is the target widget
            if data.get("type") == "widget" and data.get("widgetType") == "html":
                if "properties" not in data:
                    data["properties"] = {}
                data["properties"]["content"] = {"en": html_string}
                return True  # Found and updated

            # Prioritize searching in 'components' and 'cells' keys
            for key in ["components", "cells"]:
                if key in data and isinstance(data[key], (list, dict)):
                    if _find_and_update(data[key]):
                        return True # Propagate stop signal

        elif isinstance(data, list):
            # If it's a list, iterate over its items
            for item in data:
                if _find_and_update(item):
                    return True # Propagate stop signal

        return False # Target not found in this branch

    _find_and_update(template)
    return template