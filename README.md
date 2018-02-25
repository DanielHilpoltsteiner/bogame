# bogame
OGame bot.

## Requirements

```
pip install bs4
pip install mechanize
```

protoc 2.6.1

## Usage

```
protoc *.proto --python_out=.
python parse.py -c=fr -n=146 -u=<EMAIL> -p=<PASSWORD> -o=<OUTPUT_FILE> -v
python print.py -i=<INPUT_FILE>
python report.py -i=<INPUT_FILE>
```
