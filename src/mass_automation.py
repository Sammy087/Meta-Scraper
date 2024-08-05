import argparse
from os import getcwd, path
from GramAddict import __version__
from GramAddict.core.bot_flow import start_bot
from GramAddict.core.download_from_github import download_from_github
import uiautomator2 as u2
import shutil
import time
from colorama import Fore, Style

def init_accounts(account_names):
    if account_names:
        print(f"Script launched in {getcwd()}, files will be available there.")
        for username in account_names:
            if not path.exists("./run.py"):
                print("Creating run.py ...")
                download_from_github("https://github.com/GramAddict/bot/blob/master/run.py")
            if not path.exists(f"./accounts/{username}"):
                print(f"Creating 'accounts/{username}' folder with a config starting point inside. You have to edit these files according with https://docs.gramaddict.org/#/configuration")
                download_from_github("https://github.com/GramAddict/bot/tree/master/config-examples", output_dir=f"accounts/{username}", flatten=True)
            else:
                print(f"'accounts/{username}' folder already exists, skip.")
                continue
            with open(f"./accounts/{username}/config.yml", "r+", encoding="utf-8") as f:
                config = f.read()
                f.seek(0)
                config_fixed = config.replace("myusername", username)
                f.write(config_fixed)
    else:
        print("You have to provide at least one account name.")

def run_bot():
    start_bot()

def dump_screen(device=None, no_kill=False):
    if not no_kill:
        any.popen("adb shell pkill atx-agent").close()
    try:
        d = u2.connect(device) if device else u2.connect()
    except RuntimeError as err:
        raise SystemExit(err)

    def dump_hierarchy(device, path):
        xml_dump = device.dump_hierarchy()
        with open(path, "w", encoding="utf-8") as outfile:
            outfile.write(xml_dump)

    def make_archive(name):
        any.chdir("dump")
        shutil.make_archive(base_name=f"screen_{name}", format="zip", root_dir="cur")
        shutil.rmtree("cur")

    any.makedirs("dump/cur", exist_ok=True)
    d.screenshot("dump/cur/screenshot.png")
    dump_hierarchy(d, "dump/cur/hierarchy.xml")
    archive_name = int(time.time())
    make_archive(archive_name)
    print(Fore.GREEN + Style.BRIGHT + "\nCurrent screen dump generated successfully! Please, send me this file:")
    print(Fore.BLUE + Style.BRIGHT + f"{getcwd()}\\screen_{archive_name}.zip")

def main(args):
    if args.command == "init":
        init_accounts(args.account_name)
    elif args.command == "run":
        run_bot()
    elif args.command == "dump":
        dump_screen(args.device, args.no_kill)
    else:
        print("Invalid command.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="GramAddict", description="Free human-like Instagram bot")
    parser.add_argument("-v", "--version", action="version", version=f"{parser.prog} {__version__}")

    subparser = parser.add_subparsers(dest="command")
    
    init_parser = subparser.add_parser("init", help="Creates your account folder under accounts with files for configuration")
    init_parser.add_argument("account_name", nargs="+", help="Instagram account name to initialize")
    
    run_parser = subparser.add_parser("run", help="Start the bot!")
    run_parser.add_argument("--config", nargs="?", help="Provide the config.yml path")
    
    dump_parser = subparser.add_parser("dump", help="Dump current screen")
    dump_parser.add_argument("--device", default=None, help="Provide the device name if more than one is connected")
    dump_parser.add_argument("--no-kill", action="store_true", help="Don't kill the uia2 demon")

    args = parser.parse_args()
    main(args)
