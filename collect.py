import json
from typing import Any

import unidecode
from scraper import meeting_areas

data: dict[str, Any] = {}

counties: list[list[Any]] = [
    [1, "Adana"],
    [2, "Adıyaman"],
    [46, "Kahramanmaraş"],
    [27, "Gaziantep"],
    [44, "Malatya"],
    [21, "Diyarbakır"],
    [79, "Kilis"],
    [63, "Şanlıurfa"],
    [31, "Hatay"],
    [80, "Osmaniye"],
]
for county_code, county_name in counties:
    state_response = json.loads(
        meeting_areas._get_data(f"ilKodu={county_code}&islem=ilceKodu").text
    )
    states = state_response["data"]["dataArr"]
    data[county_name] = {"ilId": county_code, "ilceler": {}}
    for state in states:
        data[county_name]["ilceler"][state["name"]] = {
            "ilceId": state["id"],
            "mahalleler": {},
        }
        district_data = json.loads(
            meeting_areas._get_data(
                f"ilKodu={county_code}&ilceKodu={state['id']}&islem=mahalleKodu"
            ).text
        )
        districts = district_data["data"]["dataArr"]
        for district in districts:
            data[county_name]["ilceler"][state["name"]]["mahalleler"][
                district["name"]
            ] = {
                "mahalleId": district["id"],
                "sokaklar": {},
                "toplanmaAlanlari": {},
            }
            streets_data = meeting_areas._get_data(
                f"ilKodu={county_code}&ilceKodu={state['id']}&sokakKodu={district['id']}&islem=sokakKodu"
            )
            streets = json.loads(streets_data.text)

            results = meeting_areas._get_data_from_map(
                county_code, state["id"], district["id"]
            )
            if results is not None:
                for result in results:
                    data[county_name]["ilceler"][state["name"]]["mahalleler"][
                        district["name"]
                    ]["toplanmaAlanlari"][result["properties"]["id"]] = result[
                        "properties"
                    ]

            streets_info = streets["data"]["dataArr"]
            for street in streets_info:
                data[county_name]["ilceler"][state["name"]]["mahalleler"][
                    district["name"]
                ]["sokaklar"][street["name"]] = {"sokakId": street["id"]}

        print(state, "done")
    dump = json.dumps(data)
    with open(f"{unidecode.unidecode(county_name)}.json", "w") as f:
        f.write(dump)
