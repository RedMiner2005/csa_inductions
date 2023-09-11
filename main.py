from PIL import Image
import pytesseract
import cv2
import csv
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from libgen_api import LibgenSearch
from urllib.request import urlretrieve


pytesseract.pytesseract.tesseract_cmd = r'<YOUR_TESSERACT_EXECUTABLE_LOCATION>'


def get_camera() -> Image:
    cam = cv2.VideoCapture(0)
    image = None

    while True:
        result, image = cam.read()
        if result:
            cv2.imshow("Camera", image)
            cv2.waitKey(0)
            cv2.destroyWindow("Camera")
            break

    color_coverted = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(color_coverted)

    return pil_image


def get_file(name: str) -> Image:
    return Image.open(name)


def extract_text(image: Image) -> str:
    try:
        return pytesseract.image_to_string(image, timeout=2)
    except RuntimeError as timeout_error:
        print("Error in OCR. Exiting.")
        exit()


def process_text(text: str) -> tuple:
    l = text.split("\n\n")
    if len(l) == 0:
        print("Error in extracting text - empty string. Exiting.")
        exit()
    if len(l) == 1:
        return text.replace("\n", " ")
    lens = list(map(lambda x: len(x), l))
    while 1 in lens:
        i = lens.index(1)
        l.pop(i)
        lens.pop(i)
    
    while len(l) > 2:
        i = lens.index(max(lens))
        l.pop(i)
        lens.pop(i)
    l = tuple(map(lambda x: x.replace("\n", " ").lower(), l))
    return l


def get_match(text_pair: tuple) -> tuple:
    best = ('', '', 0)
    with open("main_dataset.csv", "r", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if reader.line_num == 0:
                continue
            try:
                match = (
                    row[1],
                    row[2],
                    max(
                        fuzz.partial_ratio(text_pair[0].lower(), row[1].lower()) + fuzz.partial_ratio(text_pair[1].lower(), row[2].lower()),
                        fuzz.partial_ratio(text_pair[0].lower(), row[2].lower()) + fuzz.partial_ratio(text_pair[1].lower(), row[1].lower())
                    ) / 2
                )
            except:
                print("Empty string - Matching. Exiting.")
                exit()
            if match[2] > best[2]:
                best = match
    return best


def get_links(title: str, author: str):
    search = LibgenSearch()
    author_filters = {"Author": author}
    results = search.search_title(title)
    if len(results) == 0:
        print(f"No book found under the name: {title} by {author}")
        exit()
    download_links = search.resolve_download_links(results[0])
    return download_links


def download(filename: str, links: dict):
    for key in links:
        if key == "GET":
            continue
        try:
            extension = links[key].split(".")[-1]
            urlretrieve(links[key], filename + "." + extension)
            break
        except:
            continue
    else:
        print("Couldn't download file.")


def main():
    image = get_file("magician.jpg")
    extracted_text = extract_text(image)
    if extracted_text.strip == "":
        print("Error in extracting text - empty string. Exiting.")
        exit()
    print(extracted_text)
    processed = process_text(extracted_text)
    print(processed)
    match = get_match(processed)
    print(match)
    links = get_links(match[0], match[1])
    print(links)
    download(match[0].replace(" ", "_"), links)


if __name__ == "__main__":
    main()
