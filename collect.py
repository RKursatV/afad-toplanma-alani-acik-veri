
import json, scraper, unidecode
scraper.__init__()

allData = {}

toplanmaAlanlari = {}

iller = [[1, "Adana"], [2, "Adıyaman"], [46, "Kahramanmaraş"], [27, "Gaziantep"], [44, "Malatya"], [21, "Diyarbakır"], [79, "Kilis"], [63, "Şanlıurfa"], [31, "Hatay"], [80, "Osmaniye"]]

for ilCode, ilName in iller:
    getirIlce = scraper.getData(f"ilKodu={ilCode}&islem=ilceKodu")
    dat = json.loads(getirIlce.text)
    ilceler = (dat['data']['dataArr'])
    allData[ilName] = {'ilId': ilCode, 'ilceler': {}}
    for ilce in ilceler:
        allData[ilName]['ilceler'][ilce['name']] = {'ilceId': ilce['id'], 'mahalleler': {}}
        getirMahalle = scraper.getData(f"ilKodu={ilCode}&ilceKodu={ilce['id']}&islem=mahalleKodu")
        dat = json.loads(getirMahalle.text)
        mahalleler = (dat['data']['dataArr'])
        for mahalle in mahalleler:
            allData[ilName]['ilceler'][ilce['name']]['mahalleler'][mahalle['name']] = {'mahalleId': mahalle['id'], 'sokaklar': {}, 'toplanmaAlanlari': {}}
            getirSokak = scraper.getData(f"ilKodu={ilCode}&ilceKodu={ilce['id']}&sokakKodu={mahalle['id']}&islem=sokakKodu")
            dat = json.loads(getirSokak.text)

            queryResults = scraper.getFromMap(ilCode, ilce['id'], mahalle['id'])
            if queryResults is not None:
                for queryRes in queryResults:
                   allData[ilName]['ilceler'][ilce['name']]['mahalleler'][mahalle['name']]['toplanmaAlanlari'][queryRes['properties']['id']] = queryRes['properties']

            sokaklar = (dat['data']['dataArr'])
            for sokak in sokaklar:
                allData[ilName]['ilceler'][ilce['name']]['mahalleler'][mahalle['name']]['sokaklar'][sokak['name']] = {'sokakId': sokak['id']}

        print(ilce, 'done')
    dump = json.dumps(allData)
    with open(f"{unidecode.unidecode(ilName)}.json", 'w') as f:
        f.write(dump)
