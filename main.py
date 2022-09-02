from src.content.content_builder import ContentBuilder
from src.qrcode.qrcode_generator import QrCodeGenerator

DATA_DIR = "data/"
DATABASE_DIR = "databases/"
CONTENT_DIR_PRODUCERS = "content/producers/"


def build_qrcode():
    qrcg = QrCodeGenerator()
    qrcg.from_url_to_stl(
        "https://open-smartwatch.github.io/resources/firmware/#lang_stw_start-was-not-declared-in-this-scope",
        "D:\\Github_repos\\open-filaments\\content\\producers\\Prusament\\PETG\\Jet Black",
        "02_b3436596-7504-4bfe-8dc3-6b0d4090651a"
    )


def build_content():
    cb = ContentBuilder()
    cb.load_producers_data(DATABASE_DIR + "producers.json")
    cb.load_producer(DATA_DIR + "prusament.yml")
    cb.load_producer(DATA_DIR + "esun.yml")

    cb.generate_uuids()
    cb.generate_content(CONTENT_DIR_PRODUCERS)
    cb.save_producers_data(DATABASE_DIR + "producers.json")


if __name__ == "__main__":
    build_qrcode()
    # build_content()
