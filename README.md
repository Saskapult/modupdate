# Modupdate
I wanted to download things from curseforge automatically but this was not so easy.
There were not many scripts online that I could go to for guidance, so I'm putting this up to maybe help people.

Update:
It seems that the api I have used redirects requests for certain fabric mods to their forge counterparts.
I absolutely hate this.

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

