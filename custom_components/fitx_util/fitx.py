from http.cookies import Morsel, SimpleCookie
import aiohttp
from base64 import b64encode, b64decode


class FitXApi:
    """FitX Api"""

    def __init__(self, studio: str, brand: str) -> None:
        self.studio = studio
        self.studio_int = (
            (b64decode(studio.encode("utf-8"))).decode("utf-8").split(":")[1]
        )
        self.brand = brand
        self.cookie_jar = aiohttp.CookieJar()
        self.session = aiohttp.ClientSession(cookie_jar=self.cookie_jar)

        self.public_facility_group = ""
        self.tenant = ""
        self.studio_name = ""
        self.has_init = False

        brand = brand.lower()
        if brand == "mcfit":
            self.api_host = "my.mcfit.com"
        elif brand == "fitx":
            self.api_host = "mein.fitx.de"
        else:
            raise ValueError("invalid brand")

    async def close(self):
        """Closes the ClientSession"""
        await self.session.close()

    async def init(self):
        """Initializes the API"""
        if self.has_init is True:
            return
        async with self.session.get(
            f"https://{self.api_host}/whitelabelconfigs/web"
        ) as response:
            response.raise_for_status()
            json_data = await response.json()
            self.public_facility_group = json_data["publicFacilityGroup"]
            self.tenant = json_data["tenantName"]

        headers = {"x-public-facility-group": self.public_facility_group}
        async with self.session.get(
            f"https://{self.api_host}/sponsorship/v1/public/studios/{self.studio}",
            headers=headers,
        ) as response:
            response.raise_for_status()
            json_data = await response.json()
            self.studio_name = json_data["name"]
        self.has_init = True

    async def login(self, email: str, password: str):
        """Login endpoint"""
        headers = {
            "authority": self.api_host,
            "accept": "*/*",
            "accept-language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
            "authorization": f'Basic {(b64encode((email+":"+password).encode("utf-8"))).decode("utf-8")}',
            "origin": "https://" + self.api_host,
            "referer": "https://" + self.api_host + "/login-register",
            "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36",
            "x-nox-client-type": "WEB",
            "x-public-facility-group": self.public_facility_group,
            "x-tenant": self.tenant,
        }
        json_data = {
            "username": email,
            "password": password,
        }
        async with self.session.post(
            f"https://{self.api_host}/login", headers=headers, json=json_data
        ) as response:
            response.raise_for_status()
            # session now saved in cookie jar

    async def get_utilv2(self):
        """Utilization endpoint"""
        headers = {
            "authority": self.api_host,
            "accept": "*/*",
            "accept-language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "application/json",
            "referer": "https://" + self.api_host + "/studio/" + self.studio,
            "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36",
            "x-ms-web-context": "/studio/" + self.studio,
            "x-nox-client-type": "WEB",
            "x-nox-web-context": "",
            "x-public-facility-group": self.public_facility_group,
            "x-tenant": self.tenant,
        }
        async with self.session.get(
            f"https://{self.api_host}/nox/v1/studios/{self.studio_int}/utilization/v2/today",
            headers=headers,
        ) as response:
            response.raise_for_status()
            return await response.json()

    def get_session(self) -> Morsel[str]:
        """Returns session"""
        for _, cookie in self.cookie_jar.filter_cookies(
            "https://" + self.api_host
        ).items():
            if cookie.key == "SESSION":
                return cookie
        return None

    def set_session(self, ses: str):
        """Set session"""
        self.cookie_jar.update_cookies(
            SimpleCookie(
                f"SESSION={ses}; Domain={self.api_host}; Path=/; Secure; HttpOnly; SameSite=strict;"
            )
        )
