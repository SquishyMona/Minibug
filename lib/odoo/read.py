import requests
import os
from dotenv import load_dotenv

url = f'{os.getenv("ODOO_URL")}/json/2'
api_key = os.getenv('ODOO_API_KEY')

headers = {
    "Authorization": f"bearer {api_key}",
    "Content-Type": "application/json",
    "User-Agent": "Minibug python-requests/2.34.2"
}

def odoo_read(model: str, query: list, fields: list = None):
    res = requests.post(
        f'{url}/{model}/search_read',
        headers=headers,
        json={
            "domain": query,
            "fields": fields
        }
    )

    res.raise_for_status()
    return res.json()