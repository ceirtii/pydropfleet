import csv
import json

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
        gunfile = open('guns.json')
        gunreader = json.load(gunfile)
        for row in gunreader:
            guntype = row['guntype']
            row.pop('guntype')
            Weapon.gunDB[guntype] = row

    @staticmethod
    def load_gunDB_csv():
        gunfile = open('guns.csv')
        gunreader = csv.reader(gunfile)
        for row in gunreader:
            guntype = row.pop(0)
            gunstats = dict()
            gunstats.update({'lock':row.pop(0)})
            gunstats.update({'attack':row.pop(0)})
            gunstats.update({'damage':row.pop(0)})
            Weapon.gunDB.update({guntype:gunstats})
        
    def __str__(self):
        out_str = f'{self.guntype}'
        if self.linked != 0:
            out_str = out_str + f'({self.linked})'
        out_str = out_str + f' lock:{self.lock}, att:{self.attack}, dam:{self.damage} arc:{self.arc}'
        return out_str
    
    def to_dict(self):
        out = {'guntype':self.guntype, 'arc':self.arc, 'linked':self.linked, 'count':self.count}
        return out

class LaunchAsset():
    def __init__(self, faction, count):
        self.faction = faction
        self.count = count

if __name__ == "__main__":
    Weapon.load_gunDB()