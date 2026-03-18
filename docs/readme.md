# Welcome to 2cc NML (Revival)

This project aims to capitalise on the work of Transportman, EmperorJake, VoyagerOne and the others mentioned further down in the original readme and better document, as well as extend the last "official" release, which was around 2020.
That said, I've not worked on NML files before and my gfx skills are zero so if people will desire extra amendments that involve say new params or new graphics, they'll need to help out with them.


## Availability

The grf file is available on Github under [Releases](https://github.com/nemethviktor/2ccts_revival/releases/latest) for the time being (scroll down to Assets and it should be there). If there is ample interest from people, I'll figure a way to push the files into the game's ecosystem.


## Build

The assumption is that you have at least a vague idea about how Linux works. If you're on Windows: Install WSL. It makes life a lot easier, don't bother with CoreUtils etc. 

Regardless you'll need to `apt install` a variety of things, `python3` and `pip3` obviously, `make`, `gcc`, `nmlc`, `dos2unix`

Then in `bash` (if you're on Windows, google around about this, but if you managed to get `apt` generally functioning this shouldn't be a problem) run `make`. If you get warnings that don't seem "deadly", ignore them, especially if you are new to this. 


## "Under new management" (project directions, bug reports/feature requests)

I forked the original project because I was unsatisfied with the availability of items past Gen5 wagons and so the original aim was to extend that. However of course I'm hoping to keep the project running and extend it where possible. Not only a fair bit of time has passed since the mid 2010s when this was active (and a lot of new real vehicles have come out) but I think there'd be significant scope for extending _concept_ vehicles for future purposes because I personally find it boring that there are almost no new vehicles in any NewGRF past ~2020
Please use github to submit requests of any kind, _don't use the OTTD forums_ - I'm not active there. Also preferably don't use Reddit, I'm a reader there but Github is easier to manage.


### Help wanted/Contributing

As I wrote above my GFX skills are zero so I'd like to ask people with graphics skills to chip in with the designs, either for new/concept vehicles or just changes to existing ones. 
Please try to either stick to whichever current template (none technically available as a PSD but if people need it then I can probably hack one from the existing PNG files). The code side of the graphics templates are in src/templates.pnml


## Info

(_I know this isn't actually self-replacing the variables._)

{{GRF_TITLE}}

MD5Hash:  {{GRF_MD5}}

Version:  {{REPO_REVISION}}

GRF ID:   "VN\01\01"



## Ye Olde Readme [by Transportman, pre-2026 with minor modifications as indicated]
### 1 About

2cc Trains In NML for OpenTTD. The set gives you trains from all over the world in 2cc.

### 2 General information

#### 2.1 Requirements

- OpenTTD 1.2.0-RC1 or nightly r23971, or higher
- Not compatible with TTDPatch

#### 2.2 Installation

OpenTTD: see https://wiki.openttd.org/en/Community/NewGRF/

Releases will be available from the ingame Online Content
	~~Nightlies/Push builds can be downloaded from http://bundles.openttdcoop.org/2ccts/~~ (Site dead as of 2026; use github)
	
#### 2.3 Parameter settings
 
 - *Cost Parameters*: With the cost parameters you can set purchase and running costs. You can set the costs to the following values:
	1/16x, 1/8x, 1/4x, 1/2x, 1x (default), 2x, 4x, 8x, 16x
 - *Concept Parameter*: This parameter allows you to disable conceptual	vehicles. By default the conceptual vehicles are enabled.
 - *Regional Parameters*: These parameters allow you to enable/disable vehicles from certain regions. The European subregions follow the EuroVOC subregions. By default, all regions are enabled. Disabling all regions will completely disable this NewGRF.
	
#### 2.4 Usage
 
 - *Starting date*: You can start as early as 1835.
 - *Metro vehicles* If there is no Metro track available, the Metro vehicles will use monorail as replacement, as this set does not define other vehicles for monorail.
 - *Multiple units*: With MUs you buy the front and back as dual headed train, and use Unit Wagons to get the consist length you want. You can chose between unpowered and powered unit wagons. The unpowered wagon weighs 50% of the engine, the	powered wagon weighs 75% of the engine and costs 50% more than the unpowered wagon.
    
### 3 Known issues

### 4 Background information

- This set is a recode to NML of the original 2cc TrainSet. Future versions will include new features.

### 5 Frequently Asked Questions

Q: How do Unit Wagons work?
A: With MUs you buy both heads, and then you can use the Unit Wagons to make the consist longer.

### 6 Credits

New graphics for this set:
- Voyager One

Graphics from the original 2cc Trainset:
- Emperor Jake
- Purno
- Voyager One
- DanMacK
- Colossal404
- trainboy2004
- uzurpator

Code:
- Transportman
- V Nemeth (2026 onwards)

Makefile system:
- planetmaker (Ingo von Borstel)

Special thanks to:
- Juzza1 for help with organizing the vehicle properties from the old set
- Valle for help with the properties of coaches and wagons
- All translators
- #openttdcoop for their work on the DevZone

### 7 Contact information
#### 7.1 Bug reports

Please report any bugs you find at the  
 - bug tracker: https://github.com/nemethviktor/2ccts_revival/issues  (2026 onwards -- please don't use OTTD forums!)
 - or discussions: https://github.com/nemethviktor/2ccts_revival/discussions  (2026 onwards -- please don't use OTTD forums!)

Always included a detailed description of the bug, preferably with
screenshot and savegame. Also state the exact game version you're using, 
as well as the version of this NewGRF.

If you have a savegame that includes NewGRFs not available on OpenTTD's 
Online Content, then please try to reproduce the bug in a new game 
which has all NewGRFs easily accessible.

If you're using a patched version of the game, please try to reproduce
the bug on an official game build. If you can't reproduce the bug, then
don't report it here but in the forum topic of the patch(pack) instead.

#### 7.2 Contributing
PRs are most welcome but please try to test. 

### 8 License

2cc Trains In NML
Copyright (C) 2014, 2026 2cc Trains In NML team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
