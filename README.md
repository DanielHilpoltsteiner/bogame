# bogame
OGame bot written for Python3.

## Requirements

```
pip install -r pip-requirements.txt
```

[protoc 3.5.1](https://github.com/google/protobuf/tree/master/python)

## Usage

Command-line:
```
protoc *.proto --python_out=.
python parse.py -c=fr -n=146 -u=<EMAIL> -p=<PASSWORD> -o=<OUTPUT_FILE> -v
python print.py -i=<INPUT_FILE>
python report.py -i=<INPUT_FILE>
```

GUI:
```
protoc *.proto --python_out=.
python bogame.py
```
