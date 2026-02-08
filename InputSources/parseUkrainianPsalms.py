from bs4 import BeautifulSoup
from .parseBible import ParseBible

FILE_PATH = "/Users/kenfasano/Scripts/ScreenArt/InputSources/Data/UkrainianPsalms"
PSALM_NAME = "Псалмів"
ENCODING = "windows-1251"

class ParseUkrainianPsalms(ParseBible):
    def __init__(self):
        super().__init__(FILE_PATH, PSALM_NAME, ENCODING)

    def parse(self, content: str, chapter: int) -> list[str]:
        # Use BeautifulSoup to parse the content. Try UTF-8 first.
        soup = BeautifulSoup(content, 'lxml')

        # List to hold all extracted Psalm text parts
        results: list[str] = []

        # 1. Find all <td> tags (Table Data cells)
        # This is a good starting point to isolate the main content table
        td_elements = soup.find_all('td')

        for td in td_elements:
            # 2. Find all <p> tags nested within the current <td>
            p_elements = td.find_all('p')

            for p in p_elements:
                # 3. Extract the clean text from each <p> tag
                # strip=True removes leading/trailing whitespace from the text content
                text = p.get_text(strip=True)

                # 4. Filter out any likely blank results
                if text:
                    # Append the cleaned text. Double newlines will be used later for separation.
                    text = text.strip()
                    text = text.replace("¶ ", "").replace("%", "")
                    results.append(text)

        return results

if __name__ == '__main__':
    print("Starting main execution.") # <-- NEW PRINT
    ParseUkrainianPsalms().run(book="psalm", num_chapters=150)
    print("Finished main execution.") # <-- NEW PRINT
