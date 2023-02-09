import json
import os
import re
import warnings
from typing import Any, List, Sized

import requests

from consts import (
    ACIL_TOPLAMA_URL,
    BASE_URL,
    DATA_HEADER,
    MAP_HEADER,
    QUERY_POINT_HEADER,
    TOKEN_HEADER,
)

warnings.filterwarnings("ignore", message="Unverified HTTPS request")
session = requests.Session()
session.verify = False


class EmergencyMeetingAreas:
    """Emergency Meeting Areas."""

    def _get_data(self, payload: str) -> str:
        """
        Get data from turkiye.gov.tr for emergency meeting areas

        Args:
            payload: City, district, neighborhood information.

        Returns:
            Emergency assembly area locations.
        """
        res = session.post(
            f"{BASE_URL}/{ACIL_TOPLAMA_URL}?submit",
            headers=DATA_HEADER,
            data=f"token={os.environ['token']}&ajax=1&pn=/{ACIL_TOPLAMA_URL}&{payload}",
        )
        if res.headers["Content-Type"].startswith("application/json"):
            return res
        self._get_token()
        return self._get_data(payload)

    def _get_token(self) -> dict[str, Any]:
        """Get token."""
        response = session.get(
            f"{BASE_URL}/{ACIL_TOPLAMA_URL}",
            headers=TOKEN_HEADER,
        )
        return re.search(r'data-token=\"([^"]*)\"', response.text).group(1)

    def _get_area_with_point(self, lat: float, lng: float) -> dict[str, Any]:
        """
        Get area with cordinates.

        Args:
            lat: Latitude.
            lng: Longitude.

        Returns:
            Area information.
        """
        return session.post(
            f"{BASE_URL}/{ACIL_TOPLAMA_URL}?harita=goster&submit",
            headers=QUERY_POINT_HEADER,
            data={
                "pn": f"/{ACIL_TOPLAMA_URL}",
                "ajax": "1",
                "token": os.environ["token"],
                "islem": "getAlanlarForNokta",
                "lat": lat,
                "lng": lng,
            },
        ).json()

    def _get_data_from_map(
        self, county_code: int, state_code: int, district_code: int
    ) -> list[dict[str, Any]] | None:
        """
        Get data from map.

        Args:
            county_code: County Code.
            state_code: State code.
            district_code: District code.

        Returns:
            Area information.
        """
        res = session.post(
            f"{BASE_URL}/{ACIL_TOPLAMA_URL}?submit",
            headers=MAP_HEADER,
            data={
                "ilKodu": county_code,
                "ilceKodu": state_code,
                "mahalleKodu": district_code,
                "sokakKodu": "",
                "token": os.environ["token"],
                "btn": "Sorgula",
            },
        )
        if legit_areas := re.search(r"toplanmaAlanlari = (.*);", res.text):
            legit_areas = legit_areas.group(1)
        else:
            return None
        if legit_areas == "null":
            return None

        queries = self._get_vertices(
            json.loads(legit_areas)[0]["geometry"]["coordinates"]
        )
        result_list: list[dict[str, Any]] = []

        for query in queries:
            area_points = self._get_area_with_point(query[0], query[1])

            while area_points is None:
                self._get_token()
                area_points = self._get_area_with_point(query[0], query[1])

            for area_point in area_points["features"]:
                result_list.append(area_point)
        return result_list

    def _get_vertices(
        self, polygon: list[list[float]]
    ) -> list[list[float]] | list[float]:
        process: list[float] = polygon[0]
        if len(process) < 6.0:
            return process
        res: list[float] = []
        process.sort(key=lambda x: x[0])
        res.append(process[0])
        process.sort(key=lambda x: x[1])
        res.append(process[0])
        process.sort(key=lambda x: x[0], reverse=True)
        res.append(process[0])
        process.sort(key=lambda x: x[1], reverse=True)
        res.append(process[0])

        avg1 = sum([x[0] for x in res]) / 4
        avg2 = sum([x[1] for x in res]) / 4
        res.append([avg1, avg2])  # type: ignore
        return res

    def run(self):
        os.environ["token"] = self._get_token()  # type: ignore


meeting_areas = EmergencyMeetingAreas()
meeting_areas.run()
