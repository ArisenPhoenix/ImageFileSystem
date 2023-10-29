import os
import itertools
import json


class GetImages:
    """
        Pulls A List Of Images Based On The Categories Provided In The 'get' Method.
        This Was Made To Work With The Image Categorizer So That The Categorized Images Could Be Pulled By Simply
        Providing A List Of The Categories and Sub-Categories. It Will Be A 1D List.
        Any Files Within The Directories That Fall Within The Categories Will Be Pulled Into A List In Alphabetical
        Order In The Order They Are Pulled Using 'os.walk'.
    """
    files = []
    FINAL_LiST_OF_CATEGORIES_TO_MATCH_AGAINST = None
    FILES_DICT = {}
    FINAL_DICT = {}
    IS_SEARCHING = True
    SINGLE_CATEGORY_TO_MATCH_AGAINST = None
    LIST_OF_CATEGORIES_TO_MATCH_AGAINST = None

    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.walker = os.walk(self.root_dir)
        self.current_group_name = None
        self.current_group_json_path = None
        self.current_group_path = None
        self.current_group_files = None

    def cleanup(self):
        self.LIST_OF_CATEGORIES_TO_MATCH_AGAINST = None
        self.current_group_name = None
        self.current_group_path = None
        self.current_group_files = None
        self.current_group_json_path = None
        self.walker = os.walk(self.root_dir)
        self.FINAL_LiST_OF_CATEGORIES_TO_MATCH_AGAINST = None
        self.IS_SEARCHING = True
        self.SINGLE_CATEGORY_TO_MATCH_AGAINST = None
        self.LIST_OF_CATEGORIES_TO_MATCH_AGAINST = None


    def get(self, categories: list[str]):
        if categories is None:
            self.get_all()
        elif isinstance(categories, str):
            self.SINGLE_CATEGORY_TO_MATCH_AGAINST = categories
            self.get_one()
            return self.FILES_DICT
        elif isinstance(categories, list):
            self.LIST_OF_CATEGORIES_TO_MATCH_AGAINST = categories
            self.create_list_of_categories_to_match_against()
            self.get_selected()
            return self.FILES_DICT
        else:
            raise ValueError(f"You Supplied {categories} for 'categories', "
                             f"'categories' must be None, type dict or type str")

    def next_step(self):
        try:
            self.current_group_path, _, self.current_group_files = next(self.walker)
            if "meta.json" in self.current_group_files:
                self.current_group_name = os.path.split(self.current_group_path)[-1]
                self.current_group_json_path = os.path.join(self.current_group_path, "meta.json")
                return True
            else:
                return False
        except StopIteration:
            print("Compilation Of Images Complete")
            return None

    def create_list_of_categories_to_match_against(self):
        final = itertools.product(*self.LIST_OF_CATEGORIES_TO_MATCH_AGAINST)
        final = [x for x in final]
        self.FINAL_LiST_OF_CATEGORIES_TO_MATCH_AGAINST = final

    def get_all(self):
        self.traverse_all()
        self.cleanup()

    def get_one(self):
        self.traverse_for_single_category()
        self.cleanup()

    def get_selected(self):
        self.traverse_for_selected_categories()
        # print(self.LIST_OF_CATEGORIES_TO_MATCH_AGAINST)
        self.cleanup()



    def gather_images_from_dir(self):
        temp_list = [os.path.join(self.current_group_path, image_file) for
                     image_file in os.listdir(self.current_group_path) if image_file != "meta.json"]
        return temp_list


    @staticmethod
    def create_nested_dict(list_items: list, file_names: list):
        tree_dict = {}
        for index, key in enumerate(reversed(list_items)):
            if index == 0:
                tree_dict = {key: file_names}
            else:
                tree_dict = {key: tree_dict}
        return tree_dict

    def traverse_all(self):
        #     Means Get All Images
        while self.IS_SEARCHING:
            searching = self.next_step()
            if searching:
                with open(self.current_group_json_path, "r+") as json_file:
                    data = json.load(json_file)
                categories = data["Categories"]
                if not self.FILES_DICT.get(categories["1"]):
                    self.FILES_DICT[categories["1"]] = []
                for image_file in self.gather_images_from_dir():
                    self.FILES_DICT[categories["1"]].append(image_file)
            elif searching is None:
                self.IS_SEARCHING = False
                break
            else:
                continue


    def check_for_match_between_category_matrix_and_categories(self, json_categories: dict):
        json_values = json_categories.values()
        for categories in self.FINAL_LiST_OF_CATEGORIES_TO_MATCH_AGAINST:
            count = 0
            for category in categories:
                if category in json_values:
                    count += 1
                    if count == len(json_values):
                        return True
        return False

    def traverse_for_single_category(self):
        while self.IS_SEARCHING:
            searching = self.next_step()
            if searching:
                with open(self.current_group_json_path, "r+") as json_file:
                    data = json.load(json_file)
                categories = data["Categories"]
                if self.SINGLE_CATEGORY_TO_MATCH_AGAINST in categories.values():
                    if not self.FILES_DICT.get(self.SINGLE_CATEGORY_TO_MATCH_AGAINST):
                        self.FILES_DICT[self.SINGLE_CATEGORY_TO_MATCH_AGAINST] = []
                    for image_file in self.gather_images_from_dir():
                        self.FILES_DICT[self.SINGLE_CATEGORY_TO_MATCH_AGAINST].append(image_file)
            elif searching is None:
                self.IS_SEARCHING = False
                break
            else:
                continue

    def traverse_for_selected_categories(self):
        while self.IS_SEARCHING:
            searching = self.next_step()
            if searching:
                with open(self.current_group_json_path, "r+") as json_file:
                    data = json.load(json_file)
                categories = data["Categories"]
                if self.check_for_match_between_category_matrix_and_categories(categories):
                    if not self.FILES_DICT.get(categories["1"]):
                        self.FILES_DICT[categories["1"]] = []
                    for image_file in self.gather_images_from_dir():
                        self.FILES_DICT[categories["1"]].append(image_file)
            elif searching is None:
                self.IS_SEARCHING = False
                break
            else:
                continue






if __name__ == "__main__":
    my_list = ["Trans", "Hispanic", "Jeune", "Nude", "Poly"]