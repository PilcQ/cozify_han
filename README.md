# Cozify HAN for Home Assistant

Tämä integraatio tuo Cozify HAN -lukijan sähkömittaustiedot suoraan Home Assistantiin paikallisverkon yli. Se hakee tiedot suoraan Cozify HAN laitteen REST-rajapinnasta, mikä tekee siitä nopean ja luotettavan.



## Ominaisuudet
* **Reaaliaikainen seuranta:** Päivitysväli oletuksena 5 sekuntia.
* **Kokonaiskulutus:** Sähköenergian tuonti (Import) ja vienti (Export) kWh.
* **Vaihekohtaiset tiedot:** Teho (W), Jännite (V) ja Virta (A) jokaiselle vaiheelle (L1, L2, L3).
* **Helppo asennus:** Täysi Config Flow -tuki (asetukset suoraan käyttöliittymästä).

## Asennus

### Vaihe 1: HACS (Custom Repository)
1. Avaa Home Assistant ja mene **HACS** -> **Integrations**.
2. Klikkaa kolmea pistettä oikeassa yläkulmassa ja valitse **Custom repositories**.
3. Lisää tämän repositorion osoite: `https://github.com/pilcq/cozify_han`
4. Valitse kategoriaksi **Integration** ja klikkaa **Add**.
5. Etsi "Cozify HAN" listalta ja klikkaa **Download**.
6. **Käynnistä Home Assistant uudelleen.**

### Vaihe 2: Integraation käyttöönotto
1. Mene **Asetukset** -> **Laitteet ja palvelut**.
2. Klikkaa **Lisää integraatio**.
3. Etsi "Cozify HAN".
4. Syötä laitteesi **IP-osoite** (esim. `192.168.1.10`) ja klikkaa Lähetä.

## Sähkön hinnan seuranta (Esimerkki)

Voit käyttää integraation luomaa `sensor.cozify_han_power_total` -sensoria laskemaan sähkön hintaa reaaliajassa. Suosittelemme käyttämään **Riemann sum integral** -sensoria muuttamaan hetkellinen hinta (c/h) kumulatiiviseksi kulutukseksi (c), jota voit seurata **Utility Meterin** avulla päivä-, viikko- ja kuukausitasolla.

## Kehitys ja tuki
Tämä on yhteisöpohjainen integraatio. Jos huomaat virheitä tai haluat kehittää sitä eteenpäin, luo "Issue" tai "Pull Request" GitHubissa.

---
*Huom: Tämä integraatio ei ole Cozify Oy:n virallinen tuote.*
