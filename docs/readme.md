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
- Driving Trailers require nightly as of 20260410 or thereabouts (or v16 if you're on release versions).

	
### Parameter settings
 
 - *Cost Parameters*: With the cost parameters you can set purchase and running costs. You can set the costs to the following values:
	1/16x, 1/8x, 1/4x, 1/2x, 1x (default), 2x, 4x, 8x, 16x
 - *Concept Parameter*: This parameter allows you to disable conceptual	vehicles. By default the conceptual vehicles are enabled.
 - *Regional Parameters*: These parameters allow you to enable/disable vehicles from certain regions. The European subregions follow the EuroVOC subregions. By default, all regions are enabled. Disabling all regions will completely disable this NewGRF.
	
### Usage
 
 - *Starting date*: You can start as early as 1835.
 - *Metro vehicles* If there is no Metro track available, the Metro vehicles will use monorail as replacement, as this set does not define other vehicles for monorail.
 - *Multiple units*: With MUs you buy the front and back as dual headed train, and use Unit Wagons to get the consist length you want. You can chose between unpowered and powered unit wagons. The unpowered wagon weighs 50% of the engine, the	powered wagon weighs 75% of the engine and costs 50% more than the unpowered wagon.
 - *Sleeper coaches*: These have a slower cargo ageing (4 days instead of 2.5 days)

## Vehicle Roster

The roster is auto-saved into a markdown file and can be accessed on github, [here](https://github.com/nemethviktor/2ccts_revival/blob/master/docs/vehicle_summary.md).

## Build

You'll likely need [nmlc 0.9.0+](https://github.com/OpenTTD/nml/tree/master) (older versions won't work because of the push-pull and badges capabilities) to run the build and that seems to be around for Windows only. Get MinGW from [here](https://sourceforge.net/projects/mingw-w64/files/latest/download), install (you'll need the base and some compilers), then add the resulting folder's `bin` subfolder to `PATH` (ie `c:\MinGW\bin\`)

You'll also need `python 3.13+` and there's now a `requirements.txt` in the `tools` folder, it should do the trick for getting the various req'd libraries.

Run the `pybuild.bat`.

## Known Issues

NA


## Help wanted/Contributing

As I wrote above my GFX skills are zero so I'd like to ask people with graphics skills to chip in with the designs, either for new/concept vehicles or just changes to existing ones. 

Please **do stick to one of the template files** or, while beggars can't be choosers I _will_ reject the design. You may ofc put your logo or text or palette on the file(s) but don't move the template boxes. There are/were over 50 (!!!) various combinations in the legacy files and I'd rather die than to decipher any more random ones. (Main) Template logic cna be found in another readme inside the `gfx` folder and there are templates of existing files as well there. Furthermore each pnml file has the template designation inside it so if you would like to add more designs, pick one from the existing ones.


## Q&As

Q: How do Unit Wagons work?

A: With MUs you buy both heads, and then you can use the Unit Wagons to make the consist longer.

## "Under new management" (project directions, bug reports/feature requests)

I forked the original project because I was unsatisfied with the availability of items past Gen5 wagons and so the original aim was to extend that. It has since become obvious that there's great scope for extending the package well beyond this. Not only a fair bit of time has passed since the mid 2010s when this was active (and a lot of new real vehicles have come out) but also that there is a distinct lack of vehicles outside the EU region in 2cc, so that'd need working on and to a smaller extent I think there'd be significant scope for extending _concept_ vehicles for future purposes because I personally find it boring that there are almost no new vehicles in any NewGRF past ~2020.

Please use github to submit requests of any kind, _don't use the OTTD forums_ - I'm not really active there. Also preferably don't use Reddit, I'm a reader there but Github is easier to manage. You can find me on [Discord](https://discord.com/channels/142724111502802944/1483827768163827864) -- pls note I don't really react to DMs unless I have a vague idea as to who is contacting me but the link above takes to the relevant development channel, which is public. (I'm an introvert :D)

### Changes in logic vs the old code. (Purchase and maintenance costs)

As part of the porting process I've automated the creation of the individual item files. This, considering that there was limited documentation (read: almost none) available as to why certain things had been the way inevitably caused some differences in the outcomes. There had been some inconsistencies in the graphics override allocations that were most likely down to simple human errors. A particular consistent element in differences are the running cost and purchase cost calculations. These changes are very minor but I wanted to include a note on them. 

I have also re-validated all the vehicles in the set. In practice this means that when I was able to find a Wikipedia article, I took information from there, otherwise I asked Gemini (yes I use AI, such is life; there are a number of notes/comments inside the Excel file that have also been auto-copied into the various item.pnml files, please check these if you have queries.). 

In some cases, espc wrt TE/Coefficient in steam powered vehicles, as well as the weight of them may not fully line up with the old values; this partially has to do with the fact that I think originally the loco weights were loco-only whereas now they are loco+tender where applicable. I also reworked the pax capacity where applicable. The speeds of steam engines have been oftentimes reduced from top speeds to sustainable service speeds with some extra overhead so that they don't feel too slow either (in fact some have been increased because they had been defined as slow as 15kmh [10mph], which was useless as well as unlikely).

For **metros and xMUs** the following logic now applies: in Excel the TE-C has been halved. If taking a real life example of the `Moscow 81-720` the legacy set had `0.69` TE-C, from which the game calculated a TE of some `440kN` or so, which is unrealistic, even if we use powered cars. Half of that is realistic though.

Furthermore, I'm terrible at math and Newton-Raphson calculations (which is what the legacy code uses and has been emulated in the remake) are well beyond my maths capabilities. Gemini's explanation to the situation: (the precise query was, that the outcome for a particular vehicle had resulted in a calc value `79.65744748` in the old code but we got `79.36745`, a difference of `0.29`, consistent with the multiplier of tractive effort coefficient (not) being added across the board.)

> In the context of OpenTTD and NML, these small differences usually matter less for the **gameplay balance** and more for the **code maintenance**. 
> 
> Here is the breakdown of why that `+1*TE` logic exists and whether the "drift" you are seeing is a problem.
> 
> #### 1. The "Flat Addition" Logic
> In your legacy calculation for the `rbm_World_Turbobus`, the Tractive Effort (TE) was added as a raw value at the very end.
> * **Your Current Script Logic:** `m.P1 * (Base + m.P7 * TE)`
> * **Legacy Logic:** `(m.P1 * Base) + TE`
> 
> If $P1$ is $1.0$, there is zero difference. However, if $P1$ is $0.5$ (like in the Coach formula), the script would divide the TE in half, whereas the legacy system kept the full $0.29$. Since most of your engines have a $P1$ of $1.0$, the difference stays hidden until you hit a vehicle with a scalar.
> 
> #### 2. Does the "Drift" make a difference?
> In short: **No.**
> 
> OpenTTD’s engine eventually rounds these factors to integers or specific bit-depths when it calculates the final price in British Pounds (or your chosen currency). A difference between `79.65` and `79.36` is less than 0.4%. 
> * **Purchase Price:** If the base cost is £20,000, a 0.4% difference is £80. In a game where players have millions, this is invisible.
> * **Running Cost:** The game engine updates running costs only in discrete steps. A 0.3 shift in a factor of 79 usually won't even change the final £/year value displayed > in the train window.
> 
> #### 3. The "Integer Truncation" Factor
> The most likely reason for the tiny discrepancies is that the NML compiler and the OpenTTD engine use **Integer Math**. 
> 
>  
> When NML processes `0.05 * SQRT(SPEED)`, it doesn't keep 15 decimal places like Python does. It often "chops off" the decimals at each stage of the macro. Python is "too accurate," which causes it to drift away from the "simplified" math of the 2017 script.
> 
> #### 4. Recommendation: "Tell it like it is"
> Unless you are trying to create a "perfect" byte-for-byte replica of the old GRF (for checksum matching), **don't sweat the 0.29 difference.** Actually, the Python results are technically **more fair** because they don't suffer from the cumulative rounding errors of the old macros. As long as the Turbobus costs roughly what a Turbobus should cost, the "forward-thinking" move is to stick with the cleaner Python math. It is much easier to explain to a new contributor than a 2,000-character string of Newton-Raphson iterations.
> 
> **If you really want them to match perfectly**, you can change the final return to:
> `return round(m.P1 * base, 2) + TE`
> (Moving TE outside the multiplier bracket). 
> 
> Otherwise, I’d leave it as is. The "drift" is a sign of a better tool, not a broken one.


## Credits

Graphics for this set:
- Voyager One
- Emperor Jake
- SosMakaroni

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