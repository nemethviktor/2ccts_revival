# Welcome to 2cc NML (Revival)

This project aims to capitalise on the work of Transportman, EmperorJake, VoyagerOne and the others mentioned further down in the original readme and better document, as well as extend the last "official" release, which was around 2020.

There is now added support for various track types and voltages as well as badges. There is also support for push-pull and a small number of vehicles have been added.
What I currently need help with is for people to use the badge filters to see where we have gaps (mostly plenty of said gaps outside Europe) and suggest specific vehicles to add and preferably either provide the sprites or tell me what existing sprite they look similar to so I can clone. I'm extremely bad at drawing and have zero sense of spatial perspective.

## Availability

The grf file is available on Github under [Releases](https://github.com/nemethviktor/2ccts_revival/releases/latest) for the time being (scroll down to Assets and it should be there). If there is ample interest from people, I'll figure a way to push the files into the game's ecosystem.

There is a nightly of sorts on my [Google Drive](https://drive.google.com/file/d/15M6hdWmnYQWlgP0Xh-UZbEimmLge4TZk/view?usp=drive_link) - whenever I compile the file locally on my laptop it gets copied there but it may or may not be buggy.

## General information

### Requirements

- OpenTTD 1.2.0-RC1 or nightly r23971, or higher
- Not compatible with TTDPatch
- Badges require OpenTTD v15
- Driving Trailers require nightly as of mid April 2026 or thereabouts (or v16 if you're on release versions)
- Please note that the 'revival' newgrf is not backwards compatible with the original 2cc trains newgrf so you can't hot-swap it in savegames

### Parameter settings

- *Cost Parameters*: With the cost parameters you can set purchase and running costs. You can set the costs to the following values:
 1/16x, 1/8x, 1/4x, 1/2x, 1x (default), 2x, 4x, 8x, 16x
- *Concept Parameter*: This parameter allows you to disable conceptual vehicles. By default the conceptual vehicles are enabled.
- *Regional Parameters*: These parameters allow you to enable/disable vehicles from certain regions. The European subregions follow the EuroVOC subregions. By default, all regions are enabled. Disabling all regions will completely disable this NewGRF.

### Usage

- *Starting date*: You can start as early as 1835.
- *Metro vehicles* If there is no Metro track available, the Metro vehicles will use monorail as replacement, as this set does not define other vehicles for monorail.
- *Multiple units*: With MUs you buy the front and back as dual headed train, and use Unit Wagons to get the consist length you want. You can chose between unpowered andpowered unit wagons. The unpowered wagon weighs 50% of the engine, the powered wagon weighs 75% of the engine and costs 50% more than the unpowered wagon.
- *Sleeper coaches*: These have a slower cargo ageing (4 days instead of 2.5 days)
- *Model life*:
  - Powered/Unpowered (MU carriages): *never expire*
  - Intro year >= 1995: *never expire*
  - Wagons/Coaches: 70 years
  - Anything else: 45 years
- *Vehicle life*:
  - Powered/Unpowered (MU carriages): 25 years
  - Wagons/Coaches: 25 years
  - Metro of any type: 50 years
  - Intro year < 1900: 15 years
  - Intro year < 1950: 30 years
  - Intro year < 2000: 40 years
  - Anything else: 45 years

## Vehicle Roster

The roster is auto-saved into a markdown file and can be accessed on github, [here](https://github.com/nemethviktor/2ccts_revival/blob/master/docs/vehicle_summary.md).

## Build

You'll need [nmlc 0.9.0+](https://github.com/OpenTTD/nml/tree/master) (older versions won't work because of the push-pull and badges capabilities) to run the build and that seems to be around for Windows only. Get MinGW from [here](https://sourceforge.net/projects/mingw-w64/files/latest/download), install (you'll need the base and some compilers), then add the resulting folder's `bin` subfolder to `PATH` (ie `c:\MinGW\bin\`)

You'll also need `python 3.13+` and there's now a `requirements.txt` in the `tools` folder, it should do the trick for getting the various req'd libraries.

Run the `pybuild.bat`.

## Known Issues

Wagon attach rules don't work. Basically everything is allowed.

## Help wanted/Contributing

As I wrote above my GFX skills are zero so I'd like to ask people with graphics skills to chip in with the designs, either for new/concept vehicles or just changes to existing ones.

Please **do stick to one of the template files** or, while beggars can't be choosers I *will* reject the design. You may ofc put your logo or text or palette on the file(s) but don't move the template boxes. There are/were over 50 (!!!) various combinations in the legacy files and I'd rather die than to decipher any more random ones. (Main) Template logic can be found in another readme inside the `gfx` folder and there are templates of existing files as well there. Furthermore each pnml file has the template designation inside it so if you would like to add more designs, pick one from the existing ones.

## Q&As

Q: How do Unit Wagons work?

A: With MUs you buy both heads, and then you can use the Unit Wagons to make the consist longer.

## "Under new management" (project directions, bug reports/feature requests)

I forked the original project because I was unsatisfied with the availability of items past Gen5 wagons and so the original aim was to extend that. It has since become obvious that there's great scope for extending the package well beyond this. Not only a fair bit of time has passed since the mid 2010s when this was active (and a lot of new real vehicles have come out) but also that there is a distinct lack of vehicles outside the EU region in 2cc, so that'd need working on and to a smaller extent I think there'd be significant scope for extending *concept* vehicles for future purposes because I personally find it boring that there are almost no new vehicles in any NewGRF past ~2020.

Please use github to submit requests of any kind, *don't use the OTTD forums* - I'm not really active there. Also preferably don't use Reddit, I'm a reader there but Github is easier to manage. You can find me on [Discord](https://discord.com/channels/142724111502802944/1483827768163827864) -- pls note I don't really react to DMs unless I have a vague idea as to who is contacting me but the link above takes to the relevant development channel, which is public. (I'm an introvert :D)

### Differences from the original 2cc set

The below is a causal and incomplete blurb of some of the differences between the old and new set:

- Most vehicles' data has been rechecked and adjusted, which also means their costs will have changed. Obviously new vehicles have been added.
- MU wagons can no longer take `valuables`. It's illogical and is a cheat that the player can have valuables speeding around at 400kmh while the actual fastest wagon for it is limited to ~160kmh or so.
- Livestock vans have been separated out and the various wagons' cargo defintions have been revamped.
- Almost everything has been standardised in code and templates, this corrects a lot of generic bugs from the original setup that are too numerous to list individually.
- Rail types have been added as well as voltages, badges, etc.
- Maglev(s) for cargo purposes have been introduced. The semi-plural is because there's only one at the moment and the relevant graphics are a copypaste of `Taurus` and `gen5` but at least there is _something_.

## Credits

Graphics for this set:

- Voyager One
- Emperor Jake
- SosMakaroni
- Ragin

Graphics from the original 2cc Trainset:

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

## Contact information

### Bug reports

Please report any bugs you find at the  

- bug tracker: <https://github.com/nemethviktor/2ccts_revival/issues>  (2026 onwards -- please don't use OTTD forums!)
- or discussions: <https://github.com/nemethviktor/2ccts_revival/discussions>  (2026 onwards -- please don't use OTTD forums!)

Always included a detailed description of the bug, preferably with
screenshot and savegame. Also state the exact game version you're using,
as well as the version of this NewGRF.

If you have a savegame that includes NewGRFs not available on OpenTTD's
Online Content, then please try to reproduce the bug in a new game
which has all NewGRFs easily accessible.

If you're using a patched version of the game, please try to reproduce
the bug on an official game build. If you can't reproduce the bug, then
don't report it here but in the forum topic of the patch(pack) instead.

### Contributing

PRs are most welcome but please try to test.

## License

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
