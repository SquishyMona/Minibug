import requests
import os
from dotenv import load_dotenv
from read import odoo_read

load_dotenv('../../.env')

url = f'{os.getenv("ODOO_URL")}/json/2'
api_key = os.getenv('ODOO_API_KEY')

headers = {
    "Authorization": f"bearer {api_key}",
    "Content-Type": "application/json",
    "User-Agent": "Minibug python-requests/2.34.2"
}

def test_request():
    res = requests.post(
        f'{url}/res.partner/search_read',
        headers = headers,
        json = {
        "domain": [
            ["name", "ilike", "Squishy"]
        ]
    })

    print(res.status_code)

print(odoo_read(
    'res.partner',
    [('name', 'ilike', 'iacio')], 
    ['display_name', 'id', 'email']
))