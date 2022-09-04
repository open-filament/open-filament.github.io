from __future__ import annotations
from src.qrcode.qrcode_generator import QrCodeGenerator
import multiprocessing as mp
import dataclasses
from subprocess import call
from uuid import uuid4
import json
import os
from dataclasses import dataclass
from typing import Optional
import yaml
import coloredlogs
import logging

# Create a logger object.
logger = logging.getLogger(__name__)

# By default the install() function installs a handler on the root logger,
# this means that log messages from your code and log messages from the
# libraries that you use will all show up on the terminal.
coloredlogs.install(level='DEBUG', logger=logger)

SCAD_BASEPLATE_PATH = "models/BasePlate.scad"


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        if type(o) is list:
            return [self.default(item) for item in o]
        return super().default(o)


@dataclass
class Filament:
    name: str
    data: dict[str, str] | None
    id: Optional[str] = None

    @staticmethod
    def from_json(d: dict) -> Filament:
        return Filament(d['name'], d['data'] if 'data' in d else None, d['id'])

    def update(self, updated_filament: Filament) -> None:
        self.name = updated_filament.name
        if updated_filament.id is not None:
            self.id = updated_filament.id
        if updated_filament.data is not None:
            self.data = updated_filament.data


@dataclass
class Material:
    name: str
    filaments: list[Filament]

    @staticmethod
    def from_json(d: dict) -> Material:
        return Material(d['name'], [Filament.from_json(m) for m in d['filaments']])

    def __filament_in_list(self, filamentname: str) -> bool:
        return any(filament.name == filamentname for filament in self.filaments)

    def __filament_index(self, filamentname: str) -> int:
        return next((i for i, filament in enumerate(self.filaments) if filament.name == filamentname), -1)

    def update(self, updated_material: Material) -> None:
        for updated_filament in updated_material.filaments:
            if not self.__filament_in_list(updated_filament.name):
                self.filaments.append(updated_filament)
            else:
                index = self.__filament_index(updated_filament.name)
                self.filaments[index].update(updated_filament)


@dataclass
class Producer:
    name: str
    materials: list[Material]

    @staticmethod
    def from_json(d: dict) -> Producer:
        return Producer(d['name'], [Material.from_json(m) for m in d['materials']])

    def __material_in_list(self, materialname: str) -> bool:
        return any(material.name == materialname for material in self.materials)

    def __material_index(self, materialname: str) -> int:
        return next((i for i, material in enumerate(self.materials) if material.name == materialname), -1)

    def update(self, updated_producer: Producer) -> None:
        for updated_material in updated_producer.materials:
            if not self.__material_in_list(updated_material.name):
                self.materials.append(updated_material)
            else:
                index = self.__material_index(updated_material.name)
                self.materials[index].update(updated_material)


def producer_from_yaml(filepath: str) -> Producer | None:
    with open(filepath, "r", encoding="utf-8") as stream:
        try:
            yaml_obj = yaml.safe_load(stream)
            logger.debug(yaml_obj)
            producer = producer_yaml_to_object(yaml_obj)
            return producer
        except yaml.YAMLError as exc:
            print(exc)


def producer_yaml_to_object(yaml_obj) -> Producer:
    materials: list[Material] = []
    yaml_materials = yaml_obj["producer"]["materials"]
    for yaml_material_name in yaml_materials:
        yaml_filaments = yaml_materials[yaml_material_name]["filaments"]
        filament_names = yaml_filaments.keys()
        print(filament_names)
        filaments = [Filament(filament_name, id=None, data=yaml_filaments[filament_name])
                     for filament_name in filament_names]
        materials.append(Material(yaml_material_name, filaments))

    return Producer(yaml_obj["producer"]["name"], materials)


def ensure_directory(path: str):
    if not os.path.exists(path):
        os.mkdir(path)


def clear_name(filename: str) -> str:
    filename = filename.lower()
    filename = filename.replace(" ", "-")
    filename = filename.replace("'", "")
    filename = filename.replace(".", "")
    while "--" in filename:
        filename = filename.replace("--", "-")
    return filename


def generate_filament_content(producer: Producer, material: Material, material_path: str, filament: Filament):
    filament_path = os.path.join(
        material_path, f"{clear_name(filament.name)}.md")
    __write_filament_file(
        filament_path, producer, material, filament)

    qrcg = QrCodeGenerator()
    url_to_page = f"https://open-filament.github.io/f/{filament.id}"
    filament_exportdir = os.path.join(
        material_path, clear_name(filament.name))
    qrcg.from_url_to_stl(url_to_page, filament_exportdir,
                         clear_name(filament.name), SCAD_BASEPLATE_PATH)


def __write_filament_file(filepath: str, producer: Producer, material: Material, filament: Filament):
    data = {
        "id": filament.id,
        "title": filament.name,
        "thumbnail": f"{clear_name(filament.name)}.png",
        "assets": [
            {"name": "STL model",
                "filename": f"{clear_name(filament.name)}.stl"},
            {"name": "QR-Code",
                "filename": f"{clear_name(filament.name)}.qrcode.png"},
            {"name": "OpenSCAD file",
                "filename": f"{clear_name(filament.name)}.scad"},
            {"name": "Preview", "filename": f"{clear_name(filament.name)}.png"}
        ],
        "data": filament.data,
        "aliases": [
            f"/f/{filament.id}"
        ],
        "material": material.name,
        "producer": producer.name,
        "type": "filament"
    }
    write_content_file(filepath, data, False)


def write_content_file(filepath: str, data: dict, skip_if_exists: bool = True):
    if os.path.exists(filepath) and skip_if_exists:
        return

    with open(filepath, "w+", encoding="utf-8") as stream:
        jsonstring = json.dumps(data)
        stream.write(jsonstring)


class ContentBuilder:

    producers: list[Producer]

    def __init__(self):
        self.producers = []

    def __producer_in_list(self, producername: str) -> bool:
        return any(producer.name == producername for producer in self.producers)

    def __producer_index(self, producername: str) -> int:
        return next((i for i, item in enumerate(self.producers) if item.name == producername), -1)

    def load_producer(self, filepath: str) -> None:
        """load producer from YAML file"""
        logger.info("Load producer from file '%s'", filepath)
        producer = producer_from_yaml(filepath)
        logger.debug(producer)
        if producer is not None:
            if not self.__producer_in_list(producer.name):
                self.producers.append(producer)
            else:
                index = self.__producer_index(producer.name)
                self.producers[index].update(producer)

            # statistics
            len_materials = len(producer.materials)
            len_filaments = sum([len(mat.filaments)
                                for mat in producer.materials])
            logger.info("Producer: %s - %d materials, %d filaments",
                        producer.name, len_materials, len_filaments)

    def save_producers_data(self, filepath: str):
        """save producers to JSON file"""
        jsonstring = json.dumps(
            self.producers, cls=EnhancedJSONEncoder, indent=4)
        with open(filepath, "w+", encoding="utf-8") as stream:
            stream.write(jsonstring)

    def load_producers_data(self, filepath: str):
        """load producers from JSON file"""
        with open(filepath, "r", encoding="utf-8") as stream:
            obj = json.load(stream)  # , object_hook=list[Producer.from_json]
            self.producers = [Producer.from_json(d) for d in obj]
            # print(self.producers)

    def generate_uuids(self):
        for producer in self.producers:
            for material in producer.materials:
                for filament in material.filaments:
                    if filament.id is None:
                        filament.id = str(uuid4())

    def generate_content(self, producers_basepath: str):
        """generate content files"""

        ensure_directory(producers_basepath)

        for producer in self.producers:
            self.__generate_procuder_content(
                producers_basepath, producer)

    def __generate_procuder_content(self, producers_basepath: str, producer: Producer):
        producer_path = os.path.join(
            producers_basepath, clear_name(producer.name))
        ensure_directory(producer_path)

        self.__generate_producer_index(producer, producer_path)

        for material in producer.materials:
            self.__generate_material_content(
                producer, producer_path, material)

    def __generate_material_content(self, producer: Producer, producer_path: str, material: Material):
        material_path = os.path.join(
            producer_path, clear_name(material.name))
        ensure_directory(material_path)

        self.__generate_material_index(
            producer, material, material_path)

        pool = mp.Pool(mp.cpu_count()-2)

        results = []

        def collect_result(result):
            results.append(result)

        for filament in material.filaments:
            pool.apply_async(generate_filament_content, args=(
                producer, material, material_path, filament), callback=collect_result)

        pool.close()
        pool.join()

    def __generate_producer_index(self, producer: Producer, producer_path: str):
        filepath = os.path.join(producer_path, "_index.md")
        title = producer.name
        data = {"title": title}
        write_content_file(filepath, data)

    def __generate_material_index(self, producer: Producer, material: Material, material_path: str):
        filepath = os.path.join(material_path, "_index.md")
        title = f"{producer.name} - {material.name}"
        data = {"title": title}
        write_content_file(filepath, data)
