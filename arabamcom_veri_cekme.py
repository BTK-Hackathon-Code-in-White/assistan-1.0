from selenium import webdriver
import chromedriver_autoinstaller
import time
from selenium.webdriver.common.by import By
import sqlite3

# Veri tabanı dosyasını oluştur veya bağlan
db_name = "araba_verileri.db"
# connection = sqlite3.connect(db_name)
# cursor = connection.cursor()

# # Tablo oluşturma sorgusu
# create_table_query = """
# CREATE TABLE IF NOT EXISTS araba_ilanlari (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     link TEXT NOT NULL,
#     fiyat REAL,
#     marka TEXT NOT NULL,
#     seri TEXT NOT NULL,
#     model TEXT NOT NULL,
#     yil INTEGER NOT NULL,
#     km REAL,
#     vites TEXT,
#     yakit TEXT,
#     kasa_tipi TEXT,
#     renk TEXT,
#     boya TEXT,
#     parca TEXT
# );
# """
# cursor.execute(create_table_query)
# connection.commit()
# connection.close()

#print(f"{db_name} veri tabanında 'araba_ilanlari' tablosu oluşturuldu.")

chromedriver_autoinstaller.install()
driver = webdriver.Chrome()
otomobiller=["hyundai","honda", "mercedes-benz", "opel", "renault", "toyota", "volkswagen"]

try:
    for name in otomobiller:
        for page in range(1, 51):
            driver.get(f"https://www.arabam.com/ikinci-el/otomobil/{name}-sahibinden?page={page}")
            time.sleep(3)

            for row in range(1, 23):
                if row in [6, 12]:
                    continue

                try:
                    element = driver.find_element(By.XPATH, f"/html/body/div[2]/div[2]/div[3]/div/div[2]/div[2]/div[2]/table/tbody/tr[{row}]/td[2]/a")
                    link = element.get_attribute('href')
                    element.click()
                    time.sleep(3)

                    veriler = [link]

                    # Fiyat
                    fiyat_element = driver.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[3]/div/div[1]/div[1]/div[2]/div[2]/div[1]/div[1]/div[2]/div[1]/div')
                    fiyat_text = fiyat_element.text.replace("TL", "").replace(".", "").replace(",", "").strip()
                    try:
                        fiyat = float(fiyat_text)
                    except ValueError:
                        fiyat = None
                    veriler.append(fiyat)

                    # Marka, Seri, Model, Yıl, KM, Vites, Yakıt, Kasa Tipi, Renk
                    for i in range(3, 12):
                        try:
                            value = driver.find_element(By.XPATH, f'/html/body/div[2]/div[2]/div[3]/div/div[1]/div[1]/div[2]/div[2]/div[2]/div[{i}]/div[2]').text
                            veriler.append(value)
                        except:
                            veriler.append("")

                    # Boya Bilgisi
                    boya_element = driver.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[3]/div/div[1]/div[2]/div[2]/div[2]/div/div[2]/div[1]/div[3]/ul/li')
                    boya = "Parça Boyalı" if boya_element.text != "-" else "Boya Orijinal"
                    veriler.append(boya)

                    # Parça Bilgisi
                    parca_element = driver.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[3]/div/div[1]/div[2]/div[2]/div[2]/div/div[2]/div[1]/div[4]/ul/li')
                    parca = "Parça Değişmiş" if parca_element.text != "-" else "Parça Orijinal"
                    veriler.append(parca)

                    # Veritabanına kaydet
                    connection = sqlite3.connect(db_name)
                    cursor = connection.cursor()

                    insert_query = """
                    INSERT INTO araba_ilanlari (
                        link, fiyat, marka, seri, model, yil, km, vites, yakit, kasa_tipi, renk, boya, parca
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    cursor.execute(insert_query, veriler)
                    connection.commit()
                    connection.close()

                    print(f"Kayıt eklendi: {link}")

                    driver.back()
                    time.sleep(2)

                except Exception as e:
                    print(f"Satırda hata oluştu: {e}")
                    driver.back()
                    continue

except Exception as e:
    print(f"Genel hata: {e}")

finally:
    driver.quit()
