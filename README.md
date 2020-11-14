# Modupdate
I wanted to download things from curseforge automatically but this was not so easy.
There were not many scripts online that I could go to for guidance, so I'm putting this up to maybe help people.

Uses twitch app api and cfwidget.
Big thanks to cfwidget for making any of this possible, I am very grateful.
Without it we would not be able to tell if a file was for fabric or forge.

# Usage
I hope that this is understandable.
- Run "pip install -r requirements.txt" to install the required packages.
- Create a new Minecraft instance and install Forge/Fabric.
- Place the modupdate.py file in your ".minecraft" directory.
- Create a file called "moddata.txt"
- Put your version stuff in there. ({"1.16.2":1, "Fabric":1})
- Fill the rest of it with curseforge links. (https://www.curseforge.com/minecraft/mc-mods/MODNAME)
- Make a sacrifice to the number gods to boost your chances of success.
- Run the thing!

# Issues
Some mod authors have not included version tags for their files and this breaks the program.

The twitch api is not great for searching for mods and will sometimes show no results.
In this case we fall back and use the mod name to find the files, but this can be inaccurate.