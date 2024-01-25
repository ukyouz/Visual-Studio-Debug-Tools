# Visual Studio Debug Tools

This is a simple project help you debug app compiled from Visual Studio by giving you a more powerful Expression view and Memory view.

## Installation

Clone this repo, also: 

```bash
$ git submodule add https://github.com/ukyouz/pdbparse modules/pdbparser
```

Then I recommandate using Python virtual environment such as:

```bash
$ virtualenv venv
```

Then if you use Powershell:

```
$ .\venv\Scripts\activate.ps1
$ pip install -r requirements.txt
```

You are good to go.

## Tools

There are 2 tools in this repo.

### VS Debugger



### Bin View



## Support Languages

- C

Due to limitations of pdb parser in my other repo, currently only support C. May be extended in the future.
