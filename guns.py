import csv

class Weapon:
    gunDB = dict()

    def __init__(self, guntype, arc, linked=0, count=1):
        self.guntype = guntype
        self.arc = arc
        self.linked = linked
        if not Weapon.gunDB:
            Weapon.load_gunDB()
        self.lock = Weapon.gunDB[guntype]['lock']
        self.count = count
        self.attack = Weapon.gunDB[guntype]['attack']
        self.damage = Weapon.gunDB[guntype]['damage']

    @staticmethod
    def load_gunDB():
        gunfile = open('guns.csv')
        gunreader = csv.reader(gunfile)
        for row in gunreader:
            guntype = row.pop(0)
            gunstats = dict()
            gunstats.update({'lock':row.pop(0)})
            gunstats.update({'attack':row.pop(0)})
            gunstats.update({'damage':row.pop(0)})
            Weapon.gunDB.update({guntype:gunstats})

class LaunchAsset():
    def __init__(self):
        pass