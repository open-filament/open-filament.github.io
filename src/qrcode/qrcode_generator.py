from email.mime import base
from typing import Callable
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import RadialGradiantColorMask
# import qrcode.image.svg
import numpy
from solid import difference, cube, sphere, scad_render, OpenSCADObject, intersection, import_scad, use
from solid import color, cube, scad_render, translate, union, square, linear_extrude
# from solid import *
from openscad_runner import OpenScadRunner, RenderMode, ColorScheme
from PIL import Image
import os


class QrCodeGenerator:

    qr: qrcode.QRCode

    def __init__(self) -> None:
        # Create qr code instance
        self.qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,
            border=1,
        )

        if not os.path.exists("tmp"):
            os.mkdir("tmp")

    def from_url_to_png(self, url: str):
        # Add data
        self.qr.add_data(url)
        self.qr.make(fit=True)

        # Create an image from the QR Code instance
        img = self.qr.make_image()
        img.save("tmp/image.png")

    # def from_url_to_svg(self, url: str):
    #     # if method == 'basic':
    #     # Simple factory, just a set of rects.
    #     # factory = qrcode.image.svg.SvgImage
    #     # elif method == 'fragment':
    #     # Fragment factory (also just a set of rects)
    #     # factory = qrcode.image.svg.SvgFragmentImage
    #     # elif method == 'path':
    #     # Combined path factory, fixes white space that may occur when zooming
    #     factory = qrcode.image.svg.SvgPathImage

    #     # Set data to qrcode
    #     img = qrcode.make(url, image_factory=factory)

    #     # Save svg file somewhere
    #     img.save("qrcode.svg")

    def from_url_to_stl(self, url: str, export_dir: str, basefilename: str, open_scad_base: str):

        if not os.path.exists(export_dir):
            os.mkdir(export_dir)

        # Add data
        self.qr.add_data(url)
        self.qr.make(fit=True)

        # Create an image from the QR Code instance
        img: Image = self.qr.make_image()
        # print(img)
        filepath_qrcode_png = os.path.join(
            export_dir, f"{basefilename}.qrcode.png")
        img.save(filepath_qrcode_png)

        pixels = numpy.array(img)
        # print(pixels)

        # output defaults to 1 mm per unit; this lets us increase the size of objects proportionally.
        SCALE = 1.5
        HEIGHT = 1.1
        cubes = [translate([i*SCALE, j*SCALE, 0])(square(size=[SCALE, SCALE]))
                 for i, row in enumerate(pixels)
                 for j, col in enumerate(row)
                 if pixels[i, j] == False]

        print(pixels.shape)
        total_width = pixels.shape[0]*SCALE

        # base_plate = color('white')(
        #     cube(size=(pixels.shape[0] * SCALE, pixels.shape[1] * SCALE, HEIGHT / 2)))
        # qrobj = union()(base_plate, *cubes)

        # def cube_fn(cubes: list[OpenSCADObject], base_element: OpenSCADObject) -> OpenSCADObject:
        #     return union()(
        #         cubes[0],
        #         cube_fn(cubes[1:], base_element) if len(
        #             cubes) > 1 else base_element
        #     )

        # qrobj = cube_fn(cubes, base_plate)

        # qrobj = union()(
        #     translate([0, 0, -1])(
        #         cube([90, 90, 1])
        #     ),
        #     linear_extrude(height=1)(
        #         intersection()(
        #             square([90, 90]),
        #             *cubes
        #         )
        #     )
        # )

        # qrobj = union()(
        #     cube([90, 90, 0.5]),
        #     linear_extrude(height=HEIGHT)(
        #         # intersection()(
        #         # square([90, 90]),
        #         *cubes
        #         # )
        #     )
        # )

        def cubes_splitted(cubes: OpenSCADObject, size=20) -> list[OpenSCADObject]:
            # looping till length cubes
            for i in range(0, len(cubes), size):
                yield cubes[i:i + size]

        cube_chunks = list(cubes_splitted(cubes, 5))
        linear_extrudes = [color('black')(linear_extrude(height=HEIGHT)(
            *cube_chunk)) for cube_chunk in cube_chunks]

        print(total_width, "total_width")

        use(open_scad_base)
        qrobj = union()(
            BasePlate(inner_size=total_width, margin=0, hole_margin=5),
            # translate([0, 0, 2])(cube([30, 30, 1], center=True)),
            *linear_extrudes
        )

        filepath_stl = os.path.join(export_dir, f"{basefilename}.stl")
        filepath_scad = os.path.join(export_dir, f"{basefilename}.scad")
        filepath_png = os.path.join(export_dir, f"{basefilename}.png")

        openscad_script_content = scad_render(qrobj)
        f = open(filepath_scad, "w+", encoding="utf-8")
        f.write(openscad_script_content)
        f.close()

        self.__generate_qrcode_stl(filepath_stl, filepath_scad)
        self.__generate_qrcode_png(filepath_scad, filepath_png)

    def __generate_qrcode_png(self, filepath_scad, filepath_png):
        osr = OpenScadRunner(filepath_scad, filepath_png,
                             render_mode=RenderMode.preview, imgsize=(800, 600), antialias=2.0)
        osr.run()
        for line in osr.echos:
            print(line)
        for line in osr.warnings:
            print(line)
        for line in osr.errors:
            print(line)
        if osr.good():
            print("Successfully created png")

    def __generate_qrcode_stl(self, filepath_stl, filepath_scad):
        if not os.path.exists(filepath_stl):
            osr = OpenScadRunner(filepath_scad, filepath_stl)
            osr.run()
            for line in osr.echos:
                print(line)
            for line in osr.warnings:
                print(line)
            for line in osr.errors:
                print(line)
            if osr.good():
                print("Successfully created stl")
