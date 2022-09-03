from __future__ import annotations
import dataclasses
from uuid import uuid4
import json
import os
from dataclasses import dataclass
from typing import Optional
import yaml

from src.qrcode.qrcode_generator import QrCodeGenerator


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


@dataclass
class Filament:
    name: str
    id: Optional[str] = None

    @staticmethod
    def from_json(d: dict) -> Filament:
        return Filament(d['name'], d['id'])


@dataclass
class Material:
    name: str
    filaments: list[Filament]

    @staticmethod
    def from_json(d: dict) -> Material:
        return Material(d['name'], [Filament.from_json(m) for m in d['filaments']])


@dataclass
class Producer:
    name: str
    materials: list[Material]

    @staticmethod
    def from_json(d: dict) -> Producer:
        return Producer(d['name'], [Material.from_json(m) for m in d['materials']])


def producer_from_yaml(filepath: str):
    with open(filepath, "r", encoding="utf-8") as stream:
        try:
            yaml_obj = yaml.safe_load(stream)
            producer = producer_yaml_to_object(yaml_obj)
            return producer
        except yaml.YAMLError as exc:
            print(exc)


def producer_yaml_to_object(yaml_obj) -> Producer:
    materials: list[Material] = []
    yaml_materials = yaml_obj["producer"]["materials"]
    for yaml_material_name in yaml_materials:
        yaml_filaments = yaml_materials[yaml_material_name]
        filaments = [Filament(filament_name)
                     for filament_name in yaml_filaments]
        materials.append(Material(yaml_material_name, filaments))

    return Producer(yaml_obj["producer"]["name"], materials)


def ensure_directory(path: str):
    if not os.path.exists(path):
        os.mkdir(path)


def clear_name(filename: str) -> str:
    filename = filename.lower()
    filename = filename.replace(" ", "-")
    while "--" in filename:
        filename = filename.replace("--", "-")
    return filename


class ContentBuilder:

    producers: list[Producer]

    def __init__(self):
        self.producers = []

    def __producer_in_list(self, producername: str) -> bool:
        return any(producer.name == producername for producer in self.producers)

    def load_producer(self, filepath: str) -> None:
        """load producer from YAML file"""
        producer = producer_from_yaml(filepath)
        if producer is not None:
            if not self.__producer_in_list(producer.name):
                self.producers.append(producer)

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
            print(self.producers)

    def generate_uuids(self):
        for producer in self.producers:
            for material in producer.materials:
                for filament in material.filaments:
                    if filament.id is None:
                        filament.id = str(uuid4())

    def generate_content(self, producers_basepath: str):
        """generate content files"""

        if not os.path.exists(producers_basepath):
            os.mkdir(producers_basepath)

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

        for filament in material.filaments:
            self.__generate_filament_content(
                producer, material, material_path, filament)

    def __generate_filament_content(self, producer: Producer, material: Material, material_path: str, filament: Filament):
        filament_path = os.path.join(
            material_path, f"{clear_name(filament.name)}.md")
        self.__write_filament_file(
            filament_path, producer, material, filament)

        qrcg = QrCodeGenerator()
        url_to_page = "https://open-filament.github.io/f/{filament.id}"
        filament_exportdir = os.path.join(
            material_path, clear_name(filament.name))
        qrcg.from_url_to_stl(url_to_page, filament_exportdir,
                             filament.id, "models/BasePlate.scad")

    def __generate_producer_index(self, producer: Producer, producer_path: str):
        filepath = os.path.join(producer_path, "_index.md")
        title = producer.name
        data = {"title": title}
        self.__write_content_file(filepath, data)

    def __generate_material_index(self, producer: Producer, material: Material, material_path: str):
        filepath = os.path.join(material_path, "_index.md")
        title = f"{producer.name} - {material.name}"
        data = {"title": title}
        self.__write_content_file(filepath, data)

    def __write_filament_file(self, filepath: str, producer: Producer, material: Material, filament: Filament):
        data = {
            "id": filament.id,
            "title": filament.name,
            "aliases": [
                f"/f/{filament.id}"
            ],
            "material": material.name,
            "producer": producer.name,
            "type": "filament"
        }
        self.__write_content_file(filepath, data, False)

    def __write_content_file(self, filepath: str, data: dict, skip_if_exists: bool = True):
        if os.path.exists(filepath) and skip_if_exists:
            return

        with open(filepath, "w+", encoding="utf-8") as stream:
            jsonstring = json.dumps(data)
            stream.write(jsonstring)
