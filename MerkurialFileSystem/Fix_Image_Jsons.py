import json
import os
import imghdr
from natsort import natsorted
import urllib.request
from datetime import datetime
from urllib.error import URLError
from time import sleep
from http.client import RemoteDisconnected
from Merkurial_ImageSifter.images_viewer_helpers import ImageViewerFileHandler
from ImageDownloader.image_group import ImageGroup


class FixImageJsons:
    """
        The FixImageJsons Class Was Made When I Made A Mistake And Needed To Update All The Information In The Image
        Groups. Instead Of Going Through About 3000 Directories, I Wrote This Script To Get The Job Done For Me.
    """
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.walker = os.walk(self.root_dir)
        self.traversing = True
        self.updated_file_path = os.path.join(self.root_dir, "updated.json")
        self.current_group_path = ""
        self.current_group_files = []
        self.files = ImageViewerFileHandler()
        self.items = []



    def next_step(self):
        try:
            self.current_group_path, _, self.current_group_files = next(self.walker)
            if len(self.current_group_files) > 4:
                return True
            else:
                return False
        except StopIteration:
            print("All Images Have Been Updated.")
            return exit(0)


    def traverse(self):
        full_counter = 0
        counter = 0
        while self.traversing:
            full_counter += 1
            if self.next_step():
                counter += 1
                # print(f"Groups Checked: {counter}")
                match = self.files.check_for_matching_file(self.current_group_path, self.updated_file_path)
                if not match:
                    fix = FixImageJson(self.current_group_path, self.current_group_files)
                    items_were_fixed = fix.fix()
                    if items_were_fixed:
                        print("Item Number: ", counter)
                        print(f"Fixed: {self.current_group_path}")
                    if items_were_fixed is None:
                        print("Item Number: ", counter)
                        print(f"Web Address For:\n{self.current_group_path}")
                        print("Was Either Removed Or Down")
                    self.files.add_updated_item_to_file(self.updated_file_path, self.current_group_path)
                continue


class FixImageJson:
    def __init__(self, group_path: str, current_group_files: list):
        self.group_path = group_path
        self.json_path = os.path.join(self.group_path, "meta.json")
        self.current_group_files = current_group_files

        self.json_data = {}
        self.json_image_group_links = {}
        self.json_image_group_title = ""
        self.json_image_categories = {}
        self.json_image_group_link = ""
        self.json_image_group_directory = ""
        self.json_image_saved_count = 0

        self.current_image_name_number = 0

        self.images = []
        self.dir_image_names = []
        self.dir_image_name_nums = []
        self.dir_image_name_dict = {}
        self.num_images = 0

        self.web_found_image_links = []
        self.web_link_dict = {}

        self.image_path = ""
        self.image_url = ""
        self.image_number = None

        self.updated_link_dict = {}

        self.get_image_group_data_from_json_file()
        self.get_images_from_group_dir()


    def get_image_group_data_from_json_file(self):
        with open(self.json_path, "r+") as json_file:
            self.json_data = json.load(json_file)

        self.json_image_group_title = self.json_data["Title"]
        self.json_image_categories = self.json_data["Categories"]
        self.json_image_group_link = self.json_data["Group Link"]
        self.json_image_group_directory = self.json_data["Directory"]
        self.json_image_group_links = self.json_data["Images"]
        self.json_image_saved_count = len(self.json_image_group_links)

    def create_dir_image_name_dict(self):
        for dir_img in self.dir_image_names:
            dir_img_num = dir_img.split("_")[-1]
            self.dir_image_name_dict[dir_img_num] = dir_img

    def get_images_from_group_dir(self):
        self.images = [os.path.join(self.group_path, img) for img in self.current_group_files
                       if imghdr.what(os.path.join(self.group_path, img))]
        self.images = natsorted(self.images)
        self.dir_image_names = [os.path.split(img)[-1].split(".")[0] for img in self.images]
        self.dir_image_name_nums = [img.split("_")[-1] for img in self.dir_image_names]
        self.create_dir_image_name_dict()
        self.num_images = len(self.images)

    def get_links(self):
        image_group = ImageGroup(self.json_image_group_link, self.json_image_group_title)
        image_group_links = image_group.get_second_level_images()
        if image_group_links:
            self.web_found_image_links = [img["href"] for img in image_group_links]
            for num, link in enumerate(self.web_found_image_links):
                self.web_link_dict[str(num + 1)] = link
            return True
        return False


    def fix_images(self):
        num_dir_images = len([num for num in self.dir_image_name_dict.keys()])
        num_json_images = len([num for num in self.json_image_group_links])
        if num_dir_images == num_json_images:
            return False
        elif len([num for num in self.web_link_dict.keys()]) == num_dir_images:
            return False
        else:
            has_links = self.get_links()
            if not has_links:
                print("="*100)
                print("The Page Was Either Removed Or Down")
                print("=" * 100)
                return None
            else:
                for index, image_number in enumerate(self.web_link_dict.keys()):
                    dir_link_num = self.dir_image_name_dict.get(image_number)
                    if not dir_link_num:
                        self.image_number = image_number
                        this_filename = f"{self.json_image_group_title}_{self.image_number}"
                        self.image_path = os.path.join(self.group_path, this_filename)
                        self.image_url = self.web_link_dict[image_number]
                        self.download_missing_image()
                        self.dir_image_name_dict[image_number] = this_filename
                return True



    def fix(self):
        items_were_fixed = self.fix_images()
        if items_were_fixed:
            images = self.web_link_dict
        else:
            images = self.json_image_group_links
        new_json = {"Title": self.json_image_group_title,
                    "Categories": self.json_image_categories,
                    "Group Link": self.json_image_group_link,
                    "Directory": self.group_path,
                    "Images": images,
                    "Names": self.dir_image_name_dict}

        with open(self.json_path, "w+") as json_file:
            json.dump(new_json, json_file, indent=4)

        return items_were_fixed

    @staticmethod
    def rename_image(old_file_path):
        type_of_image = imghdr.what(old_file_path)
        if type_of_image:
            if type_of_image not in old_file_path:
                new_image_name = f"{old_file_path}.{type_of_image}"
                os.rename(old_file_path, new_image_name)

    def handle_not_save_error(self, image_path: str, error: str):
        date_and_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        log = f"""Image: {image_path}\nError: {error}\nPage Url: 
{self.json_image_group_link}\nImage Url:{self.image_url}\nTime: {date_and_time}\n\n"""

        with open(os.path.join(os.getcwd(), "../Data/logs/error_log"), "a+") as err_log:
            err_log.write(str(log))
        print(f"Connection Error: {image_path} Continues To Fail Moving On")

    def handle_save_success(self, group_txt_file: str):

        with open(group_txt_file, "r+", newline="\n") as group_file:
            json_data = json.load(group_file)
        json_data["Images"][self.image_number] = self.image_url

        with open(group_txt_file, "w+", encoding="utf-8") as group_file:
            json.dump(json_data, group_file, indent=4)

    def download_missing_image(self):
        count = 0
        going = True
        while going:
            try:
                (
                    save_path,
                    self.http_message,
                ) = urllib.request.urlretrieve(self.image_url, self.image_path)
                self.rename_image(self.image_path)

                return 1, 0, 1
            except URLError as error:
                count += 1
                if count == 10:
                    self.handle_not_save_error(self.image_path, str(error))
                    return 0, 1, 1
                else:
                    sleep(0.2)
                    continue
            except RemoteDisconnected as error:
                count += 1
                if count == 10:
                    self.handle_not_save_error(self.image_path, str(error))
                    return 0, 1, 1
                else:
                    sleep(0.2)
                    continue

            except FileNotFoundError as error:
                count += 1
                if count == 10:
                    self.handle_not_save_error(self.image_path, str(error))
                    return 0, 1, 1
                else:
                    sleep(0.2)
                    continue

            except ValueError as error:
                count += 1
                if count == 10:
                    self.handle_not_save_error(self.image_path, str(error))
                    return 0, 1, 1
                else:
                    sleep(0.2)
                    continue

            except BaseException as error:
                count += 1
                if count == 10:
                    self.handle_not_save_error(self.image_path, str(error))
                    return 0, 1, 1
                else:
                    sleep(0.2)
                    continue

    def check_json_file_images(self):
        json_file_image_data = self.json_data["Images"]
        json_file_image_numbers = [num for num in json_file_image_data.keys()]
        json_file_image_numbers.sort(key=int)
        image_names_nums = [img.split("_")[-1] for img in self.dir_image_names]

        for img_num in range(len(json_file_image_data)):
            if img_num in image_names_nums:
                print("True")
                # self.download_missing_image()
            else:
                print("False")
