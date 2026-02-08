import re
from .parseBible import ParseBible
from bs4 import BeautifulSoup

FILE_PATH = "/Users/kenfasano/Scripts/ScreenArt/InputSources/Data/HebrewPsalms"
PSALM_NAME = "תְּהִלִּים"

class ParseHebrewPsalms(ParseBible):
    def __init__(self):
       super().__init__(FILE_PATH, PSALM_NAME)

    def parse(self, content: str, chapter: int) -> list[str]:
        soup = BeautifulSoup(content, 'lxml')
        psalm_id_pattern = re.compile(rf'^BHS\.PSA\.{chapter}\.\d+$')
        id_tags = soup.find_all(attrs={'id': psalm_id_pattern})
        results: list[str] = []

        for tag in id_tags:
            hebrew_span = tag.find('span')
            if hebrew_span:
                hebrew_text = hebrew_span.get_text(strip=True)
                results.append(hebrew_text)

        return results

if __name__ == '__main__':
    print("Starting main execution.") # <-- NEW PRINT
    ParseHebrewPsalms().run(book="psalm", num_chapters=150)
    print("Finished main execution.") # <-- NEW PRINT
