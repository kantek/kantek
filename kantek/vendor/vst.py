"""Module to help using the CERN Vistars page."""
import json
import os
import secrets

import requests
import bs4
from bs4 import BeautifulSoup


class CERNVistar:
    """Simple class that gets the images from the CERN Vistars page."""

    def __init__(self, base_url=None):
        if base_url is None:
            self.base_url = (
                'https://op-webtools.web.cern.ch/Vistar/vistars.php'
            )
        self.base_url = base_url
        self.pages_dict = self._get_pages_dict()

    def _get_pages_dict(self) -> dict:
        """Parse the js code and extract the dictionary with the pages."""
        req = requests.get(self.base_url)
        data = {}
        if req.status_code == 200:
            html_doc = req.text
            soup = BeautifulSoup(html_doc, 'html.parser')
            script_tags = soup.find_all('script')

            s: bs4.element.Tag
            jstag = [s for s in script_tags if s.text][0]

            for l in jstag.text.split('\n'):
                if l.find('var vistarData') != -1:
                    data = json.loads(l.strip()[17:-1:])
        return data

    def get_pages(self) -> list:
        """Get all pages from the site.

        Returns: List of vistar pages.

        """
        return list(self.pages_dict.keys())

    def _get_page_url(self, page) -> str:
        try:
            page = self.pages_dict[page]
            return page['img']
        except KeyError:
            return ''

    def download_page(self, page_name: str) -> str:
        """Download the image."""
        base_url = self._get_page_url(page_name)
        file_name = base_url.split('/')[-1]
        image_path = 'tmp/' + file_name
        url = base_url + f'?{secrets.token_urlsafe(30)}'
        r = requests.get(url, stream=True)
        try:
            os.makedirs('tmp/')
        except OSError:
            pass

        with open(image_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

        return os.path.abspath(image_path)
