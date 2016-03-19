# paranoiachargen
A script to generate characters for the first edition of the Paranoia RPG. 

## Requirements
* Python 3

## Features
* Creates first edition Paranoia characters
* Assigns random names based on US census data
* Calculates all secondary attributes, and applies them to relevant skills
* Boosts attributes based on mutant powers or skills, where applicable
* Output fits nicely on a single page of letter paper, in 12pt monospace text

## Usage
Run the character.py script in the Python interpreter installed on your system. In most cases, this will look something like this:

    python3 ./character.py
    
## Sample Output

    NAME                Ike-R-VZQ-1
    
    PRIMARY ATTRIBUTES                      SECONDARY ATTRIBUTES
    Strength             12                 Carrying Capacity    25kg
    Endurance            15                 Damage Bonus          0
    Agility              15                 Macho Bonus          -1
    Manual Dexterity      9                 Melee Bonus         +10%
    Moxie                16                 Aimed Weapon Bonus   -2%
    Chutzpah             15                 Comprehension Bonus +10%
    Mechanical Aptitude   8                 Believability Bonus +10%
    Power Index          10                 Repair Bonus         -3%
    
    SECURITY CLEARANCE  RED
    SERVICE GROUP       Internal Security
    SECRET SOCIETY      Programs Group, rank 1
    
    MUTANT POWERS
    Superior Moxie (mental)
    
    CREDITS              45
    
    EQUIPMENT
    red reflec armor                        laser pistol
    laser barrel (red stripe)               jump suit
    utility belt & pouches                  Com Unit I
    knife                                   notebook & stylus
    SuperGum & solvent                      smoke alarm
    picture of Teela-O-MLY-1
    
    WEAPONS
    laser pistol         23%
    knife (melee)        35%
    knife (thrown)       23%
    
    SKILLS
    Basics (1) - 20%/20%
        Melee Combat (2) - 25%/35%
        Weapon Maintenance (2) - 25%/22%
        Special Services (2) - 25%/35%
        Aimed Weapon Combat (2) - 25%/23%
    Personal Development (1) - 20%/20%

## Limitations
* For simplicity's sake, plasticord is purchased in 25 feet increments, rather than 1 foot per the Player's Guide
* Will not assign treasonous skills - again, this is per the Player's Guide
* Skills aren't assigned "intelligently", so generated characters may have useless skills, or skills with very low secondary attribute bonuses
