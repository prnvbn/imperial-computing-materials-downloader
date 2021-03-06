import sys
import os
import json
import subprocess
import datetime as dt

sys.path.insert(1, './lib')
from config import *
from webhelpers import *
from argsparser import *

from getpass import getpass
from distutils.dir_util import remove_tree, copy_tree
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException


if __name__ == "__main__":

    args = get_args()
    exit = False

    ############################# NON SELENIUM FLAGS #############################
        # open("lib/auth.json")
    try:
        open("auth.json")
    except FileNotFoundError:
        file = open("auth.json", "w+")
        file.write('{"shortcode": "XXXXX", "password": "XXXXX", "directory": "XXXXX"}')

    quit()

    with open("lib/auth.json") as authfile:
        auth = json.load(authfile)
        if args.credentials:
            [print(f"Your {key} is set as {auth[key]}")
             for key in ["shortcode", "directory"]]
            exit = True

        if args.update_chromedriver:
            subprocess.call(["sh", "./get_chromedriver.sh"])
            exit = True

        if s := args.shortcode:
            auth["shortcode"] = s
            print(f"Shortcode set to {s}")
            exit = True

        if args.password:
            pswd = getpass('Password:')
            auth["password"] = pswd
            if pswd == "":
                print("Password can not be empty")
            print(f"Password has been set")
            exit = True

        if d := args.dir:
            if os.path.isdir(d):
                print(f"Directory set to {d}")
            else:
                print(f"{d} is not a valid directory!!!")

                response = input(
                    f"Do you want to create directory {d}? (Y/n) ").lower()
                if response == "y" or response == "or":
                    print(f"Made directory {d}")
                    os.mkdir(d)
                else:
                    print(f"Please pass in a valid directory")

            auth["directory"] = d
            exit = True

    with open("lib/auth.json", "wt") as authfile:
        json.dump(auth, authfile)

    if exit:
        quit()

    headless = not args.real
    verbose = args.verbose

    ############################# CHROME WEBDRIVER OPTIONS #############################
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")

    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--verbose')
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": "./",
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing_for_trusted_sources_enabled": False,
        "safebrowsing.enabled": False
    })

    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('headless')

    try:
        driver = webdriver.Chrome(
            options=chrome_options, executable_path=CHROMEDRIVER_PATH)
    except WebDriverException or FileNotFoundError:
        print("There is something wrong with your chromedriver installation")
        print(
            f"Run 'sh get_chromedriver.sh' in {os.getcwd()} to get the latest version")
        print("You can also run this command with the -u (--update-chromedriver) flag.")
        quit()

    driver.get(MATERIALS_URL)

    print("authenticating...")
    authenticate(driver)

    ############################# DOWNLOADING #############################
    base_dir = "./downloads"
    try:
        os.makedirs(base_dir)
    except Exception:
        pass

    if args.quick:
        download_course(driver, args.quick, base_dir=base_dir, verbose=verbose)
    else:
        download_courses(driver, base_dir=base_dir, verbose=verbose)
    driver.quit()
    print("Finishing...")

    ############################# CLEAN UP #############################
    for parent, dirnames, filenames in os.walk(base_dir):
        for fn in filenames:
            if fn.lower().endswith('.crdownload'):
                os.remove(os.path.join(parent, fn))

    # Moving the dowloads to the specified directory
    save_dir = DIRECTORY
    if args.location is not None:
        save_dir = args.location

    copy_tree(base_dir, save_dir)
    remove_tree(base_dir)
    print("DONE!!!")
