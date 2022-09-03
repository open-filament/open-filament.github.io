import glob
from src.content.content_builder import ContentBuilder

DATA_DIR = "data/"
DATABASE_DIR = "databases/"
CONTENT_DIR_PRODUCERS = "content/producers/"


def build_content():
    cb = ContentBuilder()
    cb.load_producers_data(DATABASE_DIR + "producers.json")

    data_files = glob.glob(DATA_DIR+"*")
    for data_file in data_files:
        cb.load_producer(data_file)

    cb.generate_uuids()
    cb.generate_content(CONTENT_DIR_PRODUCERS)
    cb.save_producers_data(DATABASE_DIR + "producers.json")


if __name__ == "__main__":
    build_content()
