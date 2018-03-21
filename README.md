# bogame
OGame bot written for Python3.

## Screenshots

![Login screen](/../screenshots/screenshots/login.png?raw=true)

![Dashboard](/../screenshots/screenshots/dashboard.png?raw=true)

## Requirements

```
pip install -r requirements.txt
```

[protoc 3.5.1](https://github.com/google/protobuf/tree/master/python)

## Usage

```
protoc */*.proto --python_out=.
python main.py [-i=<PLAYER_FILE>]
```

## Acknowledgements

http://ogame.wikia.com/

Reports inspired by this spreadsheet:
http://www.voidalliance.net/screenshots/ogame/oGameEmpire.xls
