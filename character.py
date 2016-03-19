#!/usr/bin/python3
'''
Created on 2016-03-17

@author: rob
'''
from random import randint, choice
import string
import os

class Character(object):
    '''
    A class representing a first-edition Paranoia character 
    '''
    _name = None
    _primary_attributes = {}
    _secondary_attributes = {}
    _service_group = None
    _secret_society = None
    _mutant_powers = None
    _registered_mutant = False
    _equipment = None
    _skills = None
    _credits = None
    _weapon_stats = None

    _skill_tree = None

    def __init__(self):
        '''
        Constructor. This randomly generates a character based on the procedure
        specified in the Paranoia first edition Player's Handbook.
        '''
        self._skill_tree = SkillTree(DataTables.SKILLS)
        self._generate_primary_attributes()
        self._generate_mutant_powers()
        self._generate_equipment()
        self._generate_service_group()
        self._generate_secret_society()
        self._generate_skills()
        self._calculate_attribute_boosts()
        self._generate_secondary_attributes()
        self._generate_weapon_stats()
        self._generate_name()

    def _generate_primary_attributes(self):
        for attribute in DataTables.PRIMARY_ATTRIBUTES:
            dice = DataTables.PRIMARY_ATTRIBUTES[attribute]
            value = Dice.roll(dice[0], dice[1], dice[2])
            self._primary_attributes[attribute] = value

    def _generate_secondary_attributes(self):
        for attribute in DataTables.SECONDARY_ATTRIBUTES:
            attribute_data = DataTables.SECONDARY_ATTRIBUTES[attribute]
            governing_primary_attribute = (self._primary_attributes
                                                        [attribute_data[0]])
            if (governing_primary_attribute <= 28):
                value = attribute_data[1][governing_primary_attribute]
            else:
                difference = governing_primary_attribute - 28
                value = attribute_data[1][28]
                value += attribute_data[2] * difference

            self._secondary_attributes[attribute] = value

    def _generate_mutant_powers(self):
        attribute_sum = 0
        total_power_count = 1
        current_powers = []

        for attribute in self._primary_attributes:
            attribute_sum += self._primary_attributes[attribute]

        if (attribute_sum <= 80):
            total_power_count += 1

        if (attribute_sum <= 65):
            total_power_count += 1

        while (len(current_powers) < total_power_count):
            while True:
                power_roll = Dice.roll(1, 100, 0)

                for value in DataTables.NORMAL_MUTANT_POWERS:
                    if value[2] <= power_roll & power_roll <= value[3]:
                        power = value

                if (power[4] == 2):  # extraordinary mutant power
                    for value in DataTables.EXTRAORDINARY_MUTANT_POWERS:
                        if value[2] <= power_roll & power_roll <= value[3]:
                            power = value

                if (current_powers.count(power) == 0):
                    break

            current_powers.append(power)

            if (power[4] == 1 & total_power_count == 1):
                total_power_count += 1

        self._mutant_powers = current_powers

        if (Dice.roll(1, 100, 0) <= DataTables.MUTANT_REGISTRATION_CHANCE):
            self._registered_mutant = True

    def _generate_equipment(self):
        self._credits = DataTables.STARTING_CREDITS
        self._equipment = DataTables.MANDATORY_EQUIPMENT.copy()

        while True:
            item = choice(DataTables.OPTIONAL_EQUIPMENT)
            if (self._equipment.count(item[0]) == 0):
                if (item[1] <= self._credits):
                    self._equipment.append(item[0])
                    self._credits -= item[1]
                else:
                    return

    def _generate_service_group(self):
        service_group_roll = Dice.roll(1, 10, 0)
        for group in DataTables.SERVICE_GROUPS:
            if (group[1] <= service_group_roll
                & service_group_roll <= group[2]):
                self._service_group = group[0]

    def _generate_secret_society(self):
        while self._secret_society is None:
            secret_society_roll = Dice.roll(1, 100, 0)
            for society in  DataTables.SECRET_SOCIETIES:
                if (society[1] <= secret_society_roll
                    & secret_society_roll <= society[2]):
                    if society[3] is None:  # society with no mutant restriction
                        self._secret_society = society[0]
                    else:
                        for power in self._mutant_powers:
                            if (power[1] == society[3]):
                                self._secret_society = society[0]
                                break

    def _generate_skills(self):
        self._skills = []
        # print("Assigning troubleshooter _skills")
        for potential_skill in DataTables.TROUBLESHOOTER_SKILLS:
            for skill in self._skill_tree.all_skills:
                if skill._name == potential_skill:
                    skill.character_level = skill.base_level
                    self._skills.append(skill)

        # print("Assigning service group _skills")
        chosen_service_group_skills = 0
        service_group_skill_names = (DataTables.
                                     SERVICE_GROUP_SKILLS[self._service_group])
        service_group_skills = []
        for skill in self._skill_tree.all_skills:
            if service_group_skill_names.count(skill._name) > 0:
                service_group_skills.append(skill)

        # print(service_group_skills)

        while (chosen_service_group_skills <
               DataTables.SERVICE_GROUP_SKILL_COUNT):
            new_skill = choice(service_group_skills)

            while self._skills.count(new_skill) > 0:
                if len(new_skill.child_skills) == 0:
                    new_skill.character_level += 1
                    # print("Reached end of tree, incrementing skill level")
                    break

                new_skill = choice(new_skill.child_skills)

            if new_skill.character_level is None:
                # print("Assigning a new skill")
                new_skill.character_level = new_skill.base_level
                self._skills.append(new_skill)

            chosen_service_group_skills += 1

        # print("Assigning free _skills")
        chosen_free_skills = 0
        while (chosen_free_skills < DataTables.FREE_SKILL_COUNT):
            new_skill = choice(self._skill_tree.top_level_skills)

            while self._skills.count(new_skill) > 0:
                if len(new_skill.child_skills) == 0:
                    new_skill.character_level += 1
                    # print("Reached end of tree, incrementing skill level")
                    break

                new_skill = choice(new_skill.child_skills)

            if new_skill.character_level is None:
                # print("Assigning a new skill")
                new_skill.character_level = new_skill.base_level
                self._skills.append(new_skill)

            chosen_free_skills += 1

        # print(self._skills)

    def _calculate_attribute_boosts(self):
        for skill in self._skills:
            if skill.parent_skill is not None:
                if skill.parent_skill._name == "Self-improvement":
                    attribute = skill._name
                    boost = skill.character_level - 2
                    if boost > 4:
                        boost = 4
                    # print("Boosting {} by {} from {} due to skill"
                    #      .format(attribute, boost,
                    #              self._primary_attributes[attribute]))
                    self._primary_attributes[attribute] += boost

        for power in self._mutant_powers:
            if power[0].split(" ")[0] == "Superior":
                attribute = power[0].split(" ", 1)[1].lower()
                boost = Dice.roll(1, 10, 0)
                # print("Boosting {} by {} from {} due to mutation"
                #      .format(attribute, boost,
                #              self._primary_attributes[attribute]))
                self._primary_attributes[attribute] += boost


    def _generate_weapon_stats(self):
        self._weapon_stats = []

        # laser weapon skill is Basics > Aimed Weapon Combat > Laser > pistol
        laser_to_hit = 5
        laser_governing_skill = None
        for skill in self._skills:
            if skill._name == "Basics":
                laser_governing_skill = skill

        for skill in laser_governing_skill.child_skills:
            if ((skill._name == "Aimed Weapon Combat")
                & (skill.character_level is not None)):
                laser_governing_skill = skill

        if laser_governing_skill._name == "Aimed Weapon Combat":
            for skill in laser_governing_skill.child_skills:
                if ((skill._name == "Laser")
                    & (skill.character_level is not None)):
                    laser_governing_skill = skill

        if laser_governing_skill._name == "Laser":
            for skill in laser_governing_skill.child_skills:
                if ((skill._name == "pistol")
                    & (skill.character_level is not None)):
                    laser_governing_skill = skill

        if laser_governing_skill is not None:
            laser_to_hit = 15 + (laser_governing_skill.character_level * 5)

        bonus = self._secondary_attributes["aimed weapon bonus"]
        laser_to_hit += bonus

        if laser_to_hit < 5:
            laser_to_hit = 5

        self._weapon_stats.append(["laser pistol", laser_to_hit])

        # knife (melee) skill is Basics > Melee Combat > knife
        knife_melee_to_hit = 5
        knife_melee_governing_skill = None

        for skill in self._skills:
            if skill._name == "Basics":
                knife_melee_governing_skill = skill

        for skill in knife_melee_governing_skill.child_skills:
            if ((skill._name == "Melee Combat")
                & (skill.character_level is not None)):
                knife_melee_governing_skill = skill

        if knife_melee_governing_skill._name == "Melee Combat":
            for skill in knife_melee_governing_skill.child_skills:
                if ((skill._name == "knife")
                    & (skill.character_level is not None)):
                    knife_melee_governing_skill = skill

        if knife_melee_governing_skill is not None:
            knife_melee_to_hit = 15 + (knife_melee_governing_skill.character_level * 5)

        bonus = self._secondary_attributes["melee bonus"]
        knife_melee_to_hit += bonus

        if knife_melee_to_hit < 5:
            knife_melee_to_hit = 5

        self._weapon_stats.append(["knife (melee)", knife_melee_to_hit])

        # knife (thrown) skill is Basics > Aimed Weapon Combat > Projectile >
        #     thrown knife
        knife_thrown_to_hit = 5
        knife_thrown_governing_skill = None
        for skill in self._skills:
            if skill._name == "Basics":
                knife_thrown_governing_skill = skill

        for skill in knife_thrown_governing_skill.child_skills:
            if ((skill._name == "Aimed Weapon Combat")
                & (skill.character_level is not None)):
                knife_thrown_governing_skill = skill

        if knife_thrown_governing_skill._name == "Aimed Weapon Combat":
            for skill in knife_thrown_governing_skill.child_skills:
                if ((skill._name == "Projectile")
                    & (skill.character_level is not None)):
                    knife_thrown_governing_skill = skill

        if knife_thrown_governing_skill._name == "Projectile":
            for skill in knife_thrown_governing_skill.child_skills:
                if ((skill._name == "thrown knife")
                    & (skill.character_level is not None)):
                    knife_thrown_governing_skill = skill

        if knife_thrown_governing_skill is not None:
            knife_thrown_to_hit = 15 + (knife_thrown_governing_skill.character_level * 5)

        bonus = self._secondary_attributes["aimed weapon bonus"]
        knife_thrown_to_hit += bonus

        if knife_thrown_to_hit < 5:
            knife_thrown_to_hit = 5

        self._weapon_stats.append(["knife (thrown)", knife_thrown_to_hit])

    def _generate_name(self):
        gender = Dice.roll(1, 2)
        names = Names()

        if gender == 1:
            self._name = choice(names.male_names)
        else:
            self._name = choice(names.female_names)

        self._name += "-R-"

        self._name += choice(string.ascii_uppercase)
        self._name += choice(string.ascii_uppercase)
        self._name += choice(string.ascii_uppercase)
        self._name += "-1"

    def print_character(self):
        '''
        Outputs the generated character to standard output
        '''
        print(str.format("NAME\t{}", self._name).expandtabs(20))
        print("")
        print("PRIMARY ATTRIBUTES\t\tSECONDARY ATTRIBUTES".expandtabs(20))
        print(str.format("Strength\t{:3}\tCarrying Capacity\t{:3}kg",
                         self._primary_attributes['strength'],
                         self._secondary_attributes['carrying capacity'])
              .expandtabs(20))
        print(str.format("Endurance\t{:3}\tDamage Bonus\t{:3}",
                         self._primary_attributes['endurance'],
                         self._secondary_attributes['damage bonus'])
              .expandtabs(20))
        print(str.format("Agility\t{:3}\tMacho Bonus\t{:3}",
                         self._primary_attributes['agility'],
                         self._secondary_attributes['macho bonus'])
              .expandtabs(20))
        print(str.format("Manual Dexterity\t{:3}\tMelee Bonus\t{:+3}%",
                         self._primary_attributes['manual dexterity'],
                         self._secondary_attributes['melee bonus'])
              .expandtabs(20))
        print(str.format("Moxie\t{:3}\tAimed Weapon Bonus\t{:+3}%",
                         self._primary_attributes['moxie'],
                         self._secondary_attributes['aimed weapon bonus'])
              .expandtabs(20))
        print(str.format("Chutzpah\t{:3}\tComprehension Bonus\t{:+3}%",
                         self._primary_attributes['chutzpah'],
                         self._secondary_attributes['comprehension bonus'])
              .expandtabs(20))
        print(str.format("Mechanical Aptitude\t{:3}\t"
                         "Believability Bonus\t{:+3}%",
                         self._primary_attributes['mechanical aptitude'],
                         self._secondary_attributes['believability bonus'])
              .expandtabs(20))
        print(str.format("Power Index\t{:3}\tRepair Bonus\t{:+3}%",
                         self._primary_attributes['power index'],
                         self._secondary_attributes['repair bonus'])
              .expandtabs(20))

        print("")

        print("SECURITY CLEARANCE\tRED".expandtabs(20))
        print(str.format("SERVICE GROUP\t{}", self._service_group)
              .expandtabs(20))
        print(str.format("SECRET SOCIETY\t{}, rank 1", self._secret_society)
              .expandtabs(20))

        print("")

        if self._registered_mutant:
            print("MUTANT POWERS (REGISTERED)")
        else:
            print("MUTANT POWERS")
        power_string = ""
        power_num = 1
        for power in self._mutant_powers:
            power_string += str.format("{} ({})", power[0], power[1])
            if power_num % 2 == 0:
                power_string += "\n"
            else:
                power_string += "\t"
            power_num += 1

        print(power_string.rstrip().expandtabs(40))

        print("")
        print(str.format("CREDITS\t{:3}", self._credits).expandtabs(20))
        print("")
        print("EQUIPMENT")
        equipment_string = ""
        equipment_num = 1
        for item in self._equipment:
            equipment_string += item
            if equipment_num % 2 == 0:
                equipment_string += "\n"
            else:
                equipment_string += "\t"
            equipment_num += 1

        print(equipment_string.rstrip().expandtabs(40))

        print("")

        print("WEAPONS")
        for item in self._weapon_stats:
            print(str.format("{}\t{:3}%", item[0], item[1]).expandtabs(20))

        print("")

        print("SKILLS")
        self._skill_tree.print_character_skill_tree(self._secondary_attributes)

class Dice(object):
    '''
    Class to handle die-rolling behaviour
    '''
    
    @classmethod
    def roll(cls, number, die, modifier=0):
        '''
        Performs a random die roll, directly transferable to XdX+X notation.
        
        Args:
            number: the number of dice to roll
            die: the number of faces on each die
            modifier: the amount to add to the resulting roll
        
        Returns:
            the resulting roll, as an integer
        '''

        result = 0

        for i in range(number):
            result += randint(1, die)

        result += modifier
        return result

class Skill(object):
    '''
    Class to represent an individual skill
    
    Attributes:
        name: the name of the skill
        governing_attribute: the secondary character attribute applying to this 
            skill
        base_level: the level of the skill, as listed in the Player's Handbook
        child_skills: a list of Skill objects representing this skill's children
        parent_skill: the Skill object representing this skill's parent
        character_level: the current character level for this skill, or None
            if the character has no level in it
    '''
    name = None
    governing_attribute = None
    base_level = None
    child_skills = None
    parent_skill = None
    character_level = None

    def __init__(self, name, attribute=None, level=1):
        '''
        Constructor
        
        Args:
            name: the name of the skill
            attribute: the secondary character attribute applying ot this skill
            level: the level of the skill as listed in the Player's Handbook
        '''
        self._name = name
        self.governing_attribute = attribute
        self.base_level = level
        self.child_skills = []

    def add_child(self, child_skill):
        '''
        Assign a Skill object as a child of this skill
        
        Args:
            child_skill: the Skill object for the child skill
            
        Raises:
            TypeError: Only skills can be assigned to as children
            ValueError: Child skill already has a parent
            ValueError: Child skill has invalid level
        '''
        if type(child_skill) is not Skill:
            raise TypeError("Only skills can be assigned to as children")

        if child_skill.parent_skill is not None:
            raise ValueError("Child skill already has a parent")

        if (child_skill.base_level != self.base_level + 1):
            raise ValueError("Child skill has invalid level")

        self.child_skills.append(child_skill)
        child_skill.parent_skill = self

    def print_skill_and_children(self):
        '''
        Prints the skill tree, starting at this skill
        '''
        print(str.format("\t{0} ({2}) - {1}", self._name,
                         self.governing_attribute,
                         self.base_level).expandtabs((self.base_level - 1) * 4))
        for child in self.child_skills:
            child.print_skill_and_children()

    def print_character_skill_and_children(self, attributes):
        '''
        Prints the skill tree, starting at this skill, including only skills 
        with a character level
        
        Additionally, prints the percentages for these skills, modified by
        the governing attributes if they are provided.
        
        Args:
            attributes: a dictionary of secondary attributes to use for
                modifying skill percentages
        ''' 
        if self.character_level is not None:
            print(str.format("\t{0} ({1}) - {3}%/{2}%", self._name,
                             self.character_level,
                             self._calculate_percentage(attributes),
                             self._calculate_percentage(None))
                  .expandtabs((self.base_level - 1) * 4))
        for child in self.child_skills:
            child.print_character_skill_and_children(attributes)

    def _calculate_percentage(self, attributes):
        level = None
        if self.character_level == None:
            level = 5
        else:
            level = 15 + (self.character_level * 5)
            if (attributes is not None) & (self.governing_attribute is not None):
                level += attributes[self.governing_attribute]

        if level < 5:
            level = 5

        return level

    def __repr__(self, *args, **kwargs):
        return self._name

class SkillTree(object):
    '''
    A crude tree of skills
    
    Attributes:
        top_level_skills: a list of Skill at the top of the tree
        all_skills: a list of every Skill object in the tree
    '''
    top_level_skills = None
    all_skills = None

    def __init__(self, skill_list):
        '''
        Constructor. Builds the skill tree.
        
        Args:
            skill_list: a list of skills, in list format - see 
                DataTables.SKILLS
        '''
        self.top_level_skills = []
        self.all_skills = []
        self._build_tree(skill_list)

    def _build_tree(self, skill_list):

        temp_skill_list = []

        # first, build up all the relationships
        for skill_data in skill_list:
            skill = Skill(skill_data[0], skill_data[1], skill_data[2])

            if skill_data[3] is None:
                temp_skill_list.append(skill)
            else:  # skill has parent
                for existing_skill in temp_skill_list:
                    if existing_skill._name == skill_data[3]:
                        existing_skill.add_child(skill)
                        # print(str.format("Assigning skill {} to parent {}",
                        #                 skill._name, existing_skill._name))
                        break

                if skill.parent_skill is None:
                    raise ValueError("Could not find specified parent skill")

                temp_skill_list.append(skill)

        # then, assign list of top level _skills

        for skill in temp_skill_list:
            self.all_skills.append(skill)
            if skill.parent_skill is None:
                self.top_level_skills.append(skill)

        # print(str.format("{} _skills generated, {} at top level",
        #      len(self.all_skills), len(self.top_level_skills)))

    def print_skill_tree(self):
        '''
        Prints the entire skill tree
        '''
        for skill in self.top_level_skills:
            skill.print_skill_and_children()

    def print_character_skill_tree(self, attributes):
        '''
        Prints the entire skill tree, including only skills with a character 
        level
        
        Additionally, prints the percentages for these skills, modified by
        the governing attributes if they are provided.
        
        Args:
            attributes: a dictionary of secondary attributes to use for
                modifying skill percentages
        ''' 
        for skill in self.top_level_skills:
            skill.print_character_skill_and_children(attributes)

class Names(object):
    '''
    A class for holding first names to use in random name generation.
    
    Attributes:
        male_names: a list of male names
        female_names: a list of female names
    '''
    male_names = None
    female_names = None
    _NAME_FILE = "names.txt"

    def __init__(self):
        '''
        Constructor. Reads the names in names.txt and generates the male and
        female lists.
        '''
        self.male_names = []
        self.female_names = []

        file = open(os.path.join(os.path.dirname(__file__), self._NAME_FILE), 
                    'r')

        for line in file:
            name_data = line.split(" ")
            name = name_data[2].strip().capitalize()
            if name_data[0] == "MF":
                self.male_names.append(name)
                self.female_names.append(name)
            elif name_data[0] == "MO":
                self.male_names.append(name)
            elif name_data[0] == "FO":
                self.female_names.append(name)

        file.close()

class DataTables(object):
    '''
    A class containing the relevant data tables for character generation
    
    Attributes:
        PRIMARY_ATTRIBUTES: primary character attributes, and their die
            rolls
        SECONDARY_ATTRIBUTES: secondary character attributes, and information
            on how they are calculated
        SERVICE_GROUPS: service groups, and the corresponding values on a d10
        SECRET_SOCIETIES: secret societies, and their corresponding values on a 
            d100 and mutant power category restrictions
        NORMAL_MUTANT_POWERS: normal mutant powers, their corresponding values
            on a d100, and any special rulse
        EXTRAORDINARY_MUTANT_POWERS: extraordinary mutant powers, and their
            corresponding values on a d100
        MUTANT_REGISTRATION_CHANCE: the percentile chance that a character will
            register their mutant power(s)
        MANDATORY_EQUIPMENT: all the equipment all Troubleshooters should have
        OPTIONAL_EQUIPMENT: equipment for purchase, with prices
        SKILLS: skills, with attributes, base levels, and parents
        TROUBLESHOOTER_SKILLS: the skills all Troubleshooters have
        SERVICE_GROUP_SKILL_COUNT: the number of service group skills to assign
        SERVICE_GROUP_SKILLS: a dictionary of the top-level skills corresponding
            to each service group
        FREE_SKILL_COUNT: the number of skills a Troubleshooter can choose 
            freely
    '''
    
    # primary attributes and their die rolls
    PRIMARY_ATTRIBUTES = {
        'strength': [1, 10, 8],
        'endurance': [1, 10, 8],
        'agility': [2, 10, 0],
        'manual dexterity': [2, 10, 0],
        'moxie': [2, 10, 0],
        'chutzpah': [2, 10, 0],
        'mechanical aptitude': [2, 10, 0],
        'power index': [1, 10, 5]}

    # secondary attributes, with governing attribute, lookup table, and bonus
    # for each attribute point above 28
    SECONDARY_ATTRIBUTES = {
        'carrying capacity':
            ['strength', {
                2: 25,
                3: 25,
                4: 25,
                5: 25,
                6: 25,
                7: 25,
                8: 25,
                9: 25,
                10: 25,
                11: 25,
                12: 25,
                13: 30,
                14: 35,
                15: 40,
                16: 45,
                17: 50,
                18: 55,
                19: 60,
                20: 65,
                21: 70,
                22: 75,
                23: 80,
                24: 85,
                25: 90,
                26: 95,
                27: 100,
                28: 105},
             5],
        'damage bonus':
            ['strength', {
                2: 0,
                3: 0,
                4: 0,
                5: 0,
                6: 0,
                7: 0,
                8: 0,
                9: 0,
                10: 0,
                11: 0,
                12: 0,
                13: 0,
                14: 1,
                15: 1,
                16: 1,
                17: 1,
                18: 1,
                19: 2,
                20: 2,
                21: 2,
                22: 2,
                23: 2,
                24: 3,
                25: 3,
                26: 3,
                27: 3,
                28: 3},
             0],
        'macho bonus':
            ['endurance', {
                2: 0,
                3: 0,
                4: 0,
                5: 0,
                6: 0,
                7: 0,
                8: 0,
                9: 0,
                10: 0,
                11: 0,
                12: 0,
                13: 0,
                14:-1,
                15:-1,
                16:-1,
                17:-1,
                18:-1,
                19:-2,
                20:-2,
                21:-2,
                22:-2,
                23:-2,
                24:-3,
                25:-3,
                26:-3,
                27:-3,
                28:-3},
             0],
        'melee bonus':
            ['agility', {
                2:-25,
                3:-20,
                4:-15,
                5:-10,
                6:-5,
                7:-4,
                8:-3,
                9:-2,
                10:-1,
                11: 1,
                12: 3,
                13: 5,
                14: 7,
                15: 10,
                16: 12,
                17: 15,
                18: 17,
                19: 20,
                20: 22,
                21: 25,
                22: 27,
                23: 30,
                24: 32,
                25: 35,
                26: 37,
                27: 40,
                28: 42},
             2],
        'aimed weapon bonus':
            ['manual dexterity', {
                2:-25,
                3:-20,
                4:-15,
                5:-10,
                6:-5,
                7:-4,
                8:-3,
                9:-2,
                10:-1,
                11: 1,
                12: 3,
                13: 5,
                14: 7,
                15: 10,
                16: 12,
                17: 15,
                18: 17,
                19: 20,
                20: 22,
                21: 25,
                22: 27,
                23: 30,
                24: 32,
                25: 35,
                26: 37,
                27: 40,
                28: 42},
             2],
        'comprehension bonus':
            ['moxie', {
                2:-30,
                3:-25,
                4:-20,
                5:-15,
                6:-10,
                7:-5,
                8:-3,
                9:-2,
                10:-1,
                11: 1,
                12: 2,
                13: 4,
                14: 5,
                15: 7,
                16: 10,
                17: 12,
                18: 15,
                19: 17,
                20: 20,
                21: 22,
                22: 25,
                23: 27,
                24: 30,
                25: 32,
                26: 35,
                27: 37,
                28: 40},
             2],
        'believability bonus':
            ['chutzpah', {
                2:-35,
                3:-30,
                4:-25,
                5:-20,
                6:-15,
                7:-10,
                8:-5,
                9:-3,
                10:-1,
                11: 1,
                12: 3,
                13: 5,
                14: 7,
                15: 10,
                16: 12,
                17: 15,
                18: 17,
                19: 20,
                20: 22,
                21: 25,
                22: 27,
                23: 30,
                24: 32,
                25: 35,
                26: 37,
                27: 40,
                28: 42},
             2],
        'repair bonus':
            ['mechanical aptitude', {
                2:-30,
                3:-25,
                4:-20,
                5:-15,
                6:-10,
                7:-5,
                8:-3,
                9:-2,
                10:-1,
                11: 1,
                12: 2,
                13: 4,
                14: 5,
                15: 7,
                16: 10,
                17: 12,
                18: 15,
                19: 17,
                20: 20,
                21: 22,
                22: 25,
                23: 27,
                24: 30,
                25: 32,
                26: 35,
                27: 37,
                28: 40},
             2],
    }

    # service groups and their value on a d10 roll
    SERVICE_GROUPS = [
        ["Internal Security", 1, 1],
        ["Technical Services", 2, 2],
        ["HPD & Mind Control", 3, 4],
        ["Armed Forces", 5, 5],
        ["Production, Logistics and Commissary", 6, 7],
        ["Power Services", 8, 8],
        ["Research and Design", 9, 9],
        ["Central Processing Unit", 10, 10]]

    # secret societies, with their value on a d100 roll, and the governing
    # mutant power category (if any)

    SECRET_SOCIETIES = [
        ["First Church of Christ Computer Programmer", 1, 5, None],
        ["Spy for Another Alpha Complex", 6, 10, None],
        ["Psion", 11, 15, "psionic"],
        ["Humanists", 16, 20, None],
        ["Mystics", 21, 25, None],
        ["PURGE", 26, 30, None],
        ["Anti-Mutant", 31, 35, None],
        ["Frankenstein Destroyers", 36, 40, None],
        ["Corpore Metal", 41, 45, None],
        ["Spy for a Service Group", 46, 50, None],
        ["Romantics", 51, 55, None],
        ["Pro-Tech", 56, 60, None],
        ["Programs Group", 61, 65, None],
        ["Communists", 66, 70, None],
        ["Computer Phreaks", 71, 75, None],
        ["Illuminati", 76, 80, None],
        ["Free Enterprise", 81, 85, None],
        ["Death Leopard", 86, 90, None],
        ["Sierra Club", 91, 95, None],
        ["Other", 96, 100, None]
    ]
    
    # normal mutant powers, with category, die rolls and special rules
    # special rule 1: add another mutant power if this is the only one
    # special rule 2: roll an extraordinary mutant power
    NORMAL_MUTANT_POWERS = [
        ["Advanced Hearing", "biological", 1, 4, None],
        ["Advanced Vision", "biological", 5, 8, None],
        ["Advanced Touch", "biological", 9, 12, None],
        ["Advanced Taste", "biological", 13, 16, None],
        ["Advanced Smell", "biological", 17, 20, None],
        ["Superior Strength", "biological", 21, 24, None],
        ["Superior Agility", "biological", 25, 28, None],
        ["Superior Endurance", "biological", 29, 32, None],
        ["Superior Manual Dexterity", "biological", 33, 36, None],
        ["Superior Power Index", "biological", 37, 40, 1],
        ["Regeneration", "biological", 41, 44, None],
        ["Chameleon", "biological", 45, 48, None],
        ["Charm", "biological", 49, 52, None],
        ["Magnetosense", "biological", 53, 56, None],
        ["Superior Mechanical Aptitude", "mental", 56, 60, None],
        ["Superior Moxie", "mental", 61, 64, None],
        ["Superior Chutzpah", "mental", 65, 68, None],
        ["Combat Mind", "mental", 69, 72, None],
        ["Empathy", "mental", 73, 76, None],
        ["Mechanical Intuition", "mental", 77, 80, None],
        ["Telepathic Sense", "psionic", 81, 84, None],
        ["Mental Block", "psionic", 85, 88, None],
        ["Precognition", "psionic", 89, 92, None],
        ["Minor Telekinesis", "psionic", 93, 96, None],
        [None, None, 97, 100, 2]
    ]

    EXTRAORDINARY_MUTANT_POWERS = [
        ["Lung/Gill Adaptation", "biological", 1, 5, None],
        ["Matter Eater", "biological", 6, 10, None],
        ["Polymorphism", "biological", 11, 15, None],
        ["Adrenalin Control", "biological", 16, 20, None],
        ["Electroshock", "biological", 21, 25, None],
        ["Suspended Animation", "mental", 26, 30, None],
        ["Number Cruncher", "mental", 31, 35, None],
        ["Eidetic Memory", "mental", 36, 40, None],
        ["Suggestion", "mental", 41, 45, None],
        ["Machine Sense*", "mental", 45, 50, None],
        ["Paralyzer", "psionic", 51, 55, None],
        ["Trance Teleport", "psionic", 56, 60, None],
        ["Levitation", "psionic", 61, 65, None],
        ["Telepathic Projection", "psionic", 66, 70, None],
        ["Deep Probe", "psionic", 71, 75, None],
        ["Mental Blast", "psionic", 76, 80, None],
        ["Pyrokinesis", "psionic", 81, 85, None],
        ["Empathic Healing", "psionic", 86, 90, None],
        ["Machine Empathy*", "psionic", 91, 95, None],
        ["Luck", "psionic", 96, 100, None]
    ]

    MUTANT_REGISTRATION_CHANCE = 10

    MANDATORY_EQUIPMENT = [
        "red reflec armor",
        "laser pistol",
        "laser barrel (red stripe)",
        "jump suit",
        "utility belt & pouches",
        "Com Unit I",
        "knife",
        "notebook & stylus"]

    STARTING_CREDITS = 100

    OPTIONAL_EQUIPMENT = [
        ["flashlight", 10],
        ["hottorch", 100],
        ["gas mask", 50],
        ["SuperGum & solvent", 25],
        ["InfraSpecs (IR goggles)", 100],
        ["smoke alarm", 25],
        ["plasticord (25 feet)", 25],
        ["bullhorn", 50],
        ["picture of Teela-O-MLY-1", 5],
        ["nothing", 9999]  # just a placeholder to cut random selection short
                           # before character runs out of _credits
    ]

    # list of _skills used for building the skill tree
    # each skill is a list:
        # [_name, governing attribute, base level, parent skill]
    SKILLS = [
        ["Basics", None, 1, None],
        ["Personal Development", None, 1, None],
        ["Hostile Environments", None, 1, None],
        ["Vehicle Services", None, 1, None],
        ["Technical Services", None, 1, None],
        ["Melee Combat", "melee bonus", 2, "Basics"],
        ["sword", "melee bonus", 3, "Melee Combat"],
        ["knife", "melee bonus", 3, "Melee Combat"],
        ["truncheon", "melee bonus", 3, "Melee Combat"],
        ["neurowhip", "melee bonus", 3, "Melee Combat"],
        ["unarmed", "melee bonus", 3, "Melee Combat"],
        ["brass knuckles", "melee bonus", 3, "Melee Combat"],
        ["Weapon Maintenance", "repair bonus", 2, "Basics"],
        ["laser", "repair bonus", 3, "Weapon Maintenance"],
        ["projectile", "repair bonus", 3, "Weapon Maintenance"],
        ["energy", "repair bonus", 3, "Weapon Maintenance"],
        ["sonic", "repair bonus", 3, "Weapon Maintenance"],
        ["field", "repair bonus", 3, "Weapon Maintenance"],
        ["melee", "repair bonus", 3, "Weapon Maintenance"],
        ["Special Services", "comprehension bonus", 2, "Basics"],
        ["chemical weapons", "comprehension bonus", 3, "Special Services"],
        ["demolition", "comprehension bonus", 3, "Special Services"],
        ["medical", "comprehension bonus", 3, "Special Services"],
        ["surveillance", "comprehension bonus", 3, "Special Services"],
        ["security", "comprehension bonus", 3, "Special Services"],
        ["grenades", "comprehension bonus", 3, "Special Services"],
        ["Aimed Weapon Combat", "aimed weapon bonus", 2, "Basics"],
        ["Laser", "aimed weapon bonus", 3, "Aimed Weapon Combat"],
        ["pistol", "aimed weapon bonus", 4, "Laser"],
        ["rifle", "aimed weapon bonus", 4, "Laser"],
        ["Projectile", "aimed weapon bonus", 3, "Aimed Weapon Combat"],
        ["pistol", "aimed weapon bonus", 4, "Projectile"],
        ["autorifle", "aimed weapon bonus", 4, "Projectile"],
        ["conerifle", "aimed weapon bonus", 4, "Projectile"],
        ["icegun", "aimed weapon bonus", 4, "Projectile"],
        ["needlegun", "aimed weapon bonus", 4, "Projectile"],
        ["thrown knife", "aimed weapon bonus", 4, "Projectile"],
        ["Energy", "aimed weapon bonus", 3, "Aimed Weapon Combat"],
        ["pistol", "aimed weapon bonus", 4, "Energy"],
        ["rifle", "aimed weapon bonus", 4, "Energy"],
        ["Sonic", "aimed weapon bonus", 3, "Aimed Weapon Combat"],
        ["pistol", "aimed weapon bonus", 4, "Sonic"],
        ["rifle", "aimed weapon bonus", 4, "Sonic"],
        ["Field Weapons", "aimed weapon bonus", 3, "Aimed Weapon Combat"],
        ["flamethrower", "aimed weapon bonus", 4, "Field Weapons"],
        ["gauss gun", "aimed weapon bonus", 4, "Field Weapons"],
        ["tangler", "aimed weapon bonus", 4, "Field Weapons"],
        ["stun gun", "aimed weapon bonus", 4, "Field Weapons"],
        ["plasma rifle", "aimed weapon bonus", 4, "Field Weapons"],
        ["hand flamer", "aimed weapon bonus", 4, "Field Weapons"],
        ["Communications", "believability bonus", 2, "Personal Development"],
        ["intimidation", "believability bonus", 3, "Communications"],
        ["bootlicking", "believability bonus", 3, "Communications"],
        ["con", "believability bonus", 3, "Communications"],
        ["fast talk", "believability bonus", 3, "Communications"],
        ["oratory", "believability bonus", 3, "Communications"],
        ["spurious logic", "believability bonus", 3, "Communications"],
        ["Leadership", "believability bonus", 2, "Personal Development"],
        ["interrogation", "believability bonus", 3, "Leadership"],
        ["forgery", "believability bonus", 3, "Leadership"],
        ["bribery", "believability bonus", 3, "Leadership"],
        ["motivation", "believability bonus", 3, "Leadership"],
        ["psychescan", "believability bonus", 3, "Leadership"],
        ["Self-improvement", None, 2, "Personal Development"],
        ["endurance", None, 3, "Self-improvement"],
        ["strength", None, 3, "Self-improvement"],
        ["agility", None, 3, "Self-improvement"],
        ["manual dexterity", None, 3, "Self-improvement"],
        ["moxie", None, 3, "Self-improvement"],
        ["chutzpah", None, 3, "Self-improvement"],
        ["mechanical aptitude", None, 3, "Self-improvement"],
        ["Survival", "comprehension bonus", 2, "Hostile Environments"],
        ["identifying wild foods", "comprehension bonus", 3, "Survival"],
        ["eating wild foods", "comprehension bonus", 3, "Survival"],
        ["hunting, fishing, and gathering", "comprehension bonus", 3,
         "Survival"],
        ["trapping", "comprehension bonus", 3, "Survival"],
        ["Primitive Warfare", "comprehension bonus", 2, "Hostile Environments"],
        ["stealth", "comprehension bonus", 3, "Primitive Warfare"],
        ["ambush", "comprehension bonus", 3, "Primitive Warfare"],
        ["primitive melee weapons", "melee bonus", 3, "Primitive Warfare"],
        ["primitive aimed weapons", "aimed weapon bonus", 3,
         "Primitive Warfare"],
        ["Wild Lore", "comprehension bonus", 2, "Hostile Environments"],
        ["plant", "comprehension bonus", 3, "Wild Lore"],
        ["animal", "comprehension bonus", 3, "Wild Lore"],
        ["terrain", "comprehension bonus", 3, "Wild Lore"],
        ["weather", "comprehension bonus", 3, "Wild Lore"],
        ["Travel", "comprehension bonus", 2, "Hostile Environments"],
        ["tracking", "comprehension bonus", 3, "Travel"],
        ["orienteering", "comprehension bonus", 3, "Travel"],
        ["navigation", "comprehension bonus", 3, "Travel"],
        ["camping", "comprehension bonus", 3, "Travel"],
        ["mountain climbing", "comprehension bonus", 3, "Travel"],
        ["Vehicle Combat Weapons", "aimed weapon bonus", 2, "Vehicle Services"],
        ["Aimed Weapons", "aimed weapon bonus", 3, "Vehicle Combat Weapons"],
        ["laser cannon", "aimed weapon bonus", 4, "Aimed Weapons"],
        ["tube cannon", "aimed weapon bonus", 4, "Aimed Weapons"],
        ["sonic blaster", "aimed weapon bonus", 4, "Aimed Weapons"],
        ["wave-motion gun", "aimed weapon bonus", 4, "Aimed Weapons"],
        ["shock cannon", "aimed weapon bonus", 4, "Aimed Weapons"],
        ["fire-thrower", "aimed weapon bonus", 4, "Aimed Weapons"],
        ["anti-missile laser", "aimed weapon bonus", 4, "Aimed Weapons"],
        ["Launched Weapons", "aimed weapon bonus", 3, "Vehicle Combat Weapons"],
        ["drop tubes", "aimed weapon bonus", 4, "Launched Weapons"],
        ["missile racks", "aimed weapon bonus", 4, "Launched Weapons"],
        ["gas thrower", "aimed weapon bonus", 4, "Launched Weapons"],
        ["Field Weapons", "aimed weapon bonus", 3, "Vehicle Combat Weapons"],
        ["smoke generator", "aimed weapon bonus", 4, "Field Weapons"],
        ["chaff-caster", "aimed weapon bonus", 4, "Field Weapons"],
        ["gausser", "aimed weapon bonus", 4, "Field Weapons"],
        ["heat-masker", "aimed weapon bonus", 4, "Field Weapons"],
        ["radar-jammer", "aimed weapon bonus", 4, "Field Weapons"],
        ["ECM", "aimed weapon bonus", 4, "Field Weapons"],
        ["sonic shield", "aimed weapon bonus", 4, "Field Weapons"],
        ["sonic detector", "aimed weapon bonus", 4, "Field Weapons"],
        ["smoke generator", "aimed weapon bonus", 4, "Field Weapons"],
        ["Vehicle Maintenance", "repair bonus", 2, "Vehicle Services"],
        ["crawler", "repair bonus", 3, "Vehicle Maintenance"],
        ["autocar", "repair bonus", 3, "Vehicle Maintenance"],
        ["flybot", "repair bonus", 3, "Vehicle Maintenance"],
        ["hover", "repair bonus", 3, "Vehicle Maintenance"],
        ["copter", "repair bonus", 3, "Vehicle Maintenance"],
        ["vulture", "repair bonus", 3, "Vehicle Maintenance"],
        ["vehicle aimed weapons", "repair bonus", 3, "Vehicle Maintenance"],
        ["vehicle launched weapons", "repair bonus", 3, "Vehicle Maintenance"],
        ["vehicle field weapons", "repair bonus", 3, "Vehicle Maintenance"],
        ["Operation and Repair", "repair bonus", 2, "Vehicle Services"],
        ["crawler", "repair bonus", 3, "Operation and Repair"],
        ["autocar", "repair bonus", 3, "Operation and Repair"],
        ["hover", "repair bonus", 3, "Operation and Repair"],
        ["copter", "repair bonus", 3, "Operation and Repair"],
        ["vulture", "repair bonus", 3, "Operation and Repair"],
        ["Robotics", "repair bonus", 2, "Technical Services"],
        ["Operation", "repair bonus", 3, "Robotics"],
        ["docbot", "repair bonus", 4, "Operation"],
        ["jackobot", "repair bonus", 4, "Operation"],
        ["transbot", "repair bonus", 4, "Operation"],
        ["scrubot", "repair bonus", 4, "Operation"],
        ["trailbot", "repair bonus", 4, "Operation"],
        ["snooper", "repair bonus", 4, "Operation"],
        ["guardbot", "repair bonus", 4, "Operation"],
        ["flybot", "repair bonus", 4, "Operation"],
        ["Maintenance", "repair bonus", 3, "Robotics"],
        ["docbot", "repair bonus", 4, "Maintenance"],
        ["jackobot", "repair bonus", 4, "Maintenance"],
        ["transbot", "repair bonus", 4, "Maintenance"],
        ["scrubot", "repair bonus", 4, "Maintenance"],
        ["trailbot", "repair bonus", 4, "Maintenance"],
        ["snooper", "repair bonus", 4, "Maintenance"],
        ["guardbot", "repair bonus", 4, "Maintenance"],
        ["Computers", "comprehension bonus", 2, "Technical Services"],
        ["Computer Operation", "comprehension bonus", 3, "Computers"],
        ["information search", "comprehension bonus", 4, "Computer Operation"],
        ["analysis", "comprehension bonus", 4, "Computer Operation"],
        ["Computer Maintenance", "comprehension bonus", 3, "Computers"],
        ["Engineering", "comprehension bonus", 2, "Technical Services"],
        ["organic commodities", "comprehension bonus", 3, "Engineering"],
        ["industrial", "comprehension bonus", 3, "Engineering"],
        ["electronic", "comprehension bonus", 3, "Engineering"],
        ["mechanical", "comprehension bonus", 3, "Engineering"],
        ["civil", "comprehension bonus", 3, "Engineering"],
        ["chemical", "comprehension bonus", 3, "Engineering"],
        ["plastiforming", "comprehension bonus", 3, "Engineering"],
        ["communicationss", "comprehension bonus", 3, "Engineering"],
    ]

    TROUBLESHOOTER_SKILLS = [
        "Basics",
        "Aimed Weapon Combat",
        "Personal Development"
    ]

    SERVICE_GROUP_SKILL_COUNT = 2

    SERVICE_GROUP_SKILLS = {
        "Internal Security": ["Basics"],
        "Technical Services": ["Technical Services"],
        "HPD & Mind Control": ["Personal Development"],
        "Armed Forces": ["Basics", "Vehicle Services", "Hostile Environments"],
        "Production, Logistics and Commissary": ["Vehicle Services",
                                                 "Technical Services"],
        "Power Services": ["Vehicle Services", "Technical Services"],
        "Research and Design": ["Technical Services"],
        "Central Processing Unit": ["Basics", "Personal Development",
                                    "Hostile Environments", "Vehicle Services",
                                    "Technical Services"]
    }

    FREE_SKILL_COUNT = 1

def main():
    char = Character()
    char.print_character()

if __name__ == "__main__":
    main()
