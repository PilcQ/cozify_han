# Cozify HAN for Home Assistant

Tämä integraatio tuo Cozify HAN -lukijan sähkömittaustiedot suoraan Home Assistantiin paikallisverkon yli. Se hakee tiedot suoraan Cozify HAN laitteen REST-rajapinnasta, mikä tekee siitä nopean ja luotettavan.



## Ominaisuudet
* **Reaaliaikainen seuranta:** Päivitysväli oletuksena 5 sekuntia.
* **Kokonaiskulutus:** Sähköenergian osto (Import) ja myynti (Export) kWh. Myyntiä voi yleensä olla jos on esimerkiksi aurinkopaneeleja.
* **Vaihekohtaiset tiedot:** Teho (W), Jännite (V), Virta (A) ja Loisteho (VAr) jokaiselle vaiheelle (L1, L2, L3).
* **Helppo asennus:** Täysi Config Flow -tuki (Cozify HAN laitteen IP:n asetus suoraan käyttöliittymästä).

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

## Cozify HAN
Cozify HAN on kotimainen, avainlipputuote, joka tuo sähkömittarin HAN/P1-rajapinnan tiedot reaaliaikaisesti paikallisverkkoon, pilveen ja älyjärjestelmiin. Se on suunniteltu erityisesti pohjoisiin olosuhteisiin, helppoon itseasennukseen ja laajaan integraatioon (RestAPI, MQTT ja Modbus) energiankäytön optimointia, kuormanhallintaa ja automaatiota varten.

## Keskeiset ominaisuudet ##
* Reaaliaikainen mittausdata: hetkellinen teho (W/kW), jännite (V), virta (A) ja kumulatiiviset kulutusluvut (kWh) vaihekohtaisesti, kaikki data mitä HAN/P1 väylästä tulee
* Tukee Ethernet (RJ45)‑yhteyttä ja WiFi‑yhteyttä; mahdollisuus vaihtaa alkuperäinen antenni RP‑SMA‑ulkoinen antenniin parempaa kantamaa varten
* Sisäänrakennettu HTTP OpenAPI‑palvelin (/meter), MQTT‑lähetys ja Modbus (TCP)‑rajapinnat B2B‑integraatioihin
* Toimii Android- ja iOS‑sovelluksen kanssa, OTA‑firmware‑päivitykset takaavat jatkokehityksen ja tietoturvan
* Suunniteltu toimimaan pohjoismaisissa olosuhteissa –40 °C … +60 °C ja samalla IP‑luokituksella kuin sähkömittari

## Mitä laite tarjoaa käyttäjälle ##
* Täsmällinen reaaliaikainen näkyvyys sähkönkulutukseen ja tuotantoon
* Vaihekohtaisten kuormitusnäkymien avulla helppo tunnistaa ylikuormitusriskit ja tasata kuormia
* Parempi mahdollisuus hyödyntää tunti- ja varttihintaa sekä reaaliaikaista ohjausta älykkäässä latauksessa ja lämmityksessä
* Integroituu olemassa oleviin kotiautomaatioalustoihin (esim. Home Assistant) ja energianhallintajärjestelmiin (EVCC.io jne.). Rajapintojen Modbus (TCP), MQTT ja RestAPI kautta integrointimmahdollisuudet ovat rajattomat. Lisää rajapintoja tulevaisuudessa.

## Tekniset tiedot ##
* Liitännät: RJ12 (HAN/P1), RJ45 (Ethernet), WiFi , USB‑C (lisävirta),  RP-SMA (WiFi lisäantenni)
* Rajapinnat: OpenAPI (HTTP, /meter), MQTT (JSON‑payload), Modbus TCP (rekisterit)
* Käyttöympäristö: −40 °C … +60 °C; kotelo ja liitännät sähkömittariluokan mukaiset

## Asennus ja käyttöönotto ##
* Itseasennettava; sijoitetaan sähkömittarin viereen ja kiinnitetään esim. kaksipuolisella teipillä
* Jos mittari on metallisessa kaapissa, suositellaan Ethernet‑yhteyttä tai ulkoista RP‑SMA‑antennia luotettavan yhteyden varmistamiseksi

## Kehitys ja tuki
Tämä on yhteisöpohjainen integraatio. Jos huomaat virheitä tai haluat kehittää sitä eteenpäin, luo "Issue" tai "Pull Request" GitHubissa.

---
*Huom: Tämä integraatio ei ole Cozify Oy:n virallinen tuote.*
