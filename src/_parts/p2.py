

class Character:
    """Any character: the Prince, followers, or encountered foes."""

    def __init__(self, name, skill, endurance, wealth=0, mount='none',
                 guide=False, pay=0, prince=False):
        self.name = name
        self.skill = skill
        self.endurance = endurance
        self.wounds = 0
        self.wealth = wealth
        self.mount = mount          # 'none' | 'horse' | 'winged'
        self.guide = guide
        self.pay = pay
        self.prince = prince
        self.alive = True
        self.starved = 0
        self.poisoned = 0
        self.unreliable = False
        self.town_leaver = False

    @property
    def effective_skill(self):
        return max(0, self.skill - self.starved)

    @property
    def remaining(self):
        return self.endurance - self.wounds

    @property
    def serious(self):
        return self.wounds * 2 >= self.endurance

    @property
    def unconscious(self):
        return self.wounds == self.endurance - 1

    @property
    def dead(self):
        return self.wounds >= self.endurance

    def load_capacity(self):
        cap = 10
        for _ in range(self.starved):
            cap //= 2
        return cap

    def __repr__(self):
        return (f'{self.name} (skill {self.skill}, endurance {self.endurance}, '
                f'wounds {self.wounds}, mount {self.mount})')
