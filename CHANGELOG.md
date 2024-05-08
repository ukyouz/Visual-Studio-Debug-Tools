# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.1.1 (2024/05/08)

### Added

#### VS Debugger

- Support to expand function pointer as name
- Support show floating number for REAL number type
- Bin Parser widget support in dock

### Changed

- Pdb Database generation shows error reason
- Improve file explorer view
- Fix expression for casting structure

#### VS Debugger

- Fix application crashes in some corner cases

#### Bin Viewer

- For array data, use 0 count to parse all until the end

#### Run Script

- Fix new file can not be saved

## 0.1 (2024/03/22)

Now support ANY valid C expression in the following fields:

- Expression view: expression
- Memory view: address, size
- Bin Parser widget: struct, offset

### Added

- menu: PDB/Recently PDBs. Show database loading history, switch by clicking
- menu: Help/About Me...
- Application log in log folder

#### VS Debugger

- Support right-click on structure item in Expression view
- Support editable top item in Expression view. Default enabled, you can disable from the widget menu on top-right corner.

### Changed

#### VS Debugger

- Fix suffix when dump binary in Memory view
- Fix application crash if some process names are in Japanese

#### Bin Viewer

- Improve `count` field for parsing struct in BinView
    - for array, 0 parses all
    - for struct, 0 parses one

#### Others

- Improve GUI
- Improve error messages

## 0.0.3

First Release!

### Added

#### VS Debugger

- Memory View: View/Edit/Dump memory
- Expression View: View/Edit valid expression
- Multiple Memory/Expression View support

#### Bin Viewer

- View .bin file with structure at offset

#### Run Script

- Run valid python script to interact with VS Debugger or Bin Viewer.
