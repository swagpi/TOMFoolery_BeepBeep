from urllib.request import urlretrieve
import zipfile
import os

def download_gtfs_data(url: str="https://download.gtfs.de/germany/free/latest.zip",
                       filename: str="latest.zip",
                       keep_zip: bool = False):
    """
    fetches base gtfs data
    :param url: url of gtfs data to be fetched
    :param filename: name of folder gtfs data is to be stored
    :param keep_zip: decides if downloaded zip archive should be kept or deleted after unzipping
    :return:
    """

    urlretrieve(url,filename)

    with zipfile.ZipFile(filename, 'r') as zip:
        zip.extractall(filename[:-4])
    if not keep_zip:
        os.remove(filename)