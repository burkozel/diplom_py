from urllib.parse import urljoin
import requests
import time
import datetime
from datetime import datetime
import json


# x= time.time()
# print(x)
# a = time.ctime(time.time())
# print(a)
# photo.date = str(time.ctime(time.time()))

class Photos:
    def __init__(self, date, likes, sizes):
        self.date = date
        self.likes = likes
        self.sizes = sizes
        self.size_type = sizes["type"]
        self.url = sizes["url"]
        self.maxsize = max(sizes["width"], sizes["height"])

    def __repr__(self):
        return f"date: {self.date}, likes: {self.likes}, size: {self.maxsize}, url: {self.url}"


class VKAPI:
    API_BASE_URL = "https://api.vk.com/method/"
    TOKEN = "4b9b61f34eaab95b07561e4113dc0bd5501f3d79cbbd66d01834b4efef4f721d4c384638ed2a05d4d918e"
    V = "5.126"

    def __init__(self):
        self.token = self.TOKEN
        self.v = self.V

    @staticmethod
    def find_largest(sizes):
        sizes_docs = ["s", "m", "x", "o", "p", "q", "r", "y", "z", "w"]
        for letter in sizes_docs:
            for size in sizes:
                if size["type"] == letter:
                    return size

    # документация по обозначениям размеров вк

    def get_photos(self, user_id, kolvo=5):
        url = urljoin(self.API_BASE_URL, "photos.get")
        response = requests.get(url, params={
            "access_token": self.TOKEN,
            "v": self.V,
            "owner_id": user_id,
            "album_id": "profile",
            "photo_sizes": 1,
            "extended": 1
        }).json().get("response").get("items")

        return sorted(
            [Photos(photo.get("date"), photo.get("likes")["count"], self.find_largest(photo.get("sizes"))) for photo in
             response], key=lambda photos: photos.maxsize, reverse=True)[:kolvo]


class YaDAPI:
    TOKEN = ""
    HEADERS = {"Authorization": f"OAuth{TOKEN}"}

    def __init__(self, token: str):
        self.auth = f"OAuth {token}"

    @staticmethod
    def check_folder_name(new, old):
        n = 1
        if new not in old:
            return new
        else:
            new = new + "(" + str(n) + ")"
            while new in old:
                new = new.replace("(" + str(n) + ")", "(" + str(n + 1) + ")")
                n += 1
            return new

    # схема добавления папки с существующим названием. проверка старых папок

    @staticmethod
    def create_photo_names(photos):
        for photo in photos:
            photo.name = str(photo.likes)
            if [p.likes for p in photos].count(photo.likes) > 1:
                photo.name += "_" + str(datetime.fromtimestamp(photo.date).strftime("%d_%m_%Y_%H_%M_%S"))
            photo.name += ".jpg"

    # если встречается больше 1 фоторафии с таким же названием, то добавляется дата к обеим

    def get_old_folders(self):
        return [folders["name"] for folders in (
            requests.get("https://cloud-api.yandex.net/v1/disk/resources", params={"path": "/"},
                         headers={"Authorization": self.auth}).json().get("_embedded").get("items")) if
                folders["type"] == "dir"]

    # вернет урлы папок через _embedded

    def create_folder(self, folder_name):
        response = requests.put("https://cloud-api.yandex.net/v1/disk/resources", params={"path": "/" + folder_name},
                                headers={"Authorization": self.auth})
        print(f"Папка создается '{folder_name}':")
        if response.status_code == 201:
            print(f"Папка '{folder_name}' создана")
            return response.ok
        else:
            print(f"Папка '{folder_name}' не создана")
            return response.ok

    def upload(self, user_id, photos):
        uf = self.check_folder_name(user_id, self.get_old_folders())
        self.create_photo_names(photos)
        if self.create_folder(uf):
            logs = []
            for photo in photos:
                response = requests.post("https://cloud-api.yandex.net/v1/disk/resources/upload",
                                         params={"path": "/" + str(uf) + "/" + photo.name, "url": photo.url},
                                         headers={"Authorization": self.auth})
                d = json.loads(response.text)
                print(response.text)
                while True:
                    response2 = requests.get(d["href"], headers={"Authorization": self.auth}).json()
                    print("Ожидайте...")
                    time.sleep(1)
                    print(response2)
                    if response2["status"] == "success":
                        print(response2)
                        print(f"Фотография '{photo.name}' загружена")
                        logs.append({"file_name": photo.name, "size": photo.size_type})
                        break
                    if response2["status"] == "failed":
                        print(f"Фотография '{photo.name}' не загружена. Ошибка: {response.status_code}")
                        break
            print(logs)


def main():
    disktoken = input("Введите токен Яндекс.Диска: ")
    user_id = input("Введите id пользователя VK: ")
    kolvo = input("Введите количество фотографий для загрузки: ")
    vkapi = VKAPI()
    diskapi: YaDAPI = YaDAPI(disktoken)
    diskapi.upload(user_id, vkapi.get_photos(user_id, int(kolvo)))


main()