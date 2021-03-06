import requests
from urllib.parse import unquote
import time
import pathlib
import shutil
import re
import logging
from bs4 import BeautifulSoup as bs
from utils import request_headers

logging.getLogger("urllib3").propagate = False

FORMAT = logging.Formatter("%(levelname)s : %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(FORMAT)
logger.addHandler(ch)


def get_filename_from_cd(cd):
    """
    Get filename from content-disposition
    """
    if not cd:
        return None
    fname = re.findall("filename=(.+)", cd)
    if len(fname) == 0:
        return None
    return fname[0]


if __name__ == "__main__":
    # change these to your need 
    show_name = "No Guns Life"
    download_dir = pathlib.Path("E:\\torrent\\torrent_files")
    
    
    
    
    # no change from here on 
    show_url = "https://horriblesubs.info/" + "-".join(
        [i.lower() for i in show_name.split(" ")]
    )
    
    showid = 0
    nextid = 0
    retry = True
    retry_time = 0
    links = {}
    cook = {
        "cookie": "__cfduid=dc88541bab82a80aeea5f7f66bf2b85471597159976",
    }
    cookie = requests.cookies.create_cookie(
        list(cook.keys())[0], cook[list(cook.keys())[0]]
    )
    logger.info("getting show id")
    while retry:
        try:
            if not showid:
                # get show id
                with requests.Session() as session:
                    url = show_url
                    session.cookies.set_cookie(cookie)
                    req = session.get(url=url, headers=request_headers,)
                    if req.status_code == 400:
                        logger.warning(f"No show by name {show_name}")
                        retry = False
                        break
                    txt = req.text
                    parsed_webpage = bs(txt, "lxml")
                    js = parsed_webpage.find_all("script", type="text/javascript")
                    for tag in js:
                        string = tag.string
                        if string:
                            if "hs_showid" in tag.string:
                                showid = string.split()[-1].replace(";", "")

            else:
                # get all torrents
                with requests.Session() as session:

                    url = f"https://horriblesubs.info/api.php?method=getshows&type=show&showid={showid}&nextid={nextid}"
                    session.cookies.set_cookie(cookie)
                    req = session.get(url=url, headers=request_headers,)
                    logger.info("getting urls ....")
                    txt = req.text
                    if txt == "DONE":
                        retry = False
                        pass
                    parsed_webpage = bs(txt, "lxml")
                    name = list(
                        parsed_webpage.find(
                            class_="rls-info-container"
                        ).stripped_strings
                    )[1]
                    link_1080 = parsed_webpage.find_all(
                        "div", class_="rls-link link-1080p"
                    )
                    for div in link_1080:
                        ep = div["id"]
                        span = div.find_all("span", class_="dl-type hs-torrent-link")
                        for a in span:
                            links[str(name + "  " + ep)] = a.find("a")["href"]
                    nextid += 1
        except Exception as e:
            pass

    logger.info("done retriving links \n downloading .torrent files",)
    logger.debug(f"saving in {str(download_dir)}")
    for k, v in links.items():
        retry = True
        logger.info(f"getting .torrent for {k}")
        while retry:
            try:
                with requests.Session() as session:
                    url = v
                    session.cookies.set_cookie(cookie)
                    req = session.get(url=url, headers=request_headers,)
                    retry = False
                    logger.debug(f"got {url}")
                    filename = get_filename_from_cd(
                        req.headers.get("content-disposition")
                    )
                    filename = (
                        unquote(filename.split(" ")[0])
                        .replace(";", "")
                        .replace('"', "")
                    )
                    with open(file=download_dir / filename, mode="wb") as torrent_file:
                        torrent_file.write(req.content)
            except requests.ConnectionError:
                pass
            except Exception as e:
                logger.warning(e)
