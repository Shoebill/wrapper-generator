# Shoebill Wrapper Generator
This project converts .inc files from pawn to .java files for Shoebill. Please keep in mind that this project is not finished yet. It’s in an early stage and the code looks really messy right now and probably does not always work like it should. If you find any errors or bugs, please create an [Issue](https://github.com/Shoebill/wrapper-generator/issues/new) with an detailed description of your problem.

# What you will need
* Python ([Windows](https://www.python.org/downloads/windows/), [Linux](http://docs.python-guide.org/en/latest/starting/install/linux/), [OS X](http://docs.python-guide.org/en/latest/starting/install/osx/))
* [PLY](http://www.dabeaz.com/ply/) and [cidl](https://github.com/Zeex/cidl) (can be installed via pip)
* An .idl you want to convert (use FCNPC.idl as an example)

# How to use

Open an command prompt an type in:
```
python main.py idls/FCNPC.idl
```
After the process has been finished, you will get 3 files which contain native functions, callbacks and definitions.

# Credits
* Zeex for the .IDL parser