class Character:
    def __init__(self, name, hp, attack):
        self.name = name
        self._hp = hp              # защищённый атрибут (доступен наследникам)
        self.attack = attack

    def get_hp(self):
        return self._hp

    def take_damage(self, dmg):
        self._hp = max(0, self._hp - dmg)

    def heal(self, amount):
        self._hp = min(100, self._hp + amount)

    def attack_enemy(self, enemy):
        enemy.take_damage(self.attack)
        print(f"{self.name} бьёт {enemy.name}: -{self.attack} HP")

    def use_ability(self, enemy):
        print(f"{self.name} не имеет способности")

    def should_use_ability(self):
        return False


class Human(Character):
    def __init__(self, name):
        super().__init__(name, 100, 15)

    def use_ability(self, enemy):
        heal = 20
        self.heal(heal)
        print(f" {self.name} лечится: +{heal} HP (теперь {self.get_hp()})")

    def should_use_ability(self):
        return self.get_hp() < 50


class Elf(Character):
    def __init__(self, name):
        super().__init__(name, 80, 20)

    def use_ability(self, enemy):
        dmg = self.attack * 2
        enemy.take_damage(dmg)
        print(f" {self.name} стреляет дважды: -{dmg} HP")

    def should_use_ability(self):
        return True


class Orc(Character):
    def __init__(self, name):
        super().__init__(name, 130, 18)

    def use_ability(self, enemy):
        dmg = self.attack + 5
        enemy.take_damage(dmg)
        print(f" {self.name} в ярости: -{dmg} HP")

    def should_use_ability(self):
        return self.get_hp() < 70


class Demon(Character):
    def __init__(self, name):
        super().__init__(name, 110, 22)

    def use_ability(self, enemy):
        dmg = self.attack + 10
        enemy.take_damage(dmg)
        print(f" {self.name} сжигает: -{dmg} HP")

    def should_use_ability(self):
        return True


fighters = [
    Human("чел"),
    Elf("эльф"),
    Orc("орк"),
    Demon("демон")
]

print("  БИТВА СО СПОСОБНОСТЯМИ  \n")

round_num = 0
while len([f for f in fighters if f.get_hp() > 0]) > 1:
    round_num += 1
    print(f"--- Раунд {round_num} ---")

    for attacker in fighters:
        if attacker.get_hp() <= 0:
            continue

        targets = [f for f in fighters if f.get_hp() > 0 and f != attacker]
        if not targets:
            break

        target = targets[0]

        if attacker.should_use_ability():
            attacker.use_ability(target)
        else:
            attacker.attack_enemy(target)

        if target.get_hp() <= 0:
            print(f"  ☠ {target.name} погиб!")
            break


alive = [f for f in fighters if f.get_hp() > 0]
if alive:
    winner = alive[0]
    print(f"\nПобедил: {winner.name} (HP: {winner.get_hp()})")