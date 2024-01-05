from shutil import copytree, ignore_patterns, rmtree
import tomlkit as tk
import requests, os, wget, patoolib
from termcolor import colored

temp_file_location = ".\\temp_files"

# Add patoolib.programs and patoolib.programs.p7zip as hidden imports or it will break!!!

def update_the_app():
    if not os.path.exists(f"{temp_file_location}"):
        print('[Update process] Creating a temp folder...')
        os.mkdir(temp_file_location)

    print('[Update process] Downloading new release...')
    wget.download(responce.json()["assets"][0]["browser_download_url"], f"{temp_file_location}\\temp_ver.7z")
    extract_and_replace()

def extract_and_replace():
    rmtree(f"{temp_file_location}\\unpacked", ignore_errors=True)
    patoolib.extract_archive(f"{temp_file_location}\\temp_ver.7z", outdir=f"{temp_file_location}\\unpacked\\")
    copytree(f"{temp_file_location}\\unpacked\\", ".\\", ignore=ignore_patterns("config.toml", "Updater.exe"), dirs_exist_ok=True)
    rmtree(f"{temp_file_location}")
    print(colored('Update successful!', 'green'))
    print(colored('Do not forget to launch the app to update version information!', 'yellow'))
    os.system('pause')

os.system('cls')
print('=# ' + colored('SN_Straitjacket ', 'magenta') + colored('Updater ', 'green') + "#=")

try:
    with open('config.toml', 'r') as configFile:
        config = tk.load(configFile)

    if 'app_version' in config['BASE']:
        print('Current app version: ' + colored(f'{config["BASE"]["app_version"]}', 'yellow'))
    else:
        print('Current app version: ' + colored(f'Base release', 'red'))

    print('Checking for new releases...')
    responce = requests.get("https://api.github.com/repos/SNeicer/SN_Straitjacket/releases/latest")

    if not ('app_version' in config['BASE']) or config['BASE']['app_version'] != responce.json()["tag_name"]:
        print(colored('Version status: ', 'yellow') + colored('Outdated!', 'red'))
        do_update = input('Update the app? [Y / N] ')
        while True:
            if do_update == 'Y' or do_update == 'y':
                print(colored('Installing an update...', 'green'))
                update_the_app()
                break
            elif do_update == 'N' or do_update == 'n':
                print(colored('Update canceled', 'red'))
                os.system('pause')
                break
            else:
                print('Incorrect responce!')
                do_update = input('Update the app? [Y / N] ')
    else:
        print(colored('Version status: ', 'yellow') + colored('Up-to-date!', 'green'))
        os.system('pause')
except FileNotFoundError:
        print(colored('App config file not found! ', 'red') + colored('Please, launch the app at least once!', 'yellow'))
        os.system('pause')