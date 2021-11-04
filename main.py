from time import sleep
from json import *
from requests import get
from colorama import Fore, init
from ctypes import windll
from datetime import datetime
from re import findall
from uuid import uuid4
from hashlib import sha1
import threading

def output(content):
    print("{c_red}{time} {c_white}| {content}".format(c_red=Fore.RED, time=datetime.now().strftime("%X"), c_white=Fore.WHITE, content=content))

class Database:
    def __init__(self, search_data, proxy=False):
        self.possible_args = ["fname", "lname", "mname", "age", "city", "state", "page"]
        self.accepted_query = {k:v for k,v in search_data.items() if k in self.possible_args}
        self.provided_query = search_data
        self.collection = []
    
    def get_page_count(self):
        return len(findall("&page=[\d]*", get("https://publicrecords.searchsystems.net/search-result.php", params=self.accepted_query).text))

    def get_data_from_html(self, content):
        scraped_data = []
        html_groups = content.split("<td scope=\"row\"")

        for section in html_groups[1:]:
            name = findall("sub3=\">[\w -]*<", section)[0][7:-1]
            age = findall("\"Age\"><div>[\d]*", section)[0][11:]
            lived_in = [location[1:-1] for location in findall(">[\w, ]+<", findall("\"Has Lived In\"><div><strong>.*</td>", section)[0][27:])]
            relatives = [relative[10:-1] for relative in findall("submit=1\">[\w ]*<", section)]
            scraped_data.append({"name": name, "age": age, "lived_in": lived_in, "relatives": relatives})
        
        return scraped_data

    def add_data(self, data):
        for k in data:
            self.collection.append(k)

    def handle_request(self, page=False):
        new_args = {k:v for (k,v) in self.accepted_query.items()}

        if page:
            new_args.update({"page": page})

        self.add_data(
            self.get_data_from_html(get("https://publicrecords.searchsystems.net/search-result.php", params=new_args).text)
        )
        
    def get(self):
        self.page_count = self.get_page_count()
        self.page_count = self.page_count == 0 and 1 or self.page_count

        for page in range(self.page_count + 1):
            threading.Thread(target=self.handle_request, args=(page, )).start()

        while threading.active_count() != 1:
            pass

        return self.collection


class USLookup:
    def __init__(self, config):
        self.target = {}
        self.config = config

        print(Fore.WHITE)

        self.target.update({"fname": input(f"  [?] Firstname: ")})
        self.target.update({"lname": input(f"  [?] Lastname: ")})
        self.target.update({"state": input(f"  [?] State [\"PA\", \"NY\" etc.]: ")})

        db = Database(self.target)
        response = db.get()

        print("\n")
        output(f"{Fore.GREEN}Fetched {Fore.MAGENTA}{len(response)}{Fore.GREEN} results.")
        
        output_type = input("Output Method [csv, json or console]: ").strip().lower()
        target_fname, target_lname = self.target.get("fname"), self.target.get("lname")
        output_file = None

        if output_type == "json":
            with open(f"output/{target_fname}-{target_lname}-{str(uuid4())[0:9]}.json", "a") as json_file:
                output_file = json_file
                json_file.write(dumps(response, indent=4))
                json_file.close()
                output(f"{Fore.GREEN}Successfully saved to {Fore.MAGENTA}{output_file.name}{Fore.WHITE}")

        elif output_type == "console":
            for result in response:
                for k, v in result.items():
                    print(f"{Fore.YELLOW}{k}{Fore.WHITE}: {v}")
                print("\n")

if __name__ == "__main__":
    with open("config.json") as json_file:
        config = load(json_file)
        init()
        windll.kernel32.SetConsoleTitleW("{name} v{version} | {credits}".format(name=config["name"], version=config["version"], credits=config["credits"]["developer"]))
        
        with open("text/welcome", "r", encoding="utf-8") as skull:
            print("\n")
            for line in skull.readlines():
                print(Fore.GREEN + line.rstrip())
                sleep(.1)
            print("\n")
            
        #input("")
        output(f"{Fore.YELLOW}Configuring USL...")
        sleep(.2)
        output(f"{Fore.GREEN}Client authenticated {Fore.WHITE}| {Fore.RED}SESSION_HASH: {sha1().hexdigest()}")

        while 1:
            lookup_handle = USLookup(config)
            sleep(2)


