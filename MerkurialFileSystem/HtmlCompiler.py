import os
from ImageDownloader.image_downloader import ImagePuller


class HtmlCompiler:
    """
        The Root Dir In This Case Is A Directory Containing HTML Files With Similar Contents In Them.
        This One Will Place All HTMLS Matching The List Of Strings Provided Into One HTML File Leaving The Rest Alone.
        It Will Not Remove Any Files, That Will Have To Be Done Manually.

    """
    def __init__(self, root_dir: str):
        self.root_dir = root_dir


    @staticmethod
    def append_anywhere(filename: str, list_of_strings: list[dict]) -> bool:
        try:
            with open(filename, "a+") as html_file:
                for a in list_of_strings:
                    a_html = f"<a href={a['href']}>{a['title']}</a>"
                    html_file.write(a_html+"\n")
            return True
        except FileNotFoundError:
            return False

    def compile_htmls(self, category_schema: dict, new_html_name_beginner: str | None = None) -> list[str]:
        """
        :returns list[str] : str = html file path/name
        :param category_schema: a simple dictionary with categories as keys and a list of keywords for it as values.
        :param new_html_name_beginner: This is what will preface the newly created html files - Default "ALL_"
        :return list[str]: list of html file names
        """
        list_of_htmls = []
        total_as = 0
        separating_path_name = "ALL_" if new_html_name_beginner is None else new_html_name_beginner

        for html in os.listdir():
            if separating_path_name not in html:
                html_file = os.path.join(self.root_dir, html)
                imager = ImagePuller(html_file)
                all_as = imager.remove_duplicate_links()
                total_as += len(all_as)
                if ".html" in html.lower():
                    for category in category_schema.keys():
                        keywords = category_schema[category]
                        for keyword in keywords:
                            if keyword.lower() in html.lower():
                                new_file = f"{self.root_dir}/{separating_path_name}{category}.html"
                                ok = self.append_anywhere(new_file, all_as)
                                if ok:
                                    continue
                                else:
                                    ok = self.append_anywhere(new_file, all_as)
                                    if ok:
                                        list_of_htmls.append(new_file)
                                    else:
                                        print(f"Adding As To: {new_file} Failed Moving On.")

        for html in os.listdir():
            file_loc = os.path.join(self.root_dir, html)
            if separating_path_name in html:
                with open(file_loc, "r+") as file:
                    lines = file.readlines()
                    print()
                    print(f"There Are {len(lines)} In {html}")
                if lines is not None:
                    with open(file_loc, "w+") as file:
                        lines = list(set(lines))
                        lines.sort()
                        print(f"There Are Now {len(lines)} In {html}")
                        for line in lines:
                            file.write(line)

        return list_of_htmls
