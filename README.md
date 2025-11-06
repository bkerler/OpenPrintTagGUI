# OpenPrintTagGUI
GUI for the open print tag standard (openprinttag.org)

### Requirements
- python >= 3.8

### Installation
```bash
git clone https://github.com/bkerler/OpenPrintTagGUI
git submodule init
git submodule update
pip3 install -r requirements.txt
```

### Usage
```bash
python openprinttag_gui.py
```
or opening your tag binary directly
```bash
python openprinttag_gui.py yourtag.bin
```

### ToDo
- TD1S integration
- Read/Write directly to tag using NFC Writer

### Currently supported
- Read/write binary blobs that can be written using ProxMark3 cli

### Add custom filament to default settings
```
{
  "Prusament": {
    "My special ASA": {
      "weight": [193, 850, 850],
      "material": "ASA",
      "density": 1.07,
      "nozzle": [
        250,
        270
      ],
      "bed": [`
        105,
        115
      ],
      "properties": [
        "Abrasive",
        "Contains Carbon Fiber"
      ]
      "colors": {
        "Jet Black": ["#24292A",0.4,"https://www.prusa3d.com/product/prusament-asa-jet-black-800g-nfc/"],
        "Lipstick Red": ["#D02F37",0.4,"https://www.prusa3d.com/product/prusament-asa-lipstick-red-800g-nfc/"],
        "Natural": ["#DFDFD3",0.4,"https://www.prusa3d.com/product/prusament-asa-natural-800g-nfc/"],
        "Prusa Galaxy Black": ["#3D3E3D",0.4,"https://www.prusa3d.com/product/prusament-asa-prusa-galaxy-black-800g-nfc/"],
        "Prusa Orange": ["#EA5E1A",0.4,"https://www.prusa3d.com/product/prusament-asa-prusa-orange-800g-nfc/"],
        "Prusa Sapphire Blue": ["#3B4468",0.3,"https://www.prusa3d.com/product/prusament-asa-prusa-sapphire-blue-800g-nfc/"],
        "Signal White":["#E3DFD9",2.4,"https://www.prusa3d.com/product/prusament-asa-signal-white-800g-nfc/"],
        "Prusa Pro Green": ["#33d3b6",1.6,"https://www.prusa3d.com/product/prusament-asa-prusa-pro-green-800g-nfc/"]
      }
    },
}
```

- Just add a new json or edit an existing filament json in [data/filaments](data/filaments)
- <b>Brand name</b> = ```Prusament```
- <b>Material name</b> = ```My special ASA```
- <b>"material" field</b> = material type abbreviation ```ASA```
- <b>"density" field</b> = density in g/cm³
- if no <b>"diameter" field</b> is given, ```1.75``` mm is assumed
- <b>"weight" field</b> = ```[empty_spool_weight_in_g,nominal_spool_weight_netto_in_g,actual_spool_weight_netto_in_g]```
- <b>"nozzle" field</b> = ```[min_nozzle_temp_celsius,max_nozzle_temp_celsius]```
- <b>"bed" field</b> = ```[min_bed_temp_celsius, max_bed_temp_celsius]```
- <b>"properties" field</b> = tags, see [data/filament/material_properties.json](data/filament/material_properties.json)
- <b>"colors" field</b> = each field has structure ```"name" : [hex_color,opacity_transmission_distance,url]```

### Read/Write using proxmark3 (ICODE-SLIX SLIX2 ISO15693) or NXP TagInfo App
using [Icemans Proxmark3 Fork](https://github.com/RfidResearchGroup/proxmark3)
- Identify tag
```bash
hf 15 info
```

- Read tag
```bash
hf 15 dump
```

- Write tag
```bash
hf 15 restore f mytag.bin
```
