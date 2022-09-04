# Open-Filament

![header](content/open-filament-header.jpg)

**Open-Filament** is an collection of 3D-Printing filament producers, materials and product lines.

It's main purpose is to give you an easy solution to label your test print's and filament spools with a **QR-Code**.

You can simply open [https://open-filament.github.io/](https://open-filament.github.io/):

- browser producers 
- browse materials
- browse filaments
- download QR-Code badge as STL or OpenSCAD file
- print

It's based on [Hugo](https://gohugo.io/) and [Bulma](https://bulma.io/).

## Contribute

When you want to contribute, visit [GitHub](https://github.com/open-filament/open-filament.github.io) first.

### Add new producers

Each producer will be saved under [data/](data/) folder as YAML file. Feel free to create a pull request on GitHub to extend the number of producers.

See ``example.yml``

```yaml
producer:
  name: example producer
  materials:
    PLA+:
      filaments:
        PLAPlus Filament:
          color: "#FF0000"
    PETG:
      filaments:
        3D Filament - PETG:
```