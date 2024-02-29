import importlib
import os, sys, json, traceback, argparse
from colorama import Fore, init as coloramainit
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from cardboard import Cardboard
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from snowflake import SnowflakeGenerator
import uvicorn

parser = argparse.ArgumentParser()
parser.add_argument('-d ', "--debug",action='store_true')
args = parser.parse_args()
class INFO:
    """Info on the API maybe will be used at some point?"""
    NAME="Scheduler API"
    VERSION="v0.0.1"
    if args.debug:
        CONFIG_PATH="./configs/debug/"
    else:
        CONFIG_PATH="./configs/prod-main/"

class CONFIGS:
    """
    Entirity of the configs
    """
    DATE_FORMAT = "%A, %d/%B/%Y at %I:%M %p %Z GMT"

    # open config for data
    with open(f'{INFO.CONFIG_PATH}config.json', 'r') as config:
        CONFIG_DATA = json.load(config)
        config.close()

    DATABASE_CONNECTION_URL = CONFIG_DATA['database']

    API_PORT = CONFIG_DATA['APIport']
    BASE_URL = CONFIG_DATA['BaseURL'] #Used for things that require a baseURL 

if not "routes" in os.listdir():
    os.mkdir("routes")

def loadRoutes(folder, cleanup:bool=True):
    global app
    """Load Routes from the routes directory."""
    for root, dirs, files in os.walk(folder, topdown=False):
        for file in files:
            if not "__pycache__" in root:
                route_name = os.path.join(root, file).removesuffix(".py").replace("\\", "/").replace("/", ".")
                route_version = route_name.split(".")[0]
                if route_name.endswith("index"):
                    route = importlib.import_module(route_name)
                    if route.donotload:
                        continue
                    route_name = route_name.split(".")
                    del route_name[-1]
                    del route_name[0]
                    route_name = ".".join(route_name)
                    route.router.prefix = "/"+route_name.replace(".", "/")
                    route.router.tags = route.router.tags + [route_version] if isinstance(route.router.tags, list) else [route_version]
                    route.setup()
                    app.include_router(route.router)
                    print(Fore.CYAN + "routes."+route_name)
                else:
                    route = importlib.import_module(route_name)
                    if route.donotload:
                        continue
                    route_name = route_name.split(".")
                    del route_name[0]
                    route_name = ".".join(route_name)
                    route.router.prefix = "/"+route_name.replace(".", "/")
                    route.router.tags = route.router.tags + [route_version] if isinstance(route.router.tags, list) else [route_version]
                    route.setup()
                    app.include_router(route.router)
                    print(Fore.CYAN + "routes."+route_name)
    if cleanup:
        print(Fore.GREEN + "Cleaning __pycache__ up!")
        for root, dirs, files in os.walk(folder, topdown=False):
            if "__pycache__" in dirs:
                pycache_dir = os.path.join(root, "__pycache__")
                print(Fore.YELLOW + f"Deleting: {pycache_dir}")
                try:
                    # Remove the directory and its contents
                    for item in os.listdir(pycache_dir):
                        item_path = os.path.join(pycache_dir, item)
                        if os.path.isfile(item_path):
                            os.unlink(item_path)
                        else:
                            os.rmdir(item_path)
                    os.rmdir(pycache_dir)
                except Exception as e:
                    print(f"Error deleting {pycache_dir}: {e}")


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
app.add_middleware(SessionMiddleware, secret_key="your_secret_key")
cardboard = Cardboard(client_id=CONFIGS.CARDBOARD_CLIENT_ID, secret=CONFIGS.CARDBOARD_SECRET)

async def startup_event():
    coloramainit(autoreset=True)
    if args.debug:
        print(Fore.RED + "Debug Mode Enabled")
    if len(os.listdir("routes")) == 0:
        print(Fore.RED + "No routes loaded")
        sys.exit()
    print(Fore.BLUE + "Routes Loading...")
    loadRoutes("routes")
    print(Fore.GREEN + "Routes Loaded!")

app.add_event_handler("startup", startup_event)

if __name__ == "__main__":
    #TODO Be able to define host
    #TODO Be able to use debug mode

    # Useless code (pack/unpack check), for real. DO NOT TOUCH.

    # Run the app
    uvicorn.run("app:app", port=CONFIGS.API_PORT)