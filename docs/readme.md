# Welcome to 2cc Trains In NML (Revival)

This project aims to capitalise on the work of Transportman, EmperorJake, VoyagerOne and the others mentioned further down in the original readme and better document, as well as extend the last "official" release, which was around 2020.

There is now added support for various track types and voltages as well as badges. There is also support for push-pull and for the initial release, some 200+ vehicles have been added. See further below for more on this.

We now have maglev cargo capability but the Gen7 wagons use the Gen5 designs. (There's also Gen6, which are visually also identical to G5 but are ... better).

## Availability

The grf file is now available [Bananas](https://bananas.openttd.org/package/newgrf/564e0101) as well as on Github under [Releases](https://github.com/nemethviktor/2ccts_revival/releases/latest) (scroll down to Assets and it should be there). 

There is a nightly of sorts on my [Google Drive](https://drive.google.com/file/d/15M6hdWmnYQWlgP0Xh-UZbEimmLge4TZk/view?usp=drive_link) - whenever I compile the file locally on my laptop it gets copied there but it may or may not be buggy.

## General information

### Requirements

- OpenTTD 1.2.0-RC1 or nightly r23971, or higher
- Not compatible with TTDPatch
- Badges require OpenTTD v15
- Driving Trailers require v16 (at least beta thereof)
- Please note that the 'revival' newgrf is not backwards compatible with the original 2cc trains newgrf so you can't hot-swap it in savegames
  - Technically it is possible but it's a major PITA. You'd want to send all your trains to depot (otherwise they'll be stuck perma-unmovably on the tracks), preferably use JGRPP and Template replacements, swap the grf, (re)define templates and then manually clone the vehicles to the new templates. It's doable, I tried it, but mightily unpractical.
  - If you are still interested, here's a video of one of my longplay map conversions -> https://youtu.be/Qijxcduf4as

### Parameter settings

- *Cost Parameters*: With the cost parameters you can set purchase and running costs. You can set the costs to the following values:
 1/16x, 1/8x, 1/4x, 1/2x, 1x (default), 2x, 4x, 8x, 16x
- *Concept Parameter*: This parameter allows you to disable conceptual vehicles. By default the conceptual vehicles are enabled.
- *Regional Parameters*: These parameters allow you to enable/disable vehicles from certain regions. The European subregions follow the EuroVOC subregions. By default, all regions are enabled. Disabling all regions will completely disable this NewGRF.

### Usage

- *Starting date*: You can start as early as 1835, subject to region.
- *Metro vehicles* If there is no Metro track available, the Metro vehicles will use monorail as replacement, as this set does not define other vehicles for monorail.
- *Multiple units*: With MUs you buy the front and back as dual headed train, and use Unit Wagons to get the consist length you want. You can chose between unpowered andpowered unit wagons. The unpowered wagon weighs 50% of the engine, the powered wagon weighs 75% of the engine and costs 50% more than the unpowered wagon.
- *Sleeper coaches*: These have a slower cargo ageing (4 days instead of 2.5 days)
- *Model life*:
  - Powered/Unpowered (MU carriages): *never expire*
  - Intro year >= 1990: *never expire*
  - Wagons/Coaches: 70 years
  - Anything else: 45 years
- *Vehicle life*:
  - Powered/Unpowered (MU carriages): 25 years
  - Wagons/Coaches: 25 years
  - If real-life withdrawal known, use that subject to a minimum described below
  - Metro of any type: 50 years
  - Intro year < 1950: 30 years
  - Intro year < 2000: 40 years
  - Anything else: 45 years

## Vehicle Roster & Gap Analysis

The roster is auto-saved into a markdown file and can be accessed [on github](https://github.com/nemethviktor/2ccts_revival/blob/master/docs/vehicle_summary.md).

A visual gap analysis is also [on github](https://github.com/nemethviktor/2ccts_revival/blob/master/docs/vehicle_gap_analysis.md). (representing the count of vehicles available per region per role...or the lack of them)

If so inclined to get a more readable version of the image above, poke the relevant py file and change the `target_categories` inside to what you are interested in..

## Build

You'll need [nmlc 0.9.0+](https://github.com/OpenTTD/nml/tree/master) (older versions won't work because of the push-pull and badges capabilities) to run the build and that seems to be around for Windows only. Get MinGW from [sourceforge](https://sourceforge.net/projects/mingw-w64/files/latest/download), install (you'll need the base and some compilers), then add the resulting folder's `bin` subfolder to `PATH` (ie `c:\MinGW\bin\`)

You'll also need `python 3.13+` and there's now a `requirements.txt` in the `tools` folder, it should do the trick for getting the various req'd libraries.

Run the `pybuild.bat`.

## Known Issues

NA

## Help wanted/Contributing

My GFX skills are zero so I'd like to ask people with graphics skills to chip in with the designs, either for new real and concept vehicles or just changes to existing ones. Using the badges filters or just the charts referenced above are great ways to figure what regions and roles are lacking.

Please **do stick to one of the template files** or, while beggars can't be choosers I *will* reject the design. You may ofc put your logo or text or palette on the file(s) but don't move the template boxes. There are/were over 50 (!!!) various combinations in the legacy files and I'd rather die than to decipher any more random ones. (Main) Template logic can be found in another readme inside the `gfx` folder and there are templates of existing files as well there. Furthermore each pnml file has the template designation inside it so if you would like to add more designs, pick one from the existing ones.

## Q&As

Q: How do Unit Wagons work?

A: With MUs you buy both heads, and then you can use the Unit Wagons to make the consist longer.

Q: Can I haz ~~cheeseburger~~ multisystem locos whose power and speed details depend on what voltage-track they are on?

A: No. While MS locos do exist in the set and their tracktypes are defined properly, each speed/power output setting would require individual `switch` (aka if-then) statments in code. We have some 15 partially overlapping railtypes defined and each of those would require a separate `switch` statement in the nml code. There are around 15-20 vehicles in the set where this would be applicable and only a handful of those would have values differing enough to make real difference in speed or performances when running on DC power. With "OHLE" being a generic "any" track type compatibility flag generating these `switch`es in a reliable way would be a major pain in the backside even when using AI (which is not that great at this stuff) so, sorry, nope.
For Dual-Mode locos the functionality exists and works because there's only one `switch` that depends whether the current track is a fallback to `ELRL` or not, that simple.

## "Under new management" (project directions, bug reports/feature requests)

I forked the original project because I was unsatisfied with the availability of items past Gen5 wagons and so the original aim was to extend that. It has since become obvious that there's great scope for extending the package well beyond this. Not only a fair bit of time has passed since the mid 2010s when this was active (and a lot of new real vehicles have come out) but also that there is a distinct lack of vehicles outside the EU region in 2cc, so that'd need working on and to a smaller extent I think there'd be significant scope for extending *concept* vehicles for future purposes because I personally find it boring that there are almost no new vehicles in any NewGRF past ~2020.

Please use github to submit requests of any kind, *don't use the OTTD forums* - I'm not really active there. Also preferably don't use Reddit, I'm a reader there but Github is easier to manage. You can find me on [Discord](https://discord.com/channels/142724111502802944/1483827768163827864) -- pls note I don't really react to DMs unless I have a vague idea as to who is contacting me but the link above takes to the relevant development channel, which is public. (I'm an introvert :D)

### Differences from the original 2cc set

The below is a causal and incomplete blurb of some of the differences between the old and new set:

- Most vehicles' data has been rechecked and adjusted, which also means their costs will have changed. Obviously new vehicles have been added.
- All vehicles have been renamed to manufacturers' designation(s), countries removed and regions extended. The idea is that for example what used to be `(China) MTR 8000` is in fact a `Siemens ER20`, which is widely avaialble. It'd thus be 'odd' to have the "MTR" avaialble in places thousands of miles away from Hong Kong.
- Some mathematical formulae have been updated to use python libraries rather than extremely obscure calculations that generally yielded the same values (particular about square roots)
- MU wagons can no longer take `valuables`. It's illogical and is a cheat that the player can have valuables speeding around at 400kmh while the actual fastest wagon for it is limited to ~160kmh or so.
- `SuperHeavy` is now restricted to `Goods` and `Vehicles` only.
- Livestock vans have been separated out and the various wagons' cargo defintions have been revamped.
- Almost everything has been standardised in code and templates, this corrects a lot of generic bugs from the original setup that are too numerous to list individually.
- Rail types have been added as well as voltages, badges, etc.
- Maglev(s) for cargo purposes have been introduced.
- Dual-mode locos are avaiable.

#### Running Cost Changes (V4.1 onwards)

Running costs of any item in the set is made up of a complex mathematical formula that was part of the original legacy release. It has 6 components and are affected by a base scale value that's different by category and also by weight, speed, power and an arbitrary complexity value. 

In the legacy set the running costs variables were identical for both steam, diesel and electric, which was silly because IRL they aren't the same to run, steam is a lot more complex/expensive etc. There was also a huge logical flaw wrt the running costs the so-called "powered/unpowered multi-unit" items that need to be attached to xMUs, which have now been corrected. As such the following balancing on running costs has been affected:
- `Steam engines & railbuses`: a lot more expensive
- `Diesel engines & railbuses`: somewhat more expensive
- `Electric engines & railbuses`: somewhat more expensive
- `Maglev engines & railbuses`: somewhat more expensive
- `Dual-powered (diesel & electric)`: are dependent on the type of rail they are running on at any given moment.
- `Multiple unit heads`: same as their type above except maglev, where the 'base scale' has been reduced because IRL the attached carriages are similar power than the heads; see below.
- `Coaches`: somewhat cheaper
- `Wagons`: a lot cheaper - IRL their running costs are negligible compared to that of a loco whereas in the legacy set they were comparable in costs.
- `Powered/unpowered multi unit wagon/coach`: use a different calculation logic but have been made very significatly cheaper than before, except Maglev, which are a bit less cheap than the rest.

There are still the overall parameter switches you can change to apply a multiplier to the whole set should you want to.
The overall effect is a reduction of running costs, but obviously the more wagons/carriages you have the more pronounced this will be.

## Credits

Graphics for this set:

- Voyager One
- Emperor Jake
- SosMakaroni
- Ragin
- Pitagoras991
- Some of the power badges are from the `8bit badge set (by Althonos)`

Graphics from the original 2cc Trainset:

- Purno
- Voyager One
- DanMacK
- Colossal404
- trainboy2004
- uzurpator

Code:

- Transportman (original 2cc)
- V Nemeth (2026 onwards)

Makefile system:

- planetmaker (Ingo von Borstel)

Special thanks to:

- Juzza1 for help with organizing the vehicle properties from the old set
- Valle for help with the properties of coaches and wagons
- All translators
- #openttdcoop for their work on the DevZone
- Pitagoras991 on Discord for their knowledge on various items

## Contact information

### Bug reports

Please report any bugs you find at the [bug tracker](https://github.com/nemethviktor/2ccts_revival/issues) or poke me on Discord.

### Contributing

Since the database for the vehicles is stored in an Excel file that has a fair bit of complexity I'd ask people not to do a PR but instead ping me somewhere (open a ticket on Github, find me on Discord) and we can discuss ideas.

If you're designing graphics for new vehicles please use one of the templates, all of which can be found in the gfx/templates folder. Futhermore there is a flowchart and explanation [here](https://github.com/nemethviktor/2ccts_revival/tree/master/gfx) as to what template applies to what vehicle type.

## License

2cc Trains In NML (Revival)
Copyright (C) 2014, 2026 2cc Trains In NML (Revival) team

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program; if not, write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

As an amendment, some graphics are CC-BY-NC-SA; these are indicated accordingly.