Please use the template examples in this folder otherwise I'll likely reject any new graphics. 
There are/were 50+ (!!!) different settings in the legacy file and I'd rather milk a cow than to have to debug them again with new stuff.

The automated process tags the Template ID onto each pnml file just under the copyright text so you can grab example templates if confused.

The obviously chaotic naming logic is a derivative of attempt to categorise existing legacy images into templates and then ending up with 40+ of them and then grouping the vaguely similar ones.

Most **Engines** _exc Steam_ will fall into `TPL_01`, whichever version of it. I'd suggest using `TPL_01A`; if your design is dual-headed, still use that, don't move any of the boxes. 

Most **xMUs** will be `TPL_02A` (There is no `TPL_02B` - it has been removed during testing). Some special **Long EMUs** go into `D` (long), `E` (very long), `F` (long and complex) but you'd better look up what you want at this point.

Most **Metros** will be `TPL_02C`.

**Things with Tenders [exc chickens]** are usually `TPL_03x`:
- Steam w / Tender -> `TPL_03A` 
- Items w 2 engine animation states -> `TPL_03B` 
- Same as B but different 'purhchase' position -> `TPL_03C` 
- Non-Steam w / Tender -> `TPL_03D` 
- Same as A but no Visual Effect -> `TPL_03E` 
- Same as B but no Visual effect -> `TPL_03F` 


For **Wagons**, it's a little chaotic because there are 'simple' (`TPL_01F`) ones with no loading states, then ones with liveries (`TPL_04A`) + loading states (`TPL_04B`) and ones _with liveries + loading states + different sprites per cargo type_ 
- Box Car Type 1 -> `TPL_04C` (but not Gen 2/3/4 Type 2)
- Box Car Type 2 -> `TPL_04D` (but not Gen 2/3/4 Type 2)
- Centerbeam -> `TPL_04E`
- Container-Carrier -> `TPL_04F`
- Container-Doublestack -> `TPL_04G`
- Hopper Types 1/2 -> `TPL_04H`
- Flatcar/Flat Wagon -> `TPL_04I`
- Tanker Non-2nd Gen -> `TPL_04J`
- Tanker 2nd Gen -> `TPL_04K`
- Open Wagon Gen2/Gen3 -> `TPL_04L` - This has 'Driving State' for GRAIN only
- Box Car Gen3/4 Type 2 -> `TPL_04M`
- Gondola -> `TPL_04N` - This has 'Driving State' for GRAIN only
- Heavy Flatcar -> `TPL_04O`
- Box Car Gen2 Type 2 -> `TPL_04P`
- Superheavy -> `TPL_25` - [not 04x] This has Front/Back/Middle/Articulated + Loading states
- Open Wagon Gen1 -> `TPL_04Q`
- Service Cars -> `TPL_04R`
- DC/Push-Pull -> `TPL_04S`
- Livestock _only_ wagon -> `TPL_04T`

Basically don't create new types of Wagons. At the moment Gen 6/7 uses G5 graphics, it'd be awesome if someone updated those but don't reinvent the wheel please.

**Coaches** are `TPL_04A` - Unless you want loading states like the Indian whichever coach that has people hanging on it when full - that's `TPL_04B`.

Vehicles with **12 length** use `TPL_016`.
Vehicles with **10 length** use `TPL_032` - use `A` for no animation and `B` for with animation. `C` is the same as `B` but has `length` added to the visualisation switch.


Things with **front and back but no livery or loading states** use `TPL_017A`. 
- For **A/B Front/Back** it's `TPL_017B`
- For **Front 1, Front 2, Middle, Back 1, Back 2** it's `TPL_017C`.
- For **Front 1, Front 2, Middle 1, Middle 2, Back 1, Back 2** it's `TPL_017D`.
- For **Front 1, Front 2, Back 1, Back 2** it's `TPL_017E`.

**CargoDMU** is `TPL_042A` - that's the only vehicle there.

I'd suggest not producing more of them though, it's a little too complex.


You may ofc put your logo or text or palette on the file(s) but don't move the template boxes.