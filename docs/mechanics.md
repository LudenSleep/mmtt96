# Game mechanics of Micro Machines Turbo Tournament 96 (Mega Drive, Europe v1.1)

Purpose: a complete, plain-English account of how every game system behaves, precise enough to replicate the
mechanics exactly, with each statement tied to the evidence that supports it. Locating tasks (plan 1.9 T5-T10) find
the code and RAM behind each system; group closes (T13-T23) complete the sections. Meaning names in
`config/names/*.tsv` are assigned only from a confirmed claim here or from >= 3 datapoints.

Line grammar: every `- ` bullet under a `## ` or `### ` heading is one claim and ends with a marker:

```
- <claim in plain English, measured quantities with units> [confirmed: <ptr>, <ptr>, ...]
- <claim or open question> [hypothesis: <ptr>, ...]
- <open question, no evidence yet> [hypothesis]
```

A pointer is a region id (`config/regions.retail.tsv`), a RAM, routine or hardware name (`config/names/ram.tsv`,
`routines.tsv`, `hw.tsv`), a struct or `struct.field` (`structs.tsv`), a probe id `P<nnn>`
(`config/oracle/probes.tsv`), a run id `<tag>_<YYYYMMDD>T<HHMMSS>` of `config/oracle/*.tsv`, or a tracked file path.
`confirmed` needs >= 3 distinct run ids or one probe of kind `controlled`; anything less is a `hypothesis`.
Checked by `scripts/census/commentcheck.py --doc docs/mechanics.md` (in `scripts/census/wave_gate.sh`). Prose
paragraphs and tables are not checked; claims belong in bullets. Addresses in prose are ROM writer pcs or work RAM
addresses already tracked elsewhere.

Firewall (G12): this doc holds plain-English behaviour prose and measured quantities only (frames, pixels, speeds,
counts, ranges, tables of measured values). Never instruction text, bytes, mnemonic skeletons, verbatim ROM tables,
track layouts or screenshots.

## Contents

Sections in document order. (A numbered list, so that it is not read as claims.)

1. Overview
2. Glossary
3. Names to know
4. Group 1, view and scrolling: View and scrolling; Pool-table levels and the mini-micro question
5. Group 2, rules: Scoring and win condition; Out-of-view scoring; Tie-break playoff; Race start and finish; Difficulty
6. Group 3, course: Track boundary and out-of-bounds; Lap detection and checkpoints; Ramps and airborne; Pickups and hazards
7. Group 4, collisions: Car-to-car collisions; Collision areas (hitbox); Bounce and impulse response
8. Group 5, vehicle handling: Acceleration; Top speed; Braking; Steering; Drift and traction; Vehicle types; Opponent AI;
   Input and J-Cart four-player
9. Group 6, data: How a course fits together; Level data and loading; Construction kit and saved tracks; Vehicle and
   track tables; Sound cues
10. Group 7, the rest: Menus and game modes; Sound driver and music; Attract mode; Effects; Other findings

## Overview

This page sums up the sections below in plain words; each section holds the claims and the evidence behind them. A
statement here is only as firm as the claims it rests on. Most claims in the document are still hypotheses; the
confirmed ones (three or more recorded runs, or one controlled probe) sit mainly in the view, rules, course, collision,
handling and level-loading sections. Menus, the sound driver and music, attract mode and effects are still mostly open.

View (group 1). The screen shows a view onto the level that follows the player's car, or the midpoint of the cars when
two or four play; it stops at the edges of the stage and the whole screen scrolls as one piece. No separate object
steers the view: the scroll is worked out from the cars' positions every frame. Pool Slalom is drawn at half scale,
the view moving half as far for each move of a car, and one per-course switch turns that mode on. The Mega Drive has
no scaling hardware, so the look comes from half-size art and scroll, not from a zoom.

Rules (group 2). A head-to-head match is scored on a column of eight lights that starts at four; each point moves one
light, and the match ends when a player reaches the end. A point is scored when player 1's car goes too far off the
screen; both cars then restart together from the scorer's last checkpoint, with no other penalty. If the laps run out
with the lights level, a "Play Off!" banner appears and the next point decides the match. Each race opens with a
countdown during which no car is driven and the cars blink. Computer cars read nine numbers per course, one of them
their top speed, and changing any one changes how that car drives.

Course (group 3). A car reads the surface under its centre every frame. Walls only stop it; falls and sinks put it
back after a delay, and the lap count is untouched. A lap counts only after the car has passed the checkpoints in
order, so short cuts count nothing, and the race ends on the lap that takes the laps remaining to zero. A ramp throws
the car up by an amount that depends on its speed; the car keeps its speed, passes over cars and holes, and lands with
a few smaller bounces. Special floor cells such as slow patches cut a fast car to a low speed; most pickups and hazards
are still open.

Collisions (group 4). Cars touch only when they are close in height. Each car's contact area is a small rectangle
turned with its heading. A car that hits another keeps its speed and both are shoved apart, and a computer car briefly
loses control; a wall mirrors the car's motion and takes a quarter of its speed. Cars that are being put back do not
collide.

Handling (group 5). Holding accelerate adds a fixed amount of speed each frame, less drag, up to a per-course top
speed. Releasing the controls slows the car by drag, the brake slows it faster, and holding the brake past a stop
reverses the car at about half top speed. Left and right turn the car through 32 headings at a fixed rate whatever the
speed, each step costing some speed, and a grip number sets how quickly the direction of travel catches up with the
heading, so low grip means longer slides. These handling numbers come from the course and are copied to every car at
the race setup. Computer cars steer by a map of directions laid under the course and drive with pad-like inputs; they
do not speed up or slow down to match the player. Pads 1 and 2 are read every frame; in four-player each pad drives its
own car through the J-Cart adapter, which the game detects at power-on.

Data (group 6). A course is chosen by one number that selects its entries in compressed data tables, from which the
game unpacks maps, checkpoints and art. Each course has a nine-number record and a vehicle record that picks the car
art it is raced with. The construction kit saves tracks to the cartridge's memory in nine fixed slots, each with a
name and a checksum. Game events send numbered sound requests; the start countdown plays three of them about half a
second apart.

The rest (group 7). Menus and game modes, the sound driver and music, attract mode and effects are located in the code
but mostly open; their sections list what is known and what would settle each question.

## Glossary

Modern words a reader may look for, and the period terms this project uses instead.

| Modern word | Term here | Note |
|---|---|---|
| view (screen) | view and scroll | The screen shows a view onto the level; the scroll is the position the view is drawn at. There is no separate view object: the scroll is derived from the cars' positions every frame (section View and scrolling). |
| hitbox | collision area | The area tested for contact; its shape is named only when evidenced. |
| level, stage, course, track, table | as the game's own data distinguishes | The game stores no single course record: a course is an internal course number indexing some thirty per-course tables (T10, section Level data and loading); the construction kit's own word is also course. Found (T5): the game's word is course; a time-trial list index maps to an internal course number that indexes per-course tables; a pool table is an art theme, not a record; "stage" here means a course's playing area in stage pixels. |
| score | lights | The head-to-head score is a column of eight lights at the left screen edge; player 1's share is one word (section Scoring and win condition). |
| zoom | apparent zoom | Sprite and tile scale. The Mega Drive VDP has no scaling hardware (`config/names/hw.tsv` row `vdp_no_scaling`), so any zoomed-out look comes from art, sprite size or scroll layout. |
| mini-micro (developer's term) | Mini Micro (the game's own course-select label) | A half-scale display mode switched on per course, with half-size level art and smaller car art; of the time-trial courses only 17 Pool Slalom uses it, while the other pool-table course, 41 Ball Chase, is normal scale (section Pool-table levels). |

## Names to know

The ten meaning names given in the rules group (plan 1.9 T15). Each name's evidence is its row in
`config/names/ram.tsv` or `config/names/routines.tsv`; the claims are in the sections named there.

| Name | Address | Plain meaning | Where used |
|---|---|---|---|
| ram_lights_p1 | FFCF7E | Player 1's share of the eight head-to-head lights (4 = level) | set to 4 at race setup (code_01CE34), stepped by the head-to-head pause (code_00855A), read by race_win_check and laps_out_check |
| ram_match_winner | FFD670 | Which player won the match | set by race_win_check, laps_out_check and the point rule (code_01E168); read by the season loop (code_0012B4), the eight-car game (code_000D14) and the standings (code_00C998) |
| ram_start_countdown | FFD37E | Frames left of the race-start countdown | set to 100 at race start by fn_004cfa and counted down by race_main; read by cpu_drive_p2, the demo and the car-to-car test, which is off while it runs |
| ram_in_view_p1 | FFD1E2 | Player 1's car is inside the view | written every frame by car_sprite_slot0; read by the point rule (code_01E168), sounds and the contact sound |
| ram_playoff_timer | FFD66E | Times the "Play Off!" banner | started by laps_out_check when the lights stand at 4, raised by fn_007bdc; also read as "playoff running" (0x008E00 lights flash, 0x006FA8 sound, 0x0051D4 pair test) |
| ram_point_pause_count | FFD65E | Counter of the pause after a point (0 to 701) | rises 4 per frame; read by race_win_check, the view (code_00741A) and course hooks |
| race_main | 0x0045E0 | The race: setup, then one pass of the frame loop per frame until the race ends | called through fn_0045ce by both season loops |
| race_win_check | 0x007C76 | The point-pause banner and the win test | runs while ram_point_pause_count is nonzero |
| laps_out_check | 0x009804 | Ends the race by lights when the laps run out, or starts the playoff at 4 lights | every race frame, skipped in rule mode 1 |
| car_sprite_slot0 | 0x0090EE | Player 1's car sprite and shadow, and its in-view flag | every race frame while slot 0 is in use |

## Group 1: View and scrolling, with the pool-table scale

### View and scrolling

Answer to the locating question: there is no separate view-target object. Every race frame the game recomputes a
target point straight from the positions of the cars that count for the view, then moves the view toward it by at most
16 pixels per axis. The target words are scratch results of that computation: a poke of them lasts one frame.

In plain words, for a reader who wants to rebuild it: the game keeps a list of the cars the view must show (the view
set: the player's car alone in a one-player race, both cars in head-to-head, all four in four-player, minus any car
left far behind). Each frame it draws an imaginary box around those cars, takes the box's centre, and slides the
screen so that this centre sits in the middle of the screen, moving at most 16 pixels per frame in each direction.
Because the box centre is used rather than the average position, the view stays halfway between the leader and the
last car of the pack, however the cars in between are spread. Out of view is then simply "outside this screen": the
point rules (section Out-of-view scoring) test the car's position against the same view position, so with two cars in
the view set the margin becomes a fixed gap between the two cars (about 312 to 332 px across or 208 to 232 px up and down at normal scale).
The view routine is view_follow_cars; four step routines move the view one pixel at a time and draw the strip of level
that comes into sight; view_scroll_send hands the result to the video chip each frame.

Units: stage pixels are the coordinates the cars live in (`slot.x`, `slot.y`); screen pixels are what the VDP
shows (320 x 224). On normal-scale courses one stage pixel is one screen pixel; on the Mini Micro course a stage pixel
is half a screen pixel (next section). Measurements below are from controlled probes on race-start save states, each
with an identical control pair that diverged in 0 words (P007 challenge, P014 four-player, P016 Pool Slalom, P018 Ball
Chase, P020 Ferry Fiasco).

| Change made (from a race-start state) | Measured result | Probe |
|---|---|---|
| Player's car moved +160 px along x | view x +160 px (88 to 248) in 10 frames; view y unchanged apart from the car's own drift | P008 |
| Player's car moved -160 px along y | view y -160 px (808 to 648) in 10 frames; view x unchanged | P009 |
| A computer car moved +160 px (one-player challenge) | view unchanged | P010 |
| View target word set from 88 to 248 | view stepped 16 px once, back the next frame | P011 |
| A computer car added to the view set | view moves to the midpoint of the two cars (108, 788) | P012 |
| Four cars; one moved so that midpoint and mean differ | view follows the bounding-box midpoint (80), not the mean (68) | P015 |
| Car placed at (1780, 1780) on a 1792 x 1792 stage without wrap | view stops at (1471, 1567) | P013 |

- The view's top-left corner in stage pixels is held in ram_view_x (horizontal) and ram_view_y (vertical), with half-rate companions ram_FFD00A, ram_FFD00C and plane B scroll words ram_FFD002, ram_FFD004 (bullet Second plane); it moves when the followed car moves. [confirmed: P008, P009, ram_view_x, ram_view_y]
- Car slot field x (offset 0x00) is the horizontal position and y (offset 0x12) the vertical position, in stage pixels: moving the car 160 px along x moved the view 160 px horizontally only; moving it along y moved the view vertically only. Names stay neutral until the waves. [confirmed: P008, P009, slot.x, slot.y]
- There is no separate view-target object: the target words ram_view_target_x (x) and ram_view_target_y (y) are rewritten every race frame from the cars (writers 0074DA and 0074DE, once per race frame in every run); a poke of the target moved the view by one 16 px step for one frame, after which the recomputed target pulled it back, while a poke of the car moved the view for good. [confirmed: P011, P008, code_00741A, t5w_pool_20261013T174433, t5w_ballchase_20261013T174437, t5w_normal_20261013T174442]
- What the view follows: the midpoint of the bounding box (the smallest and largest x, and the smallest and largest y) of the cars in the view set, plus 8 px; the view's top-left is that point minus 152 px (x) and 104 px (y), so the midpoint of the car positions sits at screen (144, 96), 16 px left of and above the screen centre (160, 112); a car's sprite is drawn at its position plus 4 px (section Out-of-view scoring), so a lone 24 x 24 car sprite is centred on the screen centre: the 16 px is the sprite origin offset, not an off-centre view. It is not the mean position: with four cars at x 137, 312, 187 and 212 the view went to the midpoint value 80, not the mean value 68, in all 91 frames where the two differ. [confirmed: P015, P012, ram_view_target_x, ram_view_target_y]
- The view set: a car counts when its flag byte in the eight-byte array at ram_view_set_flags is set, its word in ram_FFD020 is 4 or less, and its state word (`slot.facing_state`) is below 73. In the one-player challenge only the player's car (slot 0, value 1) counts and the computer cars (values 5, 6, 7) are ignored; giving one of them a flag and the value 2 made the view centre between the two cars. [confirmed: P010, P012, ram_view_set_flags, ram_FFD020, slot.facing_state]
- In head-to-head both cars are in the view set (values 1 and 2, both flags set): clearing the computer car's flag left the view on the player alone (P024), and in the identical base pair the view sat between the two cars. In four-player all four count: moving one of the four cars moved the view to the new bounding-box midpoint (P015). [confirmed: P024, P022, P015, ram_view_set_flags, ram_FFD020]
- In a four-player run two cars left far behind got state words (`slot.facing_state`) 76 to 79 and dropped out of the set, after which the view followed the two remaining cars; what moves a car to those states (distance behind the leader, or leaving the screen) is open; a controlled probe placing one car further and further behind the pack would settle it. [hypothesis: ram_view_set_flags, slot.facing_state, docs/ops/ops-tools.md]
- How the view moves: each race frame it closes the gap to the target by at most 16 px per axis (the limit word ram_view_catchup_limit holds 16), one pixel at a time through four step routines that also draw the newly exposed tile column or row (view_step_col_a and view_step_col_b horizontal, view_step_row_a and view_step_row_b vertical). A 160 px jump of the car took 10 frames to catch up (16 px per frame, last step 8 px); while the car moves less than 16 px per frame the view equals the target in the same frame, so there is no lag and no easing. The signed per-frame steps are left in ram_view_step_x (x) and ram_view_step_y (y). [confirmed: P008, P009, P013, view_step_col_a, ram_view_catchup_limit, ram_view_step_x, ram_view_step_y]
- Sampled RAM sometimes shows a single step of 21 or 24 px, or a target not yet offset: the probe reads RAM at the video frame boundary while the game loop is part-way through the stepping, so these are sampling artefacts, not faster steps. [hypothesis: P008, P013]
- Stage edges: on a stage without wrap (the first challenge race, 1792 x 1792, wrap bytes 0) the view stops at 0 on the left and top and at 1471 (width minus 321) and 1567 (height minus 225) on the right and bottom; the target itself is not clamped (it stayed at 1636, 1684). [confirmed: P013, ram_stage_width, ram_stage_height]
- Courses whose wrap bytes ram_FFD740 (horizontal) and ram_FFD742 (vertical) are 1 let the view wrap around the stage width ram_stage_width and height ram_stage_height (34 of 48 surveyed time-trial entries); the bytes and the stage size are written once at level load (writers 01D1F6, 01D1FC, 03F1A4, 03F1AE). [hypothesis: ram_FFD740, ram_FFD742, code_00741A, t5w_pool_20261013T174433, t5w_ballchase_20261013T174437, t5w_normal_20261013T174442]
- The word ram_FFD370 is set to 1 when the view has reached the target or is held at a stage edge (it went to 1 once the view stopped at the bottom edge). [hypothesis: P013, code_00741A, ram_FFD370]
- Single-car mode: while the counter ram_point_pause_count runs (seen during the pause after each point in an idle head-to-head race), the view targets one car only (slot number in ram_scorer_idx) at its position plus 16 px, and the catch-up limit drops to 3 px per frame. [hypothesis: code_00741A, ram_point_pause_count, ram_scorer_idx, ram_view_catchup_limit]
- While the counter ram_FFED2C runs, a random offset of -3 to +4 px is added to the target on each axis each frame (a screen shake). [hypothesis: code_00741A, ram_FFED2C]
- The scroll words sent to the VDP are ram_view_scroll_x (horizontal) and ram_view_scroll_y (vertical): on normal-scale courses they equal the view position modulo 512 and modulo 256 (the plane is 512 x 256 px). [confirmed: P008, P009, ram_view_scroll_x, ram_view_scroll_y]
- The per-frame scroll writer sends one horizontal scroll table command (pc 03ECF6) and one vertical scroll (VSRAM) command (pc 03ED2C) per race frame in every run, once per run of the view follow; setup writes come from 0078C4 (table) and 0078DC, 000272 (VSRAM). [confirmed: code_03ECCC, code_007790, t2w_challenge_20261013T165019, t2w_h2h_20261013T165027, t2w_pool_20261013T165035, t5w_pool_20261013T174433, t5w_ballchase_20261013T174437, t5w_normal_20261013T174442]
- In the scroll writer's default branch the horizontal value is 511 minus the scroll word, and plane B receives a quarter of plane A's horizontal and vertical scroll (a slower background layer); flag words ram_FFD6DC, ram_FFD71E, ram_FFD720 and ram_FFD722 select other branches (equal scroll, a wobble from the table at dat_03EE44 timed by the frame counter, plane A held at 0, or separate plane B words ram_FFD002 and ram_FFD004). [hypothesis: code_03ECCC, ram_FFD6DC, ram_FFD71E, ram_FFD720, ram_FFD722, dat_03EE44]
- Scroll mode register 0B is set to 0 at each race start (one scroll value for the whole screen, both planes) and the plane size register to 64 x 32 cells at boot; register 0B writers 01F8AC, 0045EC, 00023E, the table base from 01F92C. [confirmed: vdp_reg_mode3, vdp_reg_plane_size, vdp_set_hscroll_base, code_01F800, code_0045CE, t2w_challenge_20261013T165019, t2w_h2h_20261013T165027, t2w_pool_20261013T165035]
- The sprite list is built in a RAM buffer at FFCB7C and copied to the VDP by DMA every frame from ROM pc 01FABC; a car is one 24 x 24 px sprite. [hypothesis: vdp_dma, ram_irq6_wblock, P016, P020, t2w_challenge_20261013T165019, t2w_h2h_20261013T165027, t2w_pool_20261013T165035]
- Plane A is drawn by writers at 010B0A, 010ACC and 013AB6, plane B by 013AB6; during races the tile drawers of the step routines add column and row writes at 03E5A8, 03E6FC and 03E908 (normal scale). [hypothesis: code_0108C2, code_0139B0, code_03DE0A, code_03E8C4, t5w_ballchase_20261013T174437, t5w_normal_20261013T174442]
- Sign of the per-frame steps: ram_view_step_x and ram_view_step_y hold minus the pixels the view moved right or down this frame and plus the pixels it moved left or up, so they are the shift of anything placed in screen pixels; the drifting screen objects of fn_01b268 add them to their positions to hold their place relative to the stage. [hypothesis: code_00741A, data_01B268, ram_view_step_x, ram_view_step_y, fn_01b268]
- Direction of a step: on an axis whose wrap byte is set the view moves the shorter way round the stage (the gap is compared with half the stage width or height); without wrap it moves straight toward the target. [hypothesis: code_00741A, view_follow_cars, ram_FFD740, ram_FFD742]
- Centre offset at the stage start: a target x below 0 after the 152 px offset is held at 0 on a course without horizontal wrap and wrapped by ram_stage_width otherwise, while a target y below 0 after the 104 px offset is always wrapped by ram_stage_height; the step routines then hold the view at the edge. [hypothesis: code_00741A, ram_view_target_x, ram_view_target_y, ram_FFD740]
- Vertical jump correction: when ram_FFD716 is clear, the y target fell by more than 1800 px since the previous frame and the new y target lies more than 1800 px from both stage ends, half the stage height is added to it; with ram_FFD716 set on internal course 21 (ram_FFD672) the vertical direction comes from the sign of the gap alone. Single-car mode does not reload the previous y target for this test. [hypothesis: code_00741A, ram_FFD716, ram_FFD672, ram_point_pause_count]
- Step routines: each call moves the view one stage pixel; without wrap and with ram_FFD374 clear the view stops at 0 and at stage width minus 321 / stage height minus 225 (normal scale) or minus 641 / 449 (half scale), and ram_FFD374 set lets the view pass the edges. A new tile column or row is drawn each time the view (normal) or the scroll (half scale) reaches an 8 px boundary: columns 328 px right or 8 px left of the view, rows 224 px below or at the top; at half scale 656 or 16 stage px and 448 or 0. [hypothesis: code_03DE0A, view_step_col_a, view_step_col_b, view_step_row_a, view_step_row_b, ram_FFD374]
- Initial draw: fn_03de0a sets the view, the scroll words and their copies, then draws 45 tile columns 8 px apart from 8 px left of the view (16 stage px apart from 16 stage px left at half scale, where the scroll words start at half the view position modulo 16). [hypothesis: code_03DE0A, fn_03de0a, ram_view_x, ram_view_scroll_x]
- Level drawing: the stage is a block map of 32 px blocks, each 4 x 4 tiles stored column by column in the block tile table ram_FFA0AC; a column strip is 8 blocks (256 px, the whole plane height) and a row strip 14 blocks from 64 px left of the view; a per-block bitmap at ram_FFD698 sets tile priority and block numbers from ram_FFD694 up use the second palette line. [hypothesis: code_03E8C4, code_03DE0A, fn_03e8c4, fn_03e54c, ram_FFA0AC, ram_FFD698, ram_FFD694]
- Half-scale row drawer fn_03e726 (plane A, from the half-scale branches of view_step_row_a and view_step_row_b): one row of 28 blocks at 16 plane px each (448 plane px, 896 stage px) from 128 stage px left of the view; from each block it writes only two tiles, tile columns 0 and 1 of tile row 0, or of row 1 when stage y bit 4 is set, so a half-scale block is the top-left 2 x 2 tiles of its 4 x 4 entry in ram_FFA0AC; priority and palette as at full scale. [hypothesis: code_03E726, fn_03e726, code_03DE0A, ram_FFA0AC]
- Second plane: when ram_FFD6DC is set the step routines also draw plane B strips from a second block map at ram_FF1A08; the half-rate copies ram_FFD00A, ram_FFD00C and the plane B scroll words ram_FFD002, ram_FFD004 move one pixel per two view pixels and are used when ram_FFD722 is set. [hypothesis: code_03DE0A, code_03EA82, ram_FFD6DC, ram_FFD722, ram_FF1A08, ram_FFD002]
- Scroll writer branches in detail: ram_FFD720 holds plane A at 0 and gives plane B the full scroll; ram_FFD71E gives both planes plane A's values and adds the wobble from dat_03EE44 to plane B only, its vertical index following ram_FFC21C at twice the rate of the horizontal one. [hypothesis: code_03ECCC, view_scroll_send, ram_FFD720, ram_FFD71E, dat_03EE44]
- View-relative item group: code_01A2EC (called from data_018DB2, no coverage) draws items 81, 82, 82 and 83 in a row from the stage point ram_FFD426 (x), ram_FFD428 (y), and animated items 84 to 87 (one step every 4 counts of ram_FFC21C) 4 px left and 86 px right of it, 4 px above and 116 px below; the left pair only when x is above 745, the right pair only when x is below 1016. Its shared drawer makes each point view-relative with one wrap by the stage size and skips points exactly on the view's left edge, 400 px or more below it or 448 px or more right of it. [hypothesis: code_01A2EC, data_018DB2, ram_FFD426, ram_FFD428, ram_FFC21C, ram_stage_width, ram_stage_height]

Summary by mode (from the bullets above; rule of thumb for a replica):

| Situation | Cars the view follows | Catch-up per frame | Evidence |
|---|---|---|---|
| One-player challenge | the player's car only | 16 px | confirmed (P010, P012) |
| Head-to-head, racing | both cars, box midpoint | 16 px | confirmed (P024) |
| Head-to-head, pause after a point | the scorer only, its position + 16 px | 3 px | hypothesis |
| Four-player | all four, box midpoint, minus cars left far behind | 16 px | confirmed for four cars (P015); drop-out hypothesis |
| Pool Slalom (Mini Micro) | as above, in stage px; screen moves half as far | 16 stage px = 8 screen px | confirmed for time trial only (P017); multi-car modes open (see Cars per screen below) |

Open questions of this section and what would settle each (all neutral names keep their `unresolved:` verdicts in
`config/names/ram.tsv` until then):

- Wrap: that the bytes ram_FFD740 and ram_FFD742 alone switch wrapping; settle with a controlled probe clearing one of them on a wrapping course and watching the view stop at the edge. [hypothesis: ram_FFD740, ram_FFD742, code_00741A]
- Single-car mode and its 3 px catch-up: settle with a controlled probe in head-to-head that sets ram_point_pause_count and ram_scorer_idx between points and reads the view. A pause count poked off the 701 step (690 at frame 67 of `h2h_r1`, P133) keeps the pause running past frame 200, a way to hold the mode for that probe. [hypothesis: P133, ram_point_pause_count, ram_scorer_idx, ram_view_catchup_limit]
- Screen shake: settle with a controlled probe setting ram_FFED2C during a race and measuring the target offsets over its run. [hypothesis: ram_FFED2C, code_00741A]
- Scroll writer branches, second plane and the half-rate words: no surveyed course sets ram_FFD6DC, ram_FFD71E, ram_FFD720 or ram_FFD722; settle with a flag census over all 67 course numbers and one run on a course that sets each, with a plane B capture. [hypothesis: code_03ECCC, ram_FFD6DC, ram_FFD71E, ram_FFD720, ram_FFD722, ram_FFD002, ram_FFD00A]
- Arrival flag ram_FFD370 and edge override ram_FFD374: settle with P013 plus two runs reading ram_FFD370, and a controlled poke of ram_FFD374 on a course without wrap. [hypothesis: ram_FFD370, ram_FFD374, P013]
- Vertical jump correction and the course-21 path: settle with a run on internal course 21 and one where ram_FFD716 is set. [hypothesis: ram_FFD716, ram_FFD672, code_00741A]
- Tile drawing details (block map, priority bitmap, palette threshold, which tiles the half-scale drawer keeps): settle with plane captures across one 8 px step at normal scale and one 16 px step on Pool Slalom, compared with the block definitions at ram_FFA0AC. [hypothesis: fn_03e8c4, fn_03e54c, fn_03ea82, ram_FFA0AC, ram_FFD698, ram_FFD694]
- The item group of code_01A2EC and the drifting objects of fn_01b268: no coverage run reaches them; settle by finding their dispatcher entries and a course that runs them, then a sprite-list capture. [hypothesis: code_01A2EC, data_01B268, fn_01b268, ram_FFD426]

Located: view_follow_cars in code_00741A (view target and follow, once per race frame), code_03DE0A (initial draw
fn_03de0a and the four step routines view_step_col_a, view_step_col_b, view_step_row_a, view_step_row_b),
code_03E8C4 (tile drawer), code_03EA82 (half-scale tile drawers), view_scroll_send in code_03ECCC (per-frame scroll
writer); RAM ram_view_x/ram_view_y (view), ram_view_target_x/ram_view_target_y (target), ram_view_scroll_x/ram_view_scroll_y (scroll words),
ram_view_catchup_limit (catch-up limit), ram_view_set_flags/ram_FFD020 (view set), ram_stage_width/ram_stage_height (stage size),
ram_FFD740/ram_FFD742 (wrap), ram_point_pause_count/ram_scorer_idx (single-car mode), ram_view_step_x/ram_view_step_y (per-frame
shift); probes P007-P015, P022, P024; writer runs
t5w_pool_20261013T174433, t5w_ballchase_20261013T174437, t5w_normal_20261013T174442.

### Pool-table levels and the mini-micro question

Answer: the zoomed-out look of Pool Slalom is an engine display mode at half scale (stage positions halved for the
scroll, the tile drawing and the sprites), switched on per course by a data byte, together with level art drawn at
half size and smaller car art. The half-scale code is already in the game, so further levels of this kind are data and
art work. Verdict: the look itself comes from **code** (an existing mode) plus art; making more such levels is
**data/art**.

In plain words: the cars always live in the same coordinate space (stage pixels) and drive at the same speeds there.
On a Mini Micro course the game simply shows twice as much of that space on one screen: everything is drawn at half
its stage size, one screen pixel standing for two stage pixels in each direction, so one screen covers four times the
area. The video chip cannot scale, so the game does it in software: it halves the scroll, keeps only a quarter of the
tiles of each level block when it draws, and halves the sprite positions. The car sprite itself is not shrunk; the
course's car art is simply drawn smaller inside the same sprite. That is why the effect needs matching art to look
right, and why the developer's "mini-micro" is the game's own Mini Micro class.

How the game itself organises courses (as found, not asserted): the game says "course" (course select, Course
Storage). The time-trial list is indexed by a byte at FFEAFB (0-26 listed and shown as numbers 1-27; 27-48 reachable
only by a poke and shown as 28-49). Each list entry maps to an internal course number in ram_FFD672 (values 0 to 65
seen), which indexes per-course tables at level load. Several unlisted entries load the same internal course as a
listed one (shown as 44 BBQ Burnoff, 45 Cob Challenge, 46 Frosty Frolics, 47 Electric Energy, 48 Basement Bumps, 49
Driller Killer). Beside each name the course-select screen shows a class label: Pro, Midi Mayhem, Turbo, Turbo Pro,
Short Spin or Mini Micro. No separate record for a "table", "level" or "track" was seen: the pool table is the art
theme of two courses, and "stage" in this doc means a course's playing area in stage pixels.

| Course (shown number, name) | List index | Internal course | Label | Half-scale flag | Stage (stage px) | Wrap |
|---|---|---|---|---|---|---|
| 17 Pool Slalom | 16 | 19 | Mini Micro | 1 | 1664 x 2816 | yes |
| 41 Ball Chase | 40 | 18 | Pro | 0 | 1408 x 2560 | yes |
| 24 Ferry Fiasco | 23 | 34 | Pro | 0 | 2048 x 2048 | yes |
| the other 45 surveyed entries | 0-48 except 16, 23, 27, 40 | various | the five other labels | 0 | 768-2880 x 1280-3072 | 31 of 45 |

Scale comparison: the same vehicle (the white prototype, raced only on the two pool-table courses) on a Mini Micro and
a normal pool-table course, with Ferry Fiasco as the normal-scale reference.

| Measure | Pool Slalom (Mini Micro) | Ball Chase | Ferry Fiasco |
|---|---|---|---|
| Screen scroll for a +160 stage px car move (P017, P019, P021) | 80 px | 160 px | 160 px |
| View catch-up per frame | 16 stage px = 8 screen px | 16 px | 16 px |
| View centre offset from the target (x, y) | 312, 208 stage px | 152, 104 | 152, 104 |
| Stage area on one screen | 640 x 448 stage px | 320 x 224 | 320 x 224 |
| Stage in screen tiles (8 px) | 104 x 176 | 176 x 320 | 256 x 256 |
| Car sprite (RAM sprite list) | one 24 x 24 sprite | one 24 x 24 | one 24 x 24 |
| Visible car art (screenshot, +-1 px) | about 15 x 9 px | about 22 x 14 px | about 23 x 14 px |
| Billiard balls on screen (screenshot) | about 24 px across | about 48 px across | - |
| Pattern data uploaded at level load | about 22 KB (about 660 tiles) | about 36.6 KB (about 1,110) | about 38.9 KB (about 1,180) |
| Car travel from the start, accelerate held | 51 px in 30 frames, 197 in 60 | 51, 197 | - |
| Plane size, scroll mode | 64 x 32 cells, whole screen | same | same |

- Pool-table courses: 17 Pool Slalom and the unlisted 41 Ball Chase, both raced by the white prototype; both screens show green baize, billiard balls and playing cards, but only Pool Slalom carries the Mini Micro label. [hypothesis: P016, P018, docs/ops/ops-tools.md]
- Mini-micro classification by evidence: Pool Slalom is mini-micro (half-scale flag 1, label Mini Micro, half-size art); Ball Chase is not (flag 0, label Pro, full-size art), so the two form a same-vehicle, same-theme control pair. [confirmed: P017, P019, ram_half_scale_flag, t5w_pool_20261013T174433, t5w_ballchase_20261013T174437, t5w_normal_20261013T174442]
- Of 48 surveyed time-trial list entries (all but index 27) only Pool Slalom has the half-scale flag set; across all 67 internal course numbers the flag table holds it for 19 (Pool Slalom) and 50, 53 and 54, three numbers in neither the time-trial list nor the challenge race records; they are the three courses of the eight-car game (Extra Options, Party Play, 8 Player Share; section Level data and loading). [confirmed: P116, t43w_p8_20261014T190418, t43w_p8_20261014T190439, t43w_p8b_20261014T190454, ram_half_scale_flag, ram_FFD672, data_04637A, data_0452C2, fn_04239a]
- The three unlisted Mini Micro numbers are finished courses: loaded by setting ram_FFD672 at the course setup in place of Pool Slalom, each loaded and raced at half scale with no reset; 50 is a pool table (baize, balls, a corner pocket, a cushion rail, a patterned floor beyond the table; stage 1792 x 3392 stage px), 53 and 54 are garden courses (wooden planks on a striped lawn, bushes and hedges; 2112 x 2240 and 1536 x 1536 stage px). [hypothesis: P113, ram_FFD672, ram_half_scale_flag, ram_stage_width, code_01CE34]
- Scroll step per car displacement: moving the car 160 stage px moved the view 160 stage px on all three courses, but the screen scroll moved 80 px on Pool Slalom and 160 px on Ball Chase and Ferry Fiasco: Pool Slalom shows the stage at half scale. [confirmed: P017, P019, P021, ram_view_scroll_x, ram_view_x]
- The flag ram_half_scale_flag is written once at level load by the course setup (writer 01CF22 in every run), from a per-course byte table at dat_04637A indexed by the internal course number ram_FFD672; the same setup unpacks the level data through a per-course pointer table at dat_046832. [hypothesis: code_01CE34, ram_half_scale_flag, ram_FFD672, dat_04637A, dat_046832, t5w_pool_20261013T174433]
- With the flag set the engine doubles the view centre offsets (312 and 208 instead of 152 and 104), feeds half the view position to the scroll words, draws the stage through separate half-scale tile drawers (writers 03EAC6 and 03EBEC on Pool Slalom only; 03E5A8, 03E6FC and 03E908 on the other two) and halves sprite screen positions; eight code regions read or write the flag. [hypothesis: code_00741A, code_03DE0A, code_03EA82, code_0090EE, code_0071C6, code_009B82, t5w_pool_20261013T174433, t5w_ballchase_20261013T174437]
- The VDP setup is the same on all three courses: no plane size, scroll mode or display width change, consistent with the VDP having no scaling hardware. [confirmed: vdp_no_scaling, vdp_reg_mode3, t5w_pool_20261013T174433, t5w_ballchase_20261013T174437, t5w_normal_20261013T174442]
- The art differs: the car stays one 24 x 24 sprite, but its drawn shape is about two thirds the size on Pool Slalom, the billiard balls and cards are about half the size of Ball Chase's, and about 40 % less pattern data is loaded for the level. [hypothesis: P016, P018, P020, t5w_pool_20261013T174433, t5w_ballchase_20261013T174437, t5w_normal_20261013T174442]
- Car motion is unchanged in stage units: the same vehicle covered 51 px in 30 frames and 197 px in 60 frames from the start on both pool courses, so on the Mini Micro screen it moves half as many screen pixels. [hypothesis: P016, P018]
- Cars per screen: time trial has only the player's car, so no count was possible; one Mini Micro screen covers four times the stage area of a normal screen. Whether Mini Micro courses appear in multi-car modes is open; loading Pool Slalom in a head-to-head or four-player race by a poke of the course number would show how the view set and the out-of-view margin (tested on the sprite's screen position, which is halved at half scale) behave there. [hypothesis: ram_half_scale_flag, ram_view_set_flags]
- Setting the flag for another course's data gives a working half-scale level (tested by T10 on Ferry Fiasco: drawn at half scale, recognisable but coarser, car at normal size), so new levels of this kind need no code; the half-scale drawers take 2 x 2 of each block's 4 x 4 tiles, so the half-size look of the level comes from the drawing as well as from the art (section Level data and loading). [confirmed: P105, ram_half_scale_flag, data_04637A]
- Which tiles the half-scale drawer keeps: for each 32 px block a column strip writes tiles 0 and 1 of tile column 0 or 1 (by the half of the block the stage x falls in), so the block shows its top-left 2 x 2 tiles as 16 screen px, 16 blocks per strip; the view and scroll at half scale move the scroll one pixel per two view pixels. [hypothesis: code_03EA82, fn_03ea82, code_03DE0A, ram_half_scale_flag]

What a further Mini Micro course would need, as known now (a plan of what would have to change, not an instruction;
capacity and the full list of per-course tables are in section Level data and loading):

- The switch: one byte per course number in the 67-entry half-scale flag table, read at level load; P105 showed that switching it on for Ferry Fiasco alone gives a working half-scale race, so no code change is needed for a ROM course. [confirmed: P105, ram_half_scale_flag, data_04637A, code_01CE34]
- Art: the existing course art is drawn for full size; drawn at half scale it is recognisable but coarse, because the drawer keeps 2 x 2 of each block's 4 x 4 tiles. A proper Mini Micro course needs level art designed for that drawing (Pool Slalom loads about 40 % less tile data than Ball Chase) and smaller car art inside the same 24 x 24 sprite (about two thirds the size on Pool Slalom). [hypothesis: P105, P016, P018, code_03EA82, P103]
- Room: course numbers 0 to 66 exist and 17, 32, 35, 38 and 40 are free, so up to five new courses fit without moving any table; each needs an entry in every per-course table and a place in a course list to be selectable. [hypothesis: data_045DF8, data_0463BE, data_0452C5, data_04454C]
- The construction kit: the kit's race is course number 66, built in RAM at normal scale; its 147-byte record has no scale field. A Mini Micro kit course would need the flag set for course 66 from some kit option (for example the kind-5 art variant, which picks one of four art records) plus a set of 16 piece graphics drawn for half scale: a small code change plus art. The kit race setup does not read the flag table: it writes the flag 0 itself (the only writer of the flag in a kit race, pc 001ADA, once per race), so that store is the code to change. [hypothesis: P111, code_001978, kit_race_setup, ram_kit_course, ram_FFEDCB, ram_half_scale_flag, P107]
- Kit race at half scale (flag forced to 1 right after that store, a throwaway run): the race runs (timer, car drives, stops at the same obstacle as at normal scale), the screen scroll moves half the view's steps and the kit course is drawn at half scale showing about four times the area, but some piece squares show black or wrong tiles and the scenery is coarse; the stage stays 2304 x 2304 stage px. So the engine side works; half-scale piece art is the missing part. The black is the backdrop through transparent plane A, as the half-scale drawer never writes plane B (Construction kit section). [hypothesis: P111, P156, P157, kit_race_setup, ram_half_scale_flag, ram_stage_width]
- None of the four kit ground themes is a pool table: the kind-5 art variant 0-3 changes only the ground art under the whole course (0 brown woodgrain, 1 dark red carpet, 2 grey floor tiles with red edges, 3 grass with pebbles), the pieces and the circuit unchanged. A pool-table kit theme would be new art. [hypothesis: P112, ram_FFEDCB, kit_race_setup, dat_00260E]

Located: code_01CE34 (course setup, flag load), code_00741A, code_03DE0A, code_03EA82, code_03ECCC, code_0090EE
(half-scale branches); RAM ram_half_scale_flag, ram_FFD672 (internal course number), FFEAFB (list index,
inside ram_FFEAFA), ram_stage_width/ram_stage_height (stage size), ram_FFD740/ram_FFD742 (wrap); tables dat_04637A, dat_046832;
probes P016-P021, P105; writer runs t5w_pool_20261013T174433, t5w_ballchase_20261013T174437, t5w_normal_20261013T174442.

## Group 2: Rules

### Scoring and win condition

Answer: in head-to-head a point is scored whenever player 1's car leaves the view; the point goes to the car further
along the course. The score is a column of eight lights; the match is won by taking all eight, or by leading on lights
when a car finishes the last lap. All frame counts below are video frames at 50 per second (the PAL machine: the race
clock showed 1:00.50 after 3,027 frames). Measurements come from controlled probes on the head-to-head state `h2h_r1`
(player 1 Spider idle against the computer driver Davey), with an identical control pair that diverged in 0 words over
2,200 frames (P022); in the idle base run the computer car scores at frames 214, 511 and 803 and wins the match.

| Change made (from `h2h_r1`) | Measured result | Probe |
|---|---|---|
| none (idle base) | lights 4, 3, 2, 1 at frames 117, 388, 685; the point at 803 wins the match for the computer car | P022 |
| Lights set to 1 during the computer car's point pause | match won by the computer car at the next frame | P026 |
| Lights set to 7 during the same pause | no win; lights 6, 5, 4 at the usual frames | P027 |
| Lights set to 5 (laps untouched) | ordinary points: 4, 3, 2; no match end in 700 frames | P030 |
| Four-player score word ram_FFCF80 set to 5 | 1 word diverged (the poked one): no effect on head-to-head | P031 |

- Player 1's lights are the word ram_lights_p1, a count from 0 to 8 of the eight lights at the left screen edge (player 1's colour from the top, the opponent's below); it starts at 4, goes up 1 for each player-1 point and down 1 for each opponent point (writer 0087D4 in both head-to-head writer runs with points). [confirmed: P022, P027, P030, code_00855A, t6w_h2h_20261013T180950, t6w_h2hpo_20261013T180955]
- The opponent's lights are 8 minus this word: no second score word was found and the win check reads only this one. [hypothesis: code_007BDC, ram_lights_p1]
- The light display follows the word: a poke of ram_lights_p1 changed the sprite list buffer at FFCB7C on the next frame, while a poke of the four-player score word ram_FFCF80 changed nothing else. [confirmed: P027, P030, P031]
- The lights move 174 frames after the point is scored, at the end of the point pause (pause counter ram_point_pause_count equal to 701, rising 4 per frame from 1); ram_scorer_num records whose point it was (1 player 1, 2 player 2) and ram_scorer_idx which car the view follows (0 or 1). The step is an equality: a count poked to 689 at frame 67 of `h2h_r1` reaches 701 at 70 and the lights move at 71 (base 117), while one poked to 690 steps past 701 (702 at 70, 1222 at 200) and the lights never move. [confirmed: P022, P133, P134, P136, ram_point_pause_count, ram_scorer_num, ram_scorer_idx, code_00855A]
- Win on lights: a point scored by the opponent while player 1 has 1 light, or by player 1 while player 1 has 7, ends the match at once (ram_match_winner = winner, 1 or 2; the lights stay at 1 or 7); the check runs on every frame of the point pause. [confirmed: P026, P027, P022, code_007BDC, ram_match_winner]
- The pause banner shows "Bonus!" and the scorer's name for an ordinary point and "Winner!" for the deciding one (screens at frames 50 and 820 of an idle `h2h_r1` run); the banner choice is the word ram_FFD674 (3 Bonus, 6 Winner). [hypothesis: code_007BDC, ram_FFD674, P022]
- Banner pictures: the fixed 6,912-byte block unpacked to ram_FF750C at every race setup holds six 36-tile banner pictures; fn_035890 sends the one chosen by the banner word ram_FFD674 at 12 tiles a frame (three frames) to the tiles of entry 0 of the sprite-art descriptor table ram_FFC37C, then stores the end word (6 after start 3, 9 after start 6) in ram_FFD676 and sets the banner word to -1, so race_win_check draws the banner only once its tiles are in VRAM. [hypothesis: code_035890, fn_035890, ram_FF750C, dat_05AAEA, ram_FFD674, ram_FFD676, ram_FFC37C, code_007BDC]
- The name on the pause banner (fn_007ef4): the six letters of the scoring player's driver name (ram_FFEEFA, by the driver word of its player record from ram_FFE74C) or, in the team game (ram_FFD68E = 1), RED for scorer index 0 or 2 and BLUE otherwise (dat_008030, dat_008036), each sent as a font tile from ram_FF9D2C (A-Z, 0-9, ! and /; ! and 0 share a tile, other signs one fixed tile); the next banner item is moved 4 px per trailing space (ram_FFCFB0). [hypothesis: code_007EF4, fn_007ef4, code_007BDC, ram_FFEEFA, ram_FFCFB0, dat_008030]
- After the match the results screen ("Race Positions!") lists the winner first; the winner is entered as first finisher in ram_FFD2BA (the write is at 0013CA; the writer tap reported the next instruction, 0013D0). Only that one run (t6w_h2hwin) shows the entry: in the two player-2 wins of P136 ram_FFD2BA and ram_FFD2BC are only cleared to 0 the frame after the race ends (writers 0013BA, 0013BE; frames 1085 and 400) and stay unwritten to frame 2400, so the entry is likely made for a player-1 win only (the season loops test the first words for 1). [hypothesis: code_0012B4, ram_FFD2BA, t6w_h2hwin_20261013T180953, P136]
- Four-player modes keep one score word per player at ram_FFCF80 to ram_FFCF86, raised by 1 or 2 per point (ram_FFED38), and use rule modes 3 and 4 of ram_rule_mode (1 one-player race, 2 head-to-head); not measured. [hypothesis: code_00803C, ram_FFCF80, ram_rule_mode]
- The lights win test in race_win_check names the scorer by the car index ram_scorer_idx, not by ram_scorer_num: lights 1 with index 1, 3 or 5 gives player 2 the match, lights 7 with index 0, 2 or 4 gives it to player 1. [hypothesis: race_win_check, ram_scorer_idx, ram_lights_p1]
- Four-player win tests (static reading, not measured): rule mode 3 ends the match when the scoring car's player has a score word of 1; the other four-player modes when that word is 10 or more, or exactly 7 with ram_FFEC80 set and ram_FFED36 6; with ram_FFED36 4 the lights test is used. [hypothesis: race_win_check, ram_FFCF80, ram_FFED36, ram_FFEC80]
- The point pause routine is picked each frame by rule mode in fn_00803c: 2 lbl_00877A and 3 the start of code_00855A (both in code_00855A), 4 a four-player pause in code_00803C, 1 none. In the mode-4 pause, at count 701 the scorer ram_scorer_num (1-8) gains ram_FFED38 points, the score words of the pairs numbered 1-4 by ram_FFD666, ram_FFD668 and ram_FFD662 lose 1, gain 1 (to 11) and lose 2 (pair n = cars n-1 and n+3, sharing score word n from ram_FFCF80: scorers n and n+4 both add to it), and ram_lights_p1 moves +1 for scorers 1, 3, 5, 7 and -1 for 2, 4, 6, 8, which suggests two teams of two. [hypothesis: fn_00803c, code_00803C, ram_scorer_num, ram_FFED38]
- A won match ends the race once the pause count passes 550; while the banner is held the count then rises 1 per frame instead of 4. Measured in two player-2 wins (P136): counts 149 to 340 take +4 then -3 (net +1, 192 frames, values 150 to 341), then +4 again; last count 553, the race ends that frame (1084 idle, 399 in the playoff variant); the earlier win run t6w_h2hwin_20261013T180953 also shows 192 hold writes. [hypothesis: race_main, race_win_check, ram_point_pause_count, ram_match_winner, P136, t6w_h2hwin_20261013T180953]
- The head-to-head pause lbl_00877A: at count 601 the scorer's car (index ram_scorer_idx) switches to state 52; at 701 both cars go to state 51, ram_lights_p1 steps +1 for scorer index 0 and -1 otherwise, both in-view flags are set and ram_FFD66A is set to 10; below count 20 the scorer's state follows its heading, which steps 1 per frame. No car is moved by the pause itself. [hypothesis: lbl_00877A, code_00855A, ram_scorer_idx, ram_lights_p1]
- Rule mode 3 reads as a three-car game of eight lights each: its pause (the start of code_00855A) raises by 1 the word of the car named by ram_FFD662 in ram_FFCF80-ram_FFCF84 and lowers the scorer's by 1, and fn_008858 draws 8 minus each word as lit lights in three columns, so the words count lights lost; at the end of the pause the other two cars take the scorer's progress, restart pair, laps and lap flags. How this fits the mode-3 win test (score word 1) is open. [hypothesis: code_00855A, fn_008858, ram_FFCF80, ram_FFD662]
- The score display fn_008858 (every race frame) draws the lights column in rule mode 2 (also with ram_FFD68E set, or ram_FFEC80 with ram_FFED36 4), place markers in rule mode 1, three light columns in mode 3, three stacks of one item per point with ram_FFEC80 and ram_FFED36 6, four stacks of one item per two points (at most 12) otherwise, and a time display while ram_FFD750 is set; during a point pause the affected counts flash with the step the pause will apply. [hypothesis: fn_008858, code_00855A, ram_rule_mode]
- Results points (static reading; fn_000a8c, run before the results screen fn_00e746): each player record's driver gets one more race in the 12-byte driver records at ram_FFF6A6 (count up to 99) and points: with ram_FFD68E set a team result, 30 to each driver of the winner's pair (records 1 and 3 for winner 1, else 2 and 4); rule mode 2, 30 to the winner; rule mode 3, 30 and 15 to the two players with the fewest lights lost (ram_FFCF80-ram_FFCF84, smallest first); other modes 30, 20 and 10 by score word, largest first. The results rows (fn_00e8f8) show an item per row that follows these points, and place items 1, 1, 3, 3 in the team result. A lights-ordered branch of fn_000a8c can never run (it tests ram_FFD68E again after the set case has left). [hypothesis: code_000A8C, code_00E746, ram_FFF6A6, ram_FFD68E, ram_rule_mode]
- Series end (static reading; fn_043ac6): the target is 3, 5 or 7 by ram_FFEC64 (below 5, 5, above 5); when a player record's second word reaches it, the drivers are ordered by those words, largest first, and the results screen runs with ram_FFEC14 set (no message, alternate row draw). [hypothesis: code_043AC6, code_00E746, ram_FFEC64, ram_FFEC14]

Located: code_01CE34 (rule dispatcher fn_01d862 by ram_rule_mode), code_01E168 (head-to-head point decision),
code_00855A (point pauses of rule modes 3 and 2, lights update at 0087D4, score display fn_008858), code_007BDC (pause banner, win check race_win_check), code_00803C (point pause dispatcher fn_00803c, four-player pause), code_0012B4 (head-to-head
result), code_000A8C (results points), code_00E746 (results screen), code_043AC6 (series end); RAM ram_lights_p1 (lights), ram_point_pause_count (pause counter), ram_scorer_idx, ram_scorer_num, ram_match_winner (match winner),
ram_FFD674 (banner); probes P022, P026, P027, P030, P031, P133, P134, P136; writer runs t6w_h2h_20261013T180950,
t6w_h2hwin_20261013T180953, t6w_h2hpo_20261013T180955, t38w_h2h_20261016T120601, t38w_h2hpo_20261016T120558.

### Out-of-view scoring

Answer: out of view is decided against the view, not by the distance between the cars, and only for player 1's car
(slot 0). The car is out when its sprite, drawn 4 px right of and below the car's position, is 16 px or more past the
left or top screen edge, or starts at screen x 304 or later, or at screen y 204 or later. In stage pixels relative to
the view's top-left corner (ram_view_x, ram_view_y): out when x - view x <= -20 or >= 300, or y - view y <= -20 or
>= 200. The screen is 320 x 224 and the sprite 24 x 24, so the zone is not symmetric: on the left and top the car is out with
8 px of its sprite still showing, on the right with 16 px and at the bottom with 20 px.

In plain words, for a reader who wants to rebuild it: during a head-to-head race the game asks one question every
frame, "is player 1's car still on the screen?", against the screen rectangle given by the bounds above. While the
answer is yes nothing happens. When it turns no, a point is decided between the two cars, and it goes to whichever car
is further along the course (each car carries a course progress count), not to the car that stayed on screen: player
1 leaving through the top of the screen while ahead wins the point. Because the view sits halfway between the two cars,
the cars move apart symmetrically from the screen's centre, so in practice a point falls when the gap between them
reaches about 208 to 232 px up and down or 312 to 332 px across, whichever car leads. Only player 1's car is tested;
the opponent's own flag is kept but never read for points. After the point both cars stop, the lights move one step,
and both cars are put back side by side on the scorer's last checkpoint line, ready to race again 199 frames (about 4
seconds) after the point.

| Change made (from `h2h_r1`, view following the computer car only) | Car x or y minus view x or y | Result | Probe |
|---|---|---|---|
| Player car moved right | x 300 | out, point next frame | P032 |
| Player car moved right | x 298 | in | P033 |
| Player car moved left | x -20 | out, point next frame | P034 |
| Player car moved left | x -18 | in | P035 |
| Player car moved up | y about -25 | out, point next frame | P036 |
| Player car moved up | y about -15 | in | P037 |
| Computer car drives away (player idle below) | y 197, then 201 | in, then out | P025 |

- Relative to the view: with the computer car taken out of the view set the view followed the player only and no point was scored in 550 frames although the computer car drove far off-screen; with the player's car taken out the view followed the computer car and the idle player went out 21 frames earlier than in the base run (frame 193 instead of 214). [confirmed: P024, P025, P022, ram_view_set_flags, ram_in_view_p1]
- Only player 1's car is tested: the point routine reads one flag, ram_in_view_p1 (slot 0's in-view flag, rewritten every race frame by the slot-0 sprite routine), and the computer car leaving the view never scores. [confirmed: P024, code_01E168, code_0090EE, ram_in_view_p1]
- Margin, measured: out when the car's position minus the view position is -20 px or less or 300 px or more horizontally, -20 px or less or 200 px or more vertically (stage pixels, normal scale; the top bound measured as between -25 and -15). [confirmed: P032, P033, P034, P035, P036, P037, P025]
- The test uses the previous frame's view position (the sprite routine runs before the view moves): in the base run the car's sampled offset was 198 on the frame before the point and 201 on the frame of it. [hypothesis: P022, P025, code_0090EE]
- The sprite offset is 4 px for the 32 driving headings (5 px for some) from the sprite frame table at dat_038B04; a jumping car's sprite is drawn up and left by half its height (ram_car_height), and a car whose body sprite, or that position shifted right by half the height and down by the height, lies fully inside screen x 2-286, y 2-186 also sets the fully-on-screen flag ram_FFD1F4 and counts as in view; otherwise it is in view while the shifted position is inside screen x -15 to 303, y -15 to 203. [hypothesis: code_0090EE, dat_038B04, ram_car_height, ram_FFD1F4]
- The other three slots run copies of the slot-0 sprite routine car_sprite_slot0 (fn_0091ec, fn_0092f6, fn_00940a) that keep their own in-view flags ram_FFD1E4, ram_FFD1E6, ram_FFD1E8 and fully-on-screen flags; the point decision reads only slot 0's. [hypothesis: code_0090EE, ram_FFD1E4, ram_in_view_p1]
- Car states 32 and above are sequences stepped every 4 frames (states 46-50 every 8) that stop at 51, 58, 65 and 79; a car in view requests sounds at states 34-35, 47 or 60, and 53 or 67 (fn_00951a). [hypothesis: car_sprite_slot0, fn_00951a, slot.facing_state]
- With both cars in the view set the view sits on the midpoint of the pair (section View and scrolling), so the margin becomes a gap between the cars: player 1 below the other car goes out at a vertical gap of about 208 px (209 measured twice), to its left at about 328 px (332 sampled); by the same bounds above it at about 232 px and to its right at about 312 px. [confirmed: P022, P023, P030]
- Who scores: the car further along the course, compared by the low byte of the course progress words ram_car_progress (slot 0) and ram_FFD130 (slot 1), with a wrap correction (when either is above about 140 both are shifted by 180 modulo 256); a tie goes to player 1. Leaving the view is not itself a loss: the player's car moved up the course out of the top of the view scored the point for player 1. [confirmed: P036, P032, P034, code_01E168, ram_car_progress, ram_FFD130]
- The scorer must be driving normally (car state below 32, `slot.facing_state`); a point is decided only while no pause runs and 10 frames after the previous pause (ram_FFD66A). [hypothesis: code_01E168, code_01CE34, slot.facing_state, ram_FFD66A]
- Eight-car elimination (static reading): while no pause runs and at least two cars still in are not fully on screen (ram_FFD1F4 0), the lowest-ranked car still in that is not fully on screen, or whose sprite lies outside screen x 25-263, y 25-163, is put out (state 73, out flag ram_FFD2DC + 2 x car); cars n and n + 4 form pair n + 1, and each pair with both cars out is recorded in ram_FFD662, ram_FFD666 and ram_FFD668 in turn; the third pair out ends the round: the remaining pair's car still in, or with both in the one with the greater rank value, scores (ram_scorer_idx, ram_scorer_num) and the point pause starts; after putting out a car that was not in view the next pick waits 16 steps (ram_FFD66A). [hypothesis: code_013BD6, fn_014f28, fn_0151be, fn_01509c, ram_FFD2DC, ram_FFD662]
- Rule mode 3 point decision (static reading, code_01DEA2 from the rule dispatcher): with no car out yet a three-car pick of the same shape as the eight-car one (cars 1-3, same screen box, progress-byte order, car number in ram_elim_pick) raises the picked car to state 73, names it in ram_FFD662 and sets ram_FFD66A to 4; with one car out, a remaining car that drives (state below 32) and has its in-view flag 0 scores only when its progress byte is not below the other remaining car's: the other car goes to state 52 and the point pause starts (ram_scorer_idx, ram_scorer_num). A car out of view behind the other decides nothing, unlike head-to-head where player 1 out of view always decides the point. [hypothesis: code_01DEA2, code_01E02C, ram_FFD662, ram_elim_pick, ram_scorer_num]
- Rule mode 4 uses a four-car pick of the same shape (fn_01dd18: cars 1-4 not named by ram_FFD662 or ram_FFD666) from the rule dispatcher fn_01d862. [hypothesis: code_01DD18, code_01CE34, ram_FFD666, ram_elim_pick]
- Rule mode 4 point decision (static reading, fn_01d862): the first two cars out are picked by fn_01dd18 one per call (ram_FFD662, then ram_FFD666; state 73, ram_FFD66A 4, sound 58 hex); with two out, in the team game (ram_FFD68E) when the two out are team-mates (cars 1 and 3, or 2 and 4) the remaining car further along (progress bytes of fn_01de10, a tie to the lower car number) scores at once; otherwise the mode-3 rule: a remaining car driving and out of view scores when not behind the other, which goes to state 52; ram_FFD668 names the other remaining car. [hypothesis: code_01CE34, fn_01d862, fn_01de10, ram_FFD662, ram_FFD666, ram_FFD668, ram_FFD68E, ram_scorer_num]

What happens to the car left behind (idle base run, point at frame t = 214):

| Frame | Event |
|---|---|
| t | point decided; the left-behind car switches to state 52 and plays a 24-frame sequence (states 52 to 58); the scorer stops and turns on the spot (about 3 headings per 4 frames); the view follows the scorer at 3 px per frame |
| t + 150 | the scorer's car also switches to state 52 |
| t + 174 | lights move one step; both cars to state 51 |
| t + 176 | both cars placed side by side on the line of the last checkpoint the scorer passed (here the line y 448 between x 144 and 376: cars at (242, 432) and (277, 432)) |
| t + 178 to t + 198 | both cars run the reappearing sequence (states 66-71) |
| t + 199 | both cars drive again (state 0); the whole interruption lasts about 4 s |

- No elimination, penalty time or lap loss: both cars restart together from the scorer's last checkpoint (positions from ram_last_cp_line and the per-slot copies after it), given the scorer's progress word; the only change of score is the one light. [confirmed: P022, P023, code_01E218, ram_last_cp_line, ram_car_progress]
- At the restart every car's laps-remaining word is set to player 1's (ram_FFD164), whoever scored. [confirmed: P029, code_01E218, ram_FFD164, ram_FFD166]
- Four-car restart (static reading): the slot 0 routine fn_01e256 restarts the cars as a group when ram_FFD372 is set (written every race frame by fn_01e218: 1 when every car of the view set is at state 32 or more), else slot 0 alone in rule mode 1; the group source is the scorer (ram_scorer_idx) or else the first car not out (ram_FFD662, ram_FFD666); its progress word and restart pair go to slots 0-3, slots 1-3 then take slot 0's progress, laps and the long ram_quarter_flags, and once the view is at its target (ram_FFD370) the cars still in go to state 66. [hypothesis: code_01E218, ram_FFD372, ram_scorer_idx, ram_FFD370]

Open questions of this section and what would settle each (neutral names keep their `unresolved:` verdicts in
`config/names/ram.tsv` until then):

- Previous-frame view: settle with a controlled probe that moves the view by poke on the frame before the car crosses a bound and records which view position the in-view flag used. [hypothesis: P022, P025, code_0090EE]
- Sprite offset per heading and for a jumping car: settle with P032 repeated with the car turned to each of the 32 headings, and once with the car airborne (ram_car_height set). [hypothesis: dat_038B04, ram_car_height, code_0090EE]
- The fully-on-screen flag ram_FFD1F4 and its smaller inner box (screen x 2-286, y 2-186): settle with a controlled probe that holds the flag at 0 and at 1 while the car crosses the outer bound. [hypothesis: ram_FFD1F4, code_0090EE]
- The scorer-must-be-driving rule and the 10-frame gap after a pause: settle with a controlled probe setting the leading car's state to 52 on the frame player 1 goes out, and one poking ram_FFD66A to a high value. [hypothesis: code_01E168, slot.facing_state, ram_FFD66A]
- Four-player out of view (rule modes 3 and 4, the per-slot flags ram_FFD1E4-ram_FFD1E8): no oracle state reaches a four-player race; settle with a four-player save state and a writer run on the four flags. [hypothesis: ram_FFD1E4, code_00803C, ram_rule_mode]
- Margin at Mini Micro scale: settle by loading Pool Slalom in head-to-head by a poke of the course number and repeating P032-P037. [hypothesis: ram_half_scale_flag, ram_in_view_p1]

Located: code_0090EE (car_sprite_slot0: slot-0 sprite position and in-view flags; fn_009580 car sprites), code_01E168 (point decision), code_01E218 (restart on
the checkpoint line), code_00855A (pause sequence), code_01DEA2 (rule mode 3 decision), code_01E02C and code_01DD18 (three- and four-car picks); RAM ram_in_view_p1, ram_FFD1F4, ram_car_progress, ram_FFD130, ram_last_cp_line,
ram_view_set_flags; probes P022-P025, P032-P037; writer run t6w_h2h_20261013T180950.

### Tie-break playoff

Answer: when a car finishes its last lap the game compares the lights: with a lead the leader wins at once; tied at
4-4 it shows "Play Off!" and racing goes on, and the next point wins the match (sudden death). Both cars take part,
from wherever they are; the playoff ends only with that point.

In plain words, for a reader who wants to rebuild it: a head-to-head match normally ends on lights. If neither car
has taken all eight when a car with no laps left reaches the start line, the lights decide on the spot: more than four
for player 1 wins for player 1, fewer wins for player 2. Level at four each, the game shows "Play Off!" and lets the
race go on over the same course, with no extra laps and no time limit. Nothing special is switched on for the
playoff: the point routine already ends the match whenever the scorer has no laps left, and every point restarts
both cars with player 1's laps count, which is now 0, so the next point under the ordinary out-of-view rule is
sudden death. The "Play Off!" banner is only a display: a timer that rises 4 per frame while it is on screen.

| Change made (from `h2h_r1`) | Measured result | Probe |
|---|---|---|
| Player 1's laps 3 to 0 at frame 3, lights 4-4 | "Play Off!" timer set at frame 4; the pending computer point makes the lights 3 at 117 and the computer car wins at 118 | P023 |
| Lights 5 and player 1's laps 0 at frame 3 | player 1 wins at frame 4 | P028 |
| Lights 5 at frame 3 (4-4 after the pending point at 117), player 1's laps 0 at frame 118 | the next point (frame 214, computer car) wins the match | P029 |
| Lights 5 at frame 3 only | the point at 214 is an ordinary point (lights 3 at 388) | P030 |

- The laps-out check runs every race frame in head-to-head and multi-player modes: when a car whose laps-remaining word is 0 has course progress low byte 0 (it is on the start line), the lights decide: player 1 above 4 wins (ram_match_winner = 1, writer 00988C), below 4 player 2 wins (= 2), at exactly 4 the "Play Off!" banner timer ram_playoff_timer starts and the race continues. [confirmed: P023, P028, code_0090EE, ram_FFD164, ram_playoff_timer, ram_match_winner, t6w_h2hwin_20261013T180953]
- In the playoff the next point decides: the point routine declares the scorer the match winner when the scorer's own laps-remaining word is 0, and the restart after any point gives every car player 1's laps value, so after the laps run out every point is decisive. [confirmed: P029, P030, code_01E168, t6w_h2hpo_20261013T180955]
- Who takes part: both cars of the head-to-head; the playoff has no time limit of its own and was not seen to end without a point. [hypothesis: P029]
- The fourth slot's check reads player 1's laps word instead of its own (a quirk: the start-line test for slot 3 uses slot 0's laps). [hypothesis: code_0090EE, ram_FFD164]
- The Play Off banner routine fn_007bdc runs outside rule modes 3 and 4 only; it plays sound 139 on its first frame and raises ram_playoff_timer by 4 per frame. During a point pause it sets the timer to 352 on every frame, because its test compares a 40-60 value derived from the timer, not the timer, with 348; the banner therefore jumps to its exit phase when a point is scored (the hold is measured, P136, bullet below). [hypothesis: fn_007bdc, ram_playoff_timer, race_main, P136]

Open questions of this section and what would settle each:

- Whether a playoff can end without a point (both cars driving on, or a further laps-out check): settle with a run from the P023 variant in which neither car leaves the view for 3,000 frames, both driven by the computer. [hypothesis: P029, laps_out_check]
- The banner timer is held at 352 through a point pause (the quirk above; intended effect probably "jump to the exit phase once"). Measured from the P023 variant, where the computer car's point pause is already running: laps_out_check sets ram_playoff_timer to 1 at frame 4 (0098AA), and from that frame on fn_007bdc writes it twice per frame, +4 (007C04) then 352 (007C36), through the pending point (lights at 117) and the deciding point's pause until the race ends at 399; the idle base run never writes it. [confirmed: P136, P023, fn_007bdc, ram_playoff_timer]
- The slot-3 laps quirk: settle with a four-player state in which slot 3 runs out of laps before player 1. [hypothesis: code_0090EE, ram_FFD164]
- Playoff in the four-player modes (whether rule modes 3 and 4 have one; fn_007bdc does not run there): settle with a four-player save state. [hypothesis: fn_007bdc, ram_rule_mode]

Located: laps_out_check in code_0090EE (laps-out check), code_01E168, code_007BDC (banner timer ram_playoff_timer); probes P023,
P028, P029, P030, P136; writer runs t6w_h2hwin_20261013T180953, t6w_h2hpo_20261013T180955, t38w_h2hpo_20261016T120558.

### Race start and finish

Answer: the race starts after a 100-frame countdown during which the cars blink and cannot move; it runs 3 laps; a
one-player challenge race ends 200 frames after the second car finishes, and only first or second place goes on.

In plain words, for a reader who wants to rebuild it: a race opens with the four cars on a 2 x 2 grid and a
countdown of 100 frames (2 seconds), during which the cars blink and nobody can drive; then the race clock starts. A
race is 3 laps. Each car's laps count drops by one at every crossing of the start line, and a car that reaches 0 has
finished and stops just past the line. In a one-player challenge race the game writes the finishers down in order;
once the second car is home it waits 200 frames (4 seconds), fills in the places of the cars still running from their
running order after 51 of those frames, and then shows the positions screen. In the season only first and second
place go on; third and fourth cost a life. Head-to-head races end on the lights instead (sections above).

Measured timeline, idle challenge race 1 (`challenge_r1`, writer run t6w_chal_20261013T180957; frames from the state):

| Frame | Event |
|---|---|
| 1 | countdown reads 72 (it began at 100 before the state was saved) |
| 2 to 73 | countdown written once per frame (72 writes, writer 004990), 0 at 73 |
| 74 | the computer cars start to move |
| 82 | the player's car moves, accelerate held from the start |
| 2415 | slot 3 finishes; first finishing word first written at 2416 |
| 3048 | slot 2 finishes; second finishing word written; end timer starts at 3049 |
| 3099 | end timer at 51: third and fourth finishing words filled from the running order |
| 3248 | end timer at 200: the positions screen follows |

- Grid: four cars in a 2 x 2 grid 40 px apart in each axis; in challenge race 1 the player's car (slot 0) is back left at (232, 904) and the others at (272, 864), (232, 864) and (272, 904); for one-player races the setup swaps the player's start position with slot 2's. [hypothesis: P038, code_01CE34]
- Grid by rule mode (static reading, fn_01d46e): the 2 x 2 grid of the start entry is kept in rule modes 1 and 2; rule mode 3 lines the three cars up in one row (slot 0 x - 10, slot 1 x - 20, slot 2 at slot 0 + 60, 30 px apart when the entry's columns are 40 px apart) and the other modes the four cars (slot 0 - 15, slot 1 - 30, slots 2 and 3 at slot 0 + 50 and + 75, 25 px apart); on courses 19 and 21 the grid columns become rows (slots 1 and 2 swap places) and the lines run along y. In time trial slots 1-3 are off, slot 0 moves 20 px and slot 2 (kind 1) starts on slot 0's place. [hypothesis: code_01CE34, fn_01d46e, dat_0464CA, ram_FFD020, ram_FFD750]
- Countdown: the word ram_start_countdown is set to 100 at the race start and counts down once per race frame; while it is not 0 no car is driven and the cars are hidden on alternate 8-frame spans (blinking); sound cues play at 60 and 30 remaining and a different one at 1. In `challenge_r1` it reads 72 at frame 1 and 0 at frame 73; the computer cars move from frame 74, the player's car with accelerate held from frame 82. The blinking is done by the car sprite routine fn_009580, which reads the countdown. [confirmed: P038, P005, code_0045CE, code_0090EE, ram_start_countdown, t6w_chal_20261013T180957]
- Laps: 3 per race (ram_FFD71A); each car's laps-remaining word (ram_FFD164 + 2 x slot) starts at 3 and drops by 1 as the car crosses the start line (per-slot writers 01F6DC, 01F746, 01F7B0); a finished car stops a few pixels past the line. In the idle challenge race 1 the computer cars finished at frames 2415 (slot 3) and 3048 (slot 2). [hypothesis: code_01F4F0, ram_FFD164, ram_FFD71A, t6w_chal_20261013T180957]
- Challenge finish: finishers are recorded in finishing order in ram_FFD2BA to ram_FFD2C0 (slot number + 1); the end timer ram_FFD65C is set to 1 (writer 00716C) the frame after the second computer finisher and then rises 1 per frame (0047E0); at 51 the remaining places are filled from the current running order (ram_FFD250); the race ends at 200. Measured in two finish orders (P135): idle `challenge_r1` slots 3, 2 finish at 2415, 3048 -> words 4, 3, timer 3049 to 3248, fill 2, 1 at 3099; slot 3 held back one lap -> slots 2, 1, 3 finish at 3048, 3282, 3289 -> words 3, 2, 4, timer 3283 to 3482, fill 1 at 3333; the earlier run t6w_chal_20261013T180957 agrees with the idle one. [confirmed: P135, code_0068D2, code_0045CE, ram_FFD2BA, ram_FFD65C, ram_FFD250, t6w_chal_20261013T180957]
- Challenge finish, unmeasured parts: the timer also starts when slot 0 finishes in rule mode 1 (fn_040f2a); the place-display start (fn_007072) is at place 2 unless ram_FFEC66 is set, or at place 3; the positions screen ("Race Positions!", "Try Again!" when the player is not in the top two) follows the wait; Start ends the wait after 30 frames. [hypothesis: code_0068D2, code_040F2A, ram_FFD65C, ram_FFEC66]
- Qualifying: after a challenge race, first place continues and adds to a win-streak count ram_FFEC38, second place continues except on the last race, third and fourth lose a life (ram_FFE776, 2 at race 1); three wins in a row lead to a bonus race on internal courses 55 to 59 in turn. [hypothesis: code_00102E, ram_FFEC38, ram_FFE776]
- Season: Challenge is races 0-9 and Pro Challenge races 10-24 (race number ram_FFD718, game type ram_FFEB20 = the game-type menu row 0-8); each race has a 14-byte record in dat_04454C (internal course number, three opponents with a substitute when one is the player's own driver, and a pointer to the computer cars' parameter block). Challenge race 1 is internal course 16. [hypothesis: code_00102E, dat_04454C, ram_FFD718, ram_FFEB20, ram_FFD672]
- Head-to-head finish: by lights or at the end of the laps (sections above); there are no tournament points in the one-player modes. [hypothesis: code_0090EE, code_007BDC]
- The word at FFE69A is a menu cursor lead, not race state. [hypothesis: ram_FFE69A]
- The race ends (race_main returns) when the end wait ram_FFD65C reaches 200 or Start is pressed after 30 frames of it, when a won match passes pause count 550, or in the demo (ram_FFEBEA) when its frame count runs out or any control byte is set. Measured: the end-wait and won-match exits (P135: last race writes at timer 200, frames 3248 and 3482; P136: last pause write 553); Start and the demo exits not measured. [hypothesis: race_main, ram_FFD65C, ram_FFEBEA, P135, P136]
- In rule mode 1 when the end wait reaches 51 each zero word k (0 to 3) of ram_FFD2BA-ram_FFD2C0 gets 1 + the position of the value 2k in the list at ram_FFD250. Since fn_008858 stores each slot's place x 2 there, the position of 2k is the slot holding place k, so the fill writes slot + 1 in place order, the same reading as the finishing order above (T14 read it as slot-indexed; that reading needs ram_FFD250 to be a place-ordered list of slots x 2). The writer run agrees with place order: the first word was first written the frame after slot 3 finished (2416), the second with slot 2's finish (3048), the third and fourth only by the fill (3099); slot-indexed words would have had the fourth word written at 2416. The values settle it (P135): ram_FFD250-ram_FFD256 hold each slot's place x 2 counted from 0 (6, 4, 2, 0 at the idle finish; 6, 2, 0, 4 with slot 3 held back), and the fill wrote 2 and 1 (idle, words 2 and 3) and 1 (held back, word 3), the slots in places 3 and 4. [confirmed: P135, race_main, fn_008858, ram_FFD2BA, ram_FFD250, ram_FFD2C0, t6w_chal_20261013T180957]
- The finishing words are written by the slot 0-3 state steps: in rule mode 1, on every frame a car's laps-remaining word is 0, slot + 1 goes to the first word of ram_FFD2BA that is 0 or holds it already, the car's speed loses 4 and its control bits 4-6 are cleared, so a finished car coasts to a stop; slot 0's own finish also starts the end wait ram_FFD65C (set to 1 when 0). Measured (P135): each finisher's word is rewritten every frame from the frame its laps word reaches 0 (slot 3: the frame after) to the race end (833 writes for slot 3 in the idle run), by one writer per slot (slot 1 0410A8, slot 2 0411F0, slot 3 041338); slot 0's finish, the speed and control-bit steps not measured. [hypothesis: code_040F2A, ram_FFD2BA, ram_FFD65C, P135]
- Bonus race: the bonus course (internal course 55 + ram_FFEC36) moves on to the next, 0-4 wrapping, only when the bonus race changed the lives count; Pro Challenge starts at bonus index 2. [hypothesis: code_00102E, ram_FFEC36, ram_FFE776]
- Bonus race fn_005bba: a 200-frame count-in (ram_FFD732) with blinking items while the car stays still, then a count-down race clock from 30 seconds (ram_FFD635 = 3). Item records from ram_FFD426 (x, y, state) appear one at a time: the next appears (state 5 counting down to 1) once the one before is taken by driving slot 0 to it (item x and y 74-93 hex above the car's). A taken item adds 1 to ram_FFD72C, requests sound 87 hex and moves the put-back point to it. The race is won at 1 item on courses 55, 57 and 59 and at 30 on 56 and 58 (where the count is shown and accelerate is forced on): sound 89 hex, the car spins and hops, and on return the lives ram_FFE776 rise by 1. This is the lives change that moves the bonus course on (bullet above). [hypothesis: code_005BBA, ram_FFD72C, ram_FFD72E, ram_FFD732, ram_FFE776]
- Race-number overlay at the start: the season loops set ram_FFED3A; race_main slides the race number within the season (1-10, kept in ram_FFCFB0) across the screen 4 px per frame until ram_FFED3C reaches 350. [hypothesis: race_main, ram_FFED3A, ram_FFED3C, ram_FFCFB0]
- On internal courses 22, 24 and 25 race_main forces accelerate (B) on for every car on every frame and clears brake (A) while the car's speed word is below 320. [hypothesis: race_main, ram_control_p1, slot.speed]
- Rule-mode-1 race positions: every 8 frames fn_008858 ranks the four cars by laps done x 65536 + progress low byte x 4 + (3 - slot), adding 10,000,000 to the slot named by the first word of ram_FFD2BA, 5,000,000 to the second's and so on; it sorts the keys and stores each slot's place x 2 in ram_FFD250-ram_FFD256, drawn as markers at y 150, 168, 186 and 204 (dat_0090E6). This use reads ram_FFD2BA as place order. The loop over ram_FFD2BA counts with a register the routine never sets (it ends at the first zero word). [hypothesis: fn_008858, ram_FFD250, ram_FFD2BA, dat_0090E6]
- Race clock fn_009916: it counts frames in ram_FFD639 up to ram_FFC23E (frames per second, 50 or 60), then seconds and minutes in ram_FFD636, ram_FFD635 and ram_FFD634, and stops before 5:00; it starts after the countdown and the ram_FFD752 delay and stops when slot 0's laps run out. Hundredths are frame x 2 + 1 at 50 frames per second and from the table dat_03BC4C at 60; the drawer fn_009a18 shows the last hundredths digit rounded down to even. [hypothesis: fn_009916, fn_009a18, ram_FFD634, ram_FFC23E, dat_03BC4C]
- Lap display: laps_out_check draws item 28 and slot 0's laps-remaining digit at the right of the screen; the digit flashes on the last lap, at 0 and while ram_FFEC52 is set. [hypothesis: laps_out_check, ram_FFD164, ram_FFEC52]
- A second season loop, code_0012B4, runs head-to-head races against one computer car: game type 1 runs races 0-9, other types 10-24; each race sets rule mode 2 and ram_FFD754; a win (ram_match_winner 1) moves on and raises the win streak, a loss costs a life and repeats the race. [hypothesis: code_0012B4, ram_rule_mode, ram_FFD754, ram_match_winner]

Open questions of this section and what would settle each (neutral names keep their `unresolved:` verdicts in
`config/names/ram.tsv` until then):

- Finishing words in place order (bullet above): settled by the controlled pair P135 (slot 3 held back one lap, values at each write): the words follow finishing order and the places in ram_FFD250 count from 0. [confirmed: P135, ram_FFD2BA, ram_FFD250, t6w_chal_20261013T180957]
- End timer ram_FFD65C: settled by P135 with t6w_chal: three runs, timer 1 the frame after the second finisher, +1 per frame to 200, fill at 51. [confirmed: P135, ram_FFD65C, race_main, t6w_chal_20261013T180957]
- Life loss and the bonus race: settle by play, one run finishing third (lives before and after) and one run of three won races. [hypothesis: code_00102E, ram_FFE776, ram_FFEC38]
- The one-player grid swap of slots 0 and 2: settle by comparing the start positions of a head-to-head and a challenge race on one course. [hypothesis: code_01CE34, P038]
- The mode flag ram_FFD750 (time display, fixed clock values, no scoring) is the time-trial flag: set to 1 by fn_00d3b4 (writer 00D3BA) when the TT Single Race name entry ends (game type ram_FFEB20 = 8), it reads 1 in the `tt_select` and `t7_c0` races and is not written again through race setup; only the boot clears write it in a challenge game from power-on and it is not written in the `challenge_r1` and `h2h_r1` races. TT Challenge (game type 2) not measured. [confirmed: P137, P135, P136, ram_FFD750, race_main, ram_FFEB20]
- Forced accelerate on internal courses 22, 24 and 25: settle with a run on one of them recording the control bytes. [hypothesis: race_main, ram_control_p1]
- The race clock at 60 frames per second: settle with a poke of ram_FFC23E to 60 at race start and the drawn time after 600 frames. [hypothesis: fn_009916, ram_FFC23E]

Located: code_0045CE (race_main: race frame loop, countdown, end timer), code_01CE34 (race setup: grid, per-race block),
code_01F4F0 (lap counting), code_0068D2 (finishing order), code_00102E (challenge season, qualifying),
code_0090EE (race clock fn_009916, lap display), code_00855A (rule-mode-1 ranking in fn_008858); RAM
ram_start_countdown, ram_FFD164, ram_FFD71A, ram_FFD2BA, ram_FFD65C, ram_FFD718, ram_FFEB20, ram_FFE776; probes P005, P038,
P135, P136, P137; writer runs t6w_chal_20261013T180957, t38w_chal_20261016T115943, t38w_chalhold_20261016T115946,
t38w_tt_20261016T115953, t38w_ttmenu_20261016T120300, t38w_chalmenu_20261016T120302.

### Difficulty

Answer: no difficulty setting was found. The computer cars' strength is data: every challenge race carries its own block
of nine words per computer car, copied into the cars' slots at the race start. The values follow the course rather than
rising through the season: Pro Challenge races are not faster on these words.

In plain words, for a reader who wants to rebuild it: there is no easy, normal or hard switch. Each race of a season
carries its own set of numbers for each computer car, nine per car: a top speed, an acceleration-like value, one that
works the other way, and six that shape how the car takes the turns. They are copied into the cars when the race
starts and read while the cars drive. How hard a race feels therefore comes from these per-race numbers together with
the course and the opponents chosen for it; the numbers do not climb through the season, and Pro Challenge races are on
average no faster than Challenge races. A replica gets the same opponents by copying the per-race blocks; what the six
turn words mean exactly belongs to the Opponent AI section.

| Word halved at frame 5 (computer car slot 1, challenge race 1) | Measured effect | Probe |
|---|---|---|
| ram_FFD0E8 (10 to 5) | slower from the start: 249 px covered by frame 200 instead of 462 | P039 |
| ram_FFD0FA (6 to 3) | faster from the start: 328 px covered by frame 160 instead of 269 | P040 |
| ram_FFD0D6 (320 to 160) | same until frame 111, then held at about 2.4 px per frame (base about 4.8 and rising) | P042 |
| ram_FFD700 (288 to 144) | stuck near the start: no lap by frame 1250 (base lap at 1185) | P046 |
| ram_FFD0C4, ram_FFD10C, ram_FFD6F0, ram_FFD6F8, ram_FFD708 | same position to frame 160 (the first straight), different by frame 200 (after the first turn) | P041, P043, P044, P045, P047 |

- Per-race computer parameters: the race record's pointer (copied to ram_FFD70E) leads to 27 words, nine per computer car, copied at the race start into five slot fields and four per-car words: for slot 1 ram_FFD0E8, ram_FFD0FA, ram_FFD10C, ram_FFD0D6, ram_FFD0C4, ram_FFD6F0, ram_FFD6F8, ram_FFD700, ram_FFD708, then the same words + 2 for slot 2 and + 4 for slot 3; the RAM values at challenge race 1 equal the first race's block. [hypothesis: code_01CE34, ram_FFD70E, dat_04454C, P038]
- The cars read these words during the race: halving any one of the nine changed that computer car's driving. [confirmed: P039, P040, P041, P042, P043, P044, P045, P046, P047]
- ram_FFD0D6 (slot field at offset A2) is the computer car's top speed: halved from 320 to 160 the car levelled at about 2.4 px per frame; a unit of 1/64 px per frame (320 = 5 px per frame) fits. [confirmed: P042]
- ram_FFD0E8 (offset B4) acts as acceleration and ram_FFD0FA (offset C6) works the other way (halving it made the car quicker); the remaining six shape the path through turns (steering or line following); their exact roles belong to the Opponent AI section. [hypothesis: P039, P040, P041, P043, P044, P045, P046, P047]
- No rising difficulty: across the 25 race blocks the top-speed word ranges 304-640 (mean 406) in Challenge races and 216-512 (mean 373) in Pro Challenge races, and the acceleration word 8-14 (mean 11.2) and 8-18 (mean 11.3). [hypothesis: dat_04454C, ram_FFD0D6, ram_FFD0E8]
- Head-to-head against the computer also uses such a block: on the same course the computer car's nine words equalled those of challenge race 1's third car. [hypothesis: code_0012B4, ram_FFD70E, P022]
- The head-to-head season (code_0012B4) does not take the block pointer from the race record: it points ram_FFD70E at an 18-byte block (nine words, one car) per race starting at 0x0446AA, which is directly after the 25 records of dat_04454C (25 x 14 bytes). [hypothesis: code_0012B4, ram_FFD70E, dat_04454C]
- Whether Pro modes change anything else (the player's car, the rules) is open. [hypothesis: ram_FFEB20]

Open questions of this section and what would settle each:

- Unit of the top-speed word (1/64 px per frame fits one probe): settle with controlled probes setting ram_FFD0D6 to 256 and 384 on the first straight; the unit predicts levels of 4 and 6 px per frame. [hypothesis: P042, ram_FFD0D6]
- Roles of ram_FFD0FA and the six turn words: settle in the Opponent AI close with controlled probes varying each word on a straight and through one turn. [hypothesis: P040, P041, P043, P044, P045, P046, P047]
- Whether the computer cars adapt to the player during a race (faster when behind, slower when ahead): settle with two runs of one race, the player leading and the player idle, recording the nine words and the computer cars' speeds. [hypothesis: code_01CE34, ram_FFD0D6]
- Pro modes beyond the computer blocks: settle with writer runs at the start of a Pro Challenge race compared with a Challenge race on the same course (player's car words, rule words). [hypothesis: ram_FFEB20, ram_FFD718]

Located: code_01CE34 (block copy at race setup), code_00102E (race record read), dat_04454C (race records); RAM
ram_FFD70E, ram_FFD0D6, ram_FFD0E8, ram_FFD0FA, ram_FFD700; probes P039-P047.

## Group 3: Course

### Track boundary and out-of-bounds

Answer: the course's edges are drawn in a collision map of 8 x 8 px cells, each holding a code. Open road has no code;
walls deflect the car and keep it on the course; fall cells (the edge of a table top or desk) and sink cells (water,
pool-table pockets) take the car off and, after a fixed sequence, put it back on the line of the last checkpoint it
passed, at a standstill. The only penalty is the lost time and speed: no lap, light or place is taken away. A car that
jumps too far along the course in one step (a short-cut) is taken off in the same way as a sinking car.

In plain words, for a reader who wants to rebuild it: the course is a grid of 8 px squares, each holding a code;
most are blank road. To keep the map small, squares are grouped 4 x 4 into 32 px blocks, and the map stores one
number per block that picks one of up to 256 shared block patterns. Once per frame, for each car on the ground, the
game reads the square under the car's centre and acts on its code. Walls are handled apart from this, by the
movement code, which tests three or four points of the car's outline and turns the car away; a wall never takes a
car off. A fall square starts a fixed sequence: the car slides on over the edge, tips and vanishes (91 frames), is
put back at a standstill on the line of the last checkpoint it passed, facing along the course, and may drive 24
frames later, 115 frames (2.3 s) in all. A sink square, or a jump of too many checkpoints at once, runs a shorter
sequence of 45-46 frames. Nothing else is lost: laps, lights and progress stay as they were. The map has no edge test
of its own; every surveyed course closes its playing area with walls, fall squares or sink squares.

Collision map (all units stage pixels): the course is cut into blocks of 32 x 32 px; a block map of one byte per block,
stored column by column (ram_block_map_ptr points to it; width and height in blocks at ram_maps and the word after it, the
height also in ram_FFCFDE), names one of up to 256 block patterns; a pattern (16 bytes each at ram_block_patterns) gives the
codes of its 4 x 4 cells. To read the code under a point the game takes the block from the point's position divided
by 32, then the cell from bits 3-4 of each coordinate. The 42 surveyed courses have maps from 24 to 90 blocks wide and
40 to 96 blocks high (768-2880 px by 1280-3072 px) (P057).

| Code | Found on (of 42 courses) | Effect when under the car's centre |
|---|---|---|
| none (open) | all | road |
| 20, 24-37 | 37 | wall (20 a full cell, 24-37 twenty shaped cells such as diagonals and part-cells): tested at the car's outline, the car is turned away |
| 21 | 36 | fall: the car tips over the edge and is put back (below) |
| 22 | 37 | bump: a small hop (section Ramps and airborne) |
| 23 | 11 | ramp: a jump (section Ramps and airborne) |
| 3F, 40-43 | 10, 4 | sink: the car goes under and is put back; 40-43 are part-cells (40 and 41 sink in the first 5 px of the cell along x and y, 42 and 43 beyond its first 3 px), used at pool-table pockets |
| 38-3B, 3C, 3D, 3E, 44, 45 | 4, 7, 4, 3, 3, 7 | objects and surfaces (section Pickups and hazards) |

What happens at the edge, measured (one-player races; frames at 50 per second):

| Event | Probe | Car taken off | Put back | Driving again | Where |
|---|---|---|---|---|---|
| Accelerate held off a table edge, list course 6 | P054 | frame 361 (fall cell) | 452 (+91) | 476 (+115) | (2307, 2014), on the checkpoint line from (2216, 1938) to (2400, 2122) |
| The same car falls a second time | P054 | 545 | 636 (+91) | 660 (+115) | the same way |
| Car placed on a sink cell, list course 1 | P053 | 121 | 144 (+23) | 167 (+46) | last checkpoint line |
| Car moved by 138 progress steps (refused jump), challenge race 1 | P049 | 101 | 122 (+21) | 146 (+45) | (259, 880), the line it last passed |
| Accelerate held into a wall from the grid, challenge race 1 | P056 | never | - | - | the car stays pinned at the wall at (399, 128) |

- The collision map is read with the layout above: the code under a point comes from the block map at ram_block_map_ptr and the block patterns at ram_block_patterns, in 8 px cells; cars placed on a sink, ramp and fall cell found this way did what those codes predict. [confirmed: P053, P051, P054, code_0418EA, ram_block_map_ptr, ram_block_patterns, ram_FFCFDE]
- Once per race frame each car's surface routine reads the code at its centre (position + 16 px on each axis), keeps it (slot 0 in ram_cell_p1) and acts on it; nothing is read while the car is in the air or during a point pause. [confirmed: P054, P051, code_01EA82, ram_cell_p1, t7w_fall_20261013T183258]
- The computer cars use copies of the same routine (slots 1-3), and further copies serve slots 4-7 with bump, ramp, fall and sink only. [hypothesis: code_01ED8C, code_013BD6]
- Walls are tested separately, at three or four points of the car's outline chosen by its heading, by the car-movement routine: a block numbered 32 or less is wall-free and skipped; inside other blocks a cell with code 20 or 24-37 calls one of 21 shape handlers (table data_0359DE, pointer ram_FFD690) that decides whether the point is inside the solid part and gives the wall's direction. Wall contact and bounce are measured in section Bounce and impulse response (T8). [hypothesis: code_03F834, code_0416A2, data_0359DE, ram_FFD690]
- Ten of the shape handlers (data_041706) test only the point's 2 px step inside its 8 px cell (a = x and 6, b = y and 6) against a diagonal band and answer the wall direction (1024 a full turn): a + b = 6 gives 128 and a = b 384 (slope 1); a - 2b of 0 or 2 and 2b - a of 6 or 8 give 341, a + 2b of 12-14 or 4-6 give 171 (slope 1/2); b - 2a of 0 or 2 and 2a - b of 6 or 8 give 427, 2a + b of 4-6 gives 85 (slope 2). The last handler repeats the 2a - b test with direction 85, so one slope-2 piece answers as another's direction. [hypothesis: data_041706, code_0416A2, data_0359DE, ram_FFD69C, ram_FFD69E]
- A wall never takes a car off the course: with accelerate held into it the car stayed in the driving state, pinned at the wall, for 200 frames. [confirmed: P056]
- Fall: on a fall cell the car's state (`slot.facing_state`) becomes 32; for the next frames it slides 1 px per frame along its heading (one of eight directions) as long as the cell 8 px further on is also a fall cell (15 px in P054), then runs states 33 to 50, about 4 frames each (91 frames from the fall to state 51). [confirmed: P054, code_040E4E, code_040F2A, t7w_fall_20261013T183258]
- Sink: a sink cell (or a refused progress jump, section Lap detection) sets state 59; states 59 to 64 last about 4 frames each (21-23 frames) before state 65. [confirmed: P053, P049, code_01EA82, code_041A84]
- Putting back: at state 51 or 65 the car is placed on the line of its last checkpoint (the line from ram_last_cp_line, ram_FFD19C to the next two words, kept per car, 8 bytes per slot), at the middle of the line's central three quarters for a single player, with its speed and height cleared; its state becomes 66, the reappearing sequence (66 to 71, 24 frames) follows, and it drives again in the course's direction at that checkpoint (one of eight headings, from the progress word). Measured: line (2216, 1938) to (2400, 2122), car placed at (2307, 2014), its top-left corner, i.e. centre 16 px further on each axis, on the line's middle. [confirmed: P054, P053, P049, code_01E218, code_01E504, t7w_fall_20261013T183258]
- The whole interruption costs 115 frames (2.3 s) for a fall and 45-46 frames for a sink or refused jump; the laps-remaining word and the progress word are not changed by it. [confirmed: P054, P053, P049]
- In modes with more than one player each car is put back alone, except when every active car is off the course at the same time: then all are put back together. Placement spreads the cars across the line by the number of players. [hypothesis: code_01E218, code_01E504, ram_FFD372]
- On internal course 44 sink cells act as fall cells, and on internal courses where the line is longer than 140 px (ram_FFECA2) the placement uses only the central 140 px. [hypothesis: code_01EA82, code_01E504, ram_FFECA2]
- The map lookup has no edge test: every surveyed course closes its playing area with walls, fall cells or sink cells (36 have fall cells; of the other six, two use walls only, two sink cells only, two both). [hypothesis: P057, code_0418EA]
- In the eight-car game slots 4-7 have their own surface, movement, checkpoint and sequence-end steps, each run on slot 8 of the slot table and of the per-car word arrays as a scratch car (copied in, shared routine, copied back); a slot 4-7 car whose fall or sink sequence ends is put back alone only while ram_FFD372 is 0, on its checkpoint line in lane 0-3 (slots 4-7), with the slot 0-3 rule: line cut to its central ram_FFECA2 px, an eighth of the way in plus a lane offset, 16 px up, then moved 32 px by the course direction (fn_0149e0). [hypothesis: code_013BD6, fn_014208, fn_014a46, fn_014bde, fn_0149e0, ram_FFECA2]
- Eight-car group put-back: with ram_FFD372 set no car is put back alone; once slot 0 and every other car still in the game have reached the end of a fall or sink sequence (state 51 or 65), all eight cars get one car's progress and checkpoint line and are put back on it together: the car named by the last round end (ram_scorer_idx), else the lower car of the first pair not yet out (its partner 4-7 when it is out); after ram_FFD370 is set the cars still in run the reappearing sequence. [hypothesis: code_013BD6, fn_0146c0, ram_FFD372, ram_scorer_idx, ram_FFD370]
- Fall slide detail: the slide moves 1 px per frame with the cell test only while the car's cell code is 21; a car sent to state 32 on another code (the platform hole of fn_01787a) slides 1 px every other frame without the test. The eight steps come from `slot.movedir` (1024 a full turn) in unequal sectors: 32 units around each axis direction, 224 for each diagonal. With ram_FFEC68 set the slot 0-3 state steps turn state 35 into 46, skipping states 36-45 of the fall sequence. [hypothesis: code_040E4E, code_040F2A, ram_FFEC68]
- Slot 0's put-back spreads by lanes like the others: the line's central part is divided by 3 in the head-to-head season race (ram_FFD754) and by the rule mode + 1 otherwise, slot 0 taking lane 0, and no course-direction offset is added (the slot 4-7 put-backs add 32 px). [hypothesis: code_01E504, ram_FFD754, ram_rule_mode]
- Slots 1-3 put-backs follow slot 0's: each clears its car's hold countdown, counting word and cell code, takes a replacement line and progress word when its progress lies in a range of the course's restart list (fn_01ea44, lists from dat_035B2E by ram_FFD672: progress range, line, progress word), and places the car in lane 1, 2 or 3. A lane's offset is the lane width times (lane + 1) after fn_01e9fe adds the rotation ram_FFEC9C and reduces by the rule mode (not in rule mode 1), so the cars change places across the line as the rotation rises at the point pauses. Only slot 1 has the head-to-head branch (two thirds of the central part, no lane routine). [hypothesis: code_01E66A, code_01E7E2, code_01E928, fn_01e9fe, fn_01ea44, dat_035B2E, ram_FFEC9C]
- Course hooks: one course has three platforms moving 1 px per frame between x 361 and 560 over a hole (x 209-557, y 593-781): a car on a platform rides it, a car in the hole on none falls (state 32). Another has seven objects that collapse when slot 0 reaches given progress values on given laps, each writing 34 into six RAM bytes at offsets 0, 1, 60, 61, 120 and 121 (a 3 x 2 patch of a map stored 60 bytes per column if these are block-map bytes). [hypothesis: data_017870, fn_01787a, fn_017e0e, ram_FFD426, ram_FF5859]
- Part-sink cells: 40 and 42 test the car's x within its 8 px cell, 41 and 43 its y; 40 and 41 sink at 0-4 px, 42 and 43 at 3-7 px, elsewhere in the cell nothing happens. A sink (3F or a part-sink hit) sets state 59 only while the state is below 33, a fall cell state 32 only while it is below 32; on internal course 44 the sink and part-sink cells all act as fall cells. Cars 1-3 run the same tests. [hypothesis: code_01EA82, code_01ED8C]

Open questions of this section and what would settle each:

- Whether the computer cars' surface routines (slots 1-3) fall, sink and put back exactly as slot 0's does: settle with P053 and P054 repeated on computer car slot 1. [hypothesis: code_01ED8C, P053, P054]
- Which part of each of the 20 shaped wall cells is solid: settle with one placement probe per shape code against the shape handler's answer (belongs with section Bounce and impulse response). [hypothesis: code_0416A2, data_0359DE, ram_FFD690]
- Put-back with more than one player (each car alone, all together when all are off, the lane spread): settle with a fall run from a head-to-head state, first one car off, then both. [hypothesis: code_01E218, code_01E504, ram_FFD372]
- Internal course 44 (sink acting as fall) and the 140 px line cut: settle with a sink probe on course 44 and a put-back on a course whose checkpoint line is longer than 140 px. [hypothesis: code_01EA82, ram_FFECA2]
- The eight-car put-back rules: settle with an eight-car race state, which no scenario reaches yet. [hypothesis: code_013BD6, ram_FFD372, ram_scorer_idx]
- The course hooks (moving platforms, collapsing objects) and the shortened fall with ram_FFEC68 set: settle by finding which courses run the hooks and the writer of ram_FFEC68, then one run on each. [hypothesis: data_017870, fn_01787a, ram_FFEC68]

Located: code_0418EA (cell lookup), code_01EA82 (slot 0 surface routine), code_01ED8C and code_013BD6 (other slots),
code_03F834 and code_0416A2 (wall test, shape handlers data_0359DE), code_040E4E (fall slide), code_040F2A (slot 0
state step), code_01E218, code_01E504, code_01E66A, code_01E7E2 and code_01E928 (putting back); RAM ram_block_map_ptr (block map), ram_block_patterns (block patterns),
ram_maps and ram_FFCFDE (map size), ram_cell_p1 (cell under slot 0), ram_last_cp_line (last checkpoint line per car),
ram_FFD690; probes P049, P053, P054, P056, P057; writer run t7w_fall_20261013T183258.

### Lap detection and checkpoints

Answer: each course carries a list of checkpoint areas numbered along the lap. Every frame each car's centre is looked up
in that list; the number found becomes the car's progress, but only if it moved at most 13 checkpoints forward or 14
back since the last frame, otherwise the car is taken off as a short-cutter. A lap counts when the car reaches the start
line having passed through all four quarters of the lap since it was last there; the quarters are not checked for order.
The last checkpoint area passed is kept per car and is the line the car is put back on after a fall, a sink or a
head-to-head point.

In plain words, for a reader who wants to rebuild it: there is no start-line sensor. Each course has a list of
checkpoint areas numbered around the lap from 0 at the start line to 175 (on a course with 88 checkpoints every
number is doubled, so the lap still runs 0-175). Every frame the area holding each car's centre gives that car's
progress number. If the new number is more than 13 ahead or more than 14 behind the old one, counted around the lap,
the move is treated as a short-cut: the number is not taken and the car is taken off and put back as after a sink.
Each car has four flags, one per quarter of the lap (numbers 32-63, 64-95, 96-127 and 128-167), set while its number
is in that quarter. When the number is below 7, just past the line, the flags are checked: all four set takes one lap
off the car's laps-remaining count; either way the flags are then cleared. A lap therefore needs a visit to every
quarter since the car was last at the line, in any order, and the first crossing from the grid counts nothing. The
area last found is kept per car as the line it is put back on.

| Car (challenge race 1, idle) | 1st quarter | 2nd | 3rd | 4th | Lap counted (laps remaining) |
|---|---|---|---|---|---|
| slot 1, lap 1 | frame 225 | 424 | 599 | 780 | 1185 (3 to 2) |
| slot 1, lap 2 | 1524 | 1720 | 1894 | 2070 | 2320 (2 to 1) |
| slot 1, lap 1 with its 3rd-quarter flag cleared at frame 1100 (P048) | 225 | 424 | cleared | 780 | none at 1185 (stays 3) |

| Change made | Probe | Result |
|---|---|---|
| Player's car moved at frame 100 from the grid (progress 174) to a point of progress 36 | P049 | refused: progress stays 174, car taken off at 101 and put back on the grid line |
| Player's car moved from the grid to a point 12 checkpoints on, across the start line | P050 | accepted: progress 174 to 22; laps stay 3 (no quarters passed) |
| Third-quarter flag of computer car slot 1 cleared before it reaches the line | P048 | no lap at the line; flags cleared there as usual |

- Checkpoint lookup: each frame and for each car the routine rounds the car's centre down to 8 px and searches the course's checkpoint lists (pointer ram_cp_lists: two lists of 8-byte records searched by halving, then a list of 10-byte records scanned); a hit yields the record's area, four words kept as the car's last checkpoint line (slot 0 at ram_last_cp_line, 8 bytes per car), and its progress word (ram_car_progress + 2 x slot). [confirmed: code_041A84, ram_cp_lists, ram_last_cp_line, ram_car_progress, t7w_chal_20261013T181944, t7w_fall_20261013T183258, t7w_ramp_20261013T183301]
- The progress word's low byte is the position along the lap, 0 at the start line and rising to the course's checkpoint count (ram_cp_count: 176 on the list courses probed; 88 on challenge race 1's course, where the numbers are doubled so the lap still spans 0-175); its high byte is the course direction at that point (eight directions), used to set a put-back car's heading. The grid lies just behind the line (progress 174 in challenge race 1, 175 on list course 6). [confirmed: P049, P050, P054, ram_car_progress, ram_cp_count]
- Ordering rule: the new position minus the old (counted across the start line) is accepted from 13 checkpoints forward to 14 back; anything else is refused, the progress and last line stay, and the car is taken off as on a sink cell (section Track boundary). The limits are the words ram_cp_ahead_max to ram_cp_wrap_lo (14, -14, 162 and -162 units on 176-checkpoint courses; 28, -28, 148 and -148 on the 88-checkpoint course). [confirmed: P049, P050, code_041A84, ram_cp_ahead_max, ram_cp_wrap_hi]
- A nonzero ram_FFD68C switches the ordering test off (every lookup accepted); the T7 placement probes set it to move the car freely. [hypothesis: code_041A84, ram_FFD68C, P051]
- Lap rule: each car has four quarter flags (slot 0 at ram_quarter_flags, 4 bytes per car), set while its position is in 32-63, 64-95, 96-127 or 128-167; when its position is below 7 (the first checkpoints past the start line) and all four flags are set, its laps-remaining word drops by 1; the flags are cleared whenever the position is below 7, counted or not. So a lap needs all four quarters since the last visit to the start line, in any order. [confirmed: P048, code_01F4F0, ram_quarter_flags, ram_FFD17C, t7w_chal_20261013T181944]
- The first crossing from the grid counts nothing (no flags yet), so "3 laps" are three full laps after the start; a short-cut over the line is not a lap either. [confirmed: P050, P048, t7w_chal_20261013T181944]
- For slot 0 position 6 is excluded from the lap test (only 0-5 count), a quirk of the player's copy of the routine. [hypothesis: code_01F4F0]
- At each counted lap a sound cue (request 5A) is requested for every car. [hypothesis: code_01F4F0, code_01F7F6, code_0156B6]
- Player 1's lap also records the lap time (digits from ram_FFD634, best lap ram_FFD64C) and starts a 150-frame display timer (ram_FFD658); in Challenge races 1-10 a first lap faster than the race's target time requests cue 89. [hypothesis: code_01F4F0, ram_FFD634, ram_FFD64C, ram_FFD658]
- Lap time detail: at slot 0's counted lap, only when the display timer ram_FFD658 is idle, the shown time ram_FFD63A becomes the lap time while ram_FFD750 is set (the clock ram_FFD634 minus the lap start ram_FFD652, digit by digit with borrow, tens of seconds in base 6; a strictly faster lap replaces the best lap ram_FFD64C) and the running clock while it is clear; with it clear the running clock is also shown when slot 0 reaches the position held in ram_FFD65A. [hypothesis: code_01F4F0, lap_step_s0, ram_FFD750, ram_FFD652, ram_FFD65A]
- Challenge target test: on slot 0's first counted lap (laps-remaining 3) in a challenge race (ram_FFEC5A) numbered below 10 (ram_FFD718) with ram_FFD250 at 0, the clock is compared with the race's five-digit entry of dat_043E3A; below it the lap requests cue 89 and sets the end-of-race wait ram_FFD65C to 50, ram_FFD734 to 1 and ram_FFEC5C to 12, which looks like ending the race at once as a win. While digits are equal the compare runs on up to 10 bytes, into the next race's entry. [hypothesis: code_01F4F0, dat_043E3A, ram_FFD65C, ram_FFD734, ram_FFEC5A]
- The lap cue 5A and the laps-remaining drop happen only while that car's laps-remaining word is not 0, so a finished car crossing the line again is silent. [hypothesis: code_01F4F0, code_01F7F6, ram_FFD164]
- The finish is the lap that brings the laps-remaining word to 0 (section Race start and finish); the head-to-head put-back uses the scorer's last checkpoint line, copied to every car (section Out-of-view scoring). [confirmed: P022, P023, code_01E218, ram_FFD164]
- Slots 4-7 keep their progress words (ram_FFD136 to ram_FFD13C) and last checkpoint lines (from ram_FFD1BA, 8 bytes per slot) and run the checkpoint lookup on slot 8's copies (ram_FFD13E, ram_FFD1DA); in the eight-car game the progress low bytes, with the head-to-head wrap correction, also rank the eight cars for the elimination pick. [hypothesis: code_013BD6, fn_0145d8, fn_0152aa, ram_FFD136, ram_FFD1BA]
- Checkpoint list layout: three lists behind ram_cp_lists: lines of one y (8-byte records, searched by halving on the point's 32 px y band, hit with x strictly between the ends), lines of one x (the same across), then 10-byte records of other lines scanned along x with a 10 px closeness test; the header's two words give the offsets of the second and third lists, and the third holds ram_cp_count less the second offset / 8 records. [hypothesis: code_041A84, ram_cp_lists, ram_cp_count]

Open questions of this section and what would settle each:

- Slot 0's lap window 0-5 against 0-6 for the other cars: settle with a probe placing slot 0 at progress 6 with all four flags set (lap counted or not). [hypothesis: code_01F4F0, ram_quarter_flags]
- Who sets ram_FFD68C in normal play (the probes set it by hand): settle with a writer run over a whole race in each rule mode. [hypothesis: ram_FFD68C, code_041A84]
- Lap time, best lap and the target-time cue 89: settle with a challenge race writer run on ram_FFD634 and ram_FFD64C together with the sound-request tap; whether a first lap under the target ends the race as a win (ram_FFD65C, ram_FFD734): settle with one challenge race 1-10 run beating the target. The mode that sets ram_FFD750 (lap time against running clock) is time trial (P137, Race start and finish). [hypothesis: ram_FFD634, ram_FFD64C, code_01F4F0, ram_FFD750, P137]
- Whether every course has 176 or 88 checkpoints (the ordering limits are only measured for those two): settle by recording ram_cp_count in each state of the 42-course survey. [hypothesis: ram_cp_count, P057]
- The checkpoint list layout (three lists, halving search, 10 px closeness for other lines): settle with placement probes between two lines of one y and near a diagonal line. [hypothesis: code_041A84, ram_cp_lists]
- Slots 4-7 checkpoints and the eight-car ranking: settle with an eight-car race state. [hypothesis: code_013BD6, ram_FFD136]

Located: code_041A84 (checkpoint lookup and ordering test, per-slot copies), code_01F4F0 (quarter flags, lap count,
lap time), code_01F7F6 (lap cue); RAM ram_cp_lists (checkpoint lists), ram_car_progress (progress per car), ram_last_cp_line
(last checkpoint line per car), ram_quarter_flags (quarter flags), ram_cp_count (checkpoint count), ram_cp_ahead_max to ram_cp_wrap_lo
(ordering limits), ram_FFD68C, ram_FFD164 (laps); probes P048, P049, P050; writer runs t7w_chal_20261013T181944,
t7w_fall_20261013T183258, t7w_ramp_20261013T183301.

### Ramps and airborne

Answer: a jump is a height above the ground kept beside the slot table, not a third axis of it: per car a height word
(slot 0 ram_car_height, + 2 per slot) and a vertical speed word (slot 0 ram_car_vspeed). Driving onto a ramp cell sets the
vertical speed from the car's speed; each frame gravity takes 1 off the vertical speed and the height moves by a step
looked up from it; on touching the ground the car bounces with about half its vertical speed until it settles. While in
the air the car keeps its speed and direction, ignores the cells below it and can clear walls once high enough. Ramp
cells exist on 11 of the 42 surveyed courses, bump cells (small hops) on 37 (P057).

In plain words, for a reader who wants to rebuild it: a jump does not lift the car into a third dimension of its
movement. The car goes on across the map at the speed it had, and a separate height number, drawn as the sprite
raised above its shadow, rises and falls. A ramp square gives the height an upward speed of the car's speed / 16 (at
most 32), a bump square the car's speed / 32 (at most 8). Each frame the upward speed drops by 1 and the height moves
by about a quarter of it (from a small table). When the height would go below 0 the car lands and bounces up with
about half the upward speed it had, again and again, until the bounce is too small to lift it. In the air the car
keeps its speed and direction, cannot steer or brake, ignores the squares beneath it and passes over walls once high
enough; landing on a fall or sink square acts at once. Two cars only touch when their heights are within about 6 px.
At 6.5 px per frame a ramp jump lasts 49 frames, peaks at 89 px and lands 320 px further on.

Height series measured (list course 1, internal course 2, car placed before a ramp heading right, accelerate held;
P051 and P052; bump on Ball Chase P055). Heights in stage pixels, frames from the take-off frame t:

| Run | Car speed (1/64 px per frame) | Vertical speed at take-off | Height at t+5, +10, +15, +20 | Peak (frames) | Landing | Bounces (peak heights, landings) |
|---|---|---|---|---|---|---|
| P051, ramp | 414 (6.5 px per frame) | 25 | 30, 55, 74, 86 | 89 px (t+23 to t+26) | t+49, 320 px further on | 22 px, t+73; 5 px, t+85; 1 px, t+91 |
| P052, ramp | 241 (3.8 px per frame) | 15 | 19, 31, 34, 29 | 34 px (t+13 to t+16) | t+29 | 7 px, t+43; 1 px, t+49 |
| P055, bump | 402 (6.3 px per frame) | 8 | 8, 8, 0, - | 9 px (t+6 to t+9) | t+15 | 2 px, t+23 |

- Take-off: on a ramp cell (23) the vertical speed becomes the car's speed divided by 16, at most 32; on a bump cell (22) the car's speed divided by 32, at most 8. Measured: speed 414 gave 25, speed 241 gave 15, the bump at speed 402 gave 8 (12 capped). [confirmed: P051, P052, P055, code_01EA82, ram_car_vspeed, t7w_ramp_20261013T183301, t7w_bc_20261013T182331]
- Flight: each frame the vertical speed drops by 1 and the height changes by a step from a table indexed by the vertical speed (about a quarter of it: 6 px per frame at 20-24, 5 at 15-19, 4 at 11-14, 3 at 8-10, 1 at 2-3, 0 at 1; 8 beyond 63); a 25 take-off peaks at 89 px and stays up 49 frames, a 15 take-off peaks at 34 px and stays up 29 frames. [confirmed: P051, P052, code_040F2A, data_038644, ram_car_height]
- Landing: when the height would go below 0 it is set to 0 and the car bounces up again with half its vertical speed less a thirty-second of it (ram_bounce_sw set, as in every run here; when that word is 0 the bounce is half less a quarter); bounces go on until the speed is too small to lift the car, so a ramp jump ends with two or three ever smaller hops. [confirmed: P051, P052, P055, code_040F2A, ram_bounce_sw]
- The car's driving speed does not change in the air: it stayed 414 through P051's flight and 241 through P052's, and rose again from the first landing frame. [confirmed: P051, P052]
- While the height is not 0 the surface routine reads no cell, so a jumping car crosses fall and sink cells unharmed; landing on one acts at once (P051's car landed and then reached a fall cell at t+113). [confirmed: P051, code_01EA82]
- In the air the car cannot steer or brake, and its wall test is skipped while the height is 14 px or more or the car still rises with vertical speed 6 or more, so high jumps clear walls. [hypothesis: code_03F834, ram_FFD150]
- Two cars are tested for contact only when the height difference (this car minus the other) is -6 to 5 px, so a car high in a jump passes over another (section Car-to-car collisions). [confirmed: P067, P071, code_00635E, ram_car_height]
- Drawing: the car's sprite is drawn raised by its height (up and left by half of it, section Out-of-view scoring) while its shadow stays on the ground. [hypothesis: code_0090EE, ram_car_height]
- Sound cues: take-off from a ramp requests cue 6A and from a bump 6B, only when the car is in view and its vertical speed is above 4; landing requests 6D (vertical speed above 4) or 55 (4 or less), and 86 on internal courses 15 and 43. Cues 6D, 6D and 55 were logged at P051's three landings in a repeat run with a sound-request tap. [hypothesis: code_01F48E, code_040F2A, code_0156B6]
- Slots 4-7 take off by the slot 0 rule (bump: speed / 32, at most 8; ramp: speed / 16, at most 32) into their own vertical speed words ram_FFD15A to ram_FFD160, read no cell while their height words ram_FFD148 to ram_FFD14E are not 0, and run the height step height_step on those words before each move. [hypothesis: code_013BD6, fn_013fb8, fn_014208, ram_FFD15A, ram_FFD148]
- A landing cue needs the vertical speed after the bounce to be above 2 and the car's in-view flag; on internal course 15 the speed test compares the cue number instead of the vertical speed, so every landing there requests 86, as on course 43. [hypothesis: code_040F2A, height_step, ram_FFD672]

Open questions of this section and what would settle each:

- No steering or braking in the air, and walls cleared at 14 px or while rising at 6 or more: settle with a probe holding left during P051's flight and one jumping a ramp toward a wall. [hypothesis: code_03F834, ram_FFD150]
- The other bounce rule (half less a quarter when ram_bounce_sw is 0) and what sets that word: every run had it set; settle with P051 repeated with the word cleared before take-off, and a writer run from power-on. [hypothesis: ram_bounce_sw, P051]
- The landing cues on internal courses 15 and 43 and the course-15 test quirk: settle with a sound-request tap run landing a jump on course 15. [hypothesis: height_step, code_040F2A]
- The sprite raised by half the height: settle with the sprite table read during P051's flight. [hypothesis: code_0090EE, ram_car_height]
- Jumps of slots 4-7: settle with an eight-car race state. [hypothesis: code_013BD6, ram_FFD148]

Located: code_01EA82 (take-off), code_040F2A (height step and landing for slot 0; copies for slots 1-3 in the same
region), data_038644 (height step table), code_03F834 (no steering or walls in the air), code_01F48E (cues); RAM
ram_car_height (height per car), ram_car_vspeed (vertical speed per car), ram_bounce_sw; probes P051, P052, P055, P057; writer
runs t7w_ramp_20261013T183301, t7w_bc_20261013T182331.

### Pickups and hazards

Answer: nothing on the courses is collected. Everything that affects a car is a cell code of the collision map (section
Track boundary), acted on while the car's centre is over it and the car is on the ground: besides walls, falls, sinks,
bumps and ramps there are slow cells, slippery cells, bounce cells, drift cells, a counting cell and four trigger
objects per course that can open into holes. Which course has which comes from the 42-course survey (P057).

In plain words, for a reader who wants to rebuild it: there is nothing to pick up and nothing is used up. Every
hazard is a square code of the course map, acting while the car's centre is over it and the car is on the ground. A
slow square holds the car at 1 px per frame while it is on it. A slippery square starts a 50-frame low-grip timer,
the same timer a too-long held accelerate starts at the race start: while it runs the car's acceleration, drag and
grip numbers become 6, 1 and 2, and a turn slides much further (section Drift and traction, P090). A bounce square
throws the car up, sets its speed to 4 px per frame and turns it a little at random. A drift square pushes the car
down the stage by a per-course amount each frame, like a current. A counting square only raises a counter. Four
trigger objects per course count how long a car touches them and, touched long enough, open into holes that act as
fall squares. The slow, slippery, bounce and object squares request their own sound cues when the car is in view.

| Code | Courses (list numbers) | Effect, measured or from the code | Probe |
|---|---|---|---|
| 45 slow | 3, 13, 21, 23, 26, 34, 35 | speed cut to 64 (1 px per frame) on the first frame and held there while on the cell; normal acceleration after it | P060 |
| 3C slippery | 5, 10, 13, 19, 34, 37, 39 | a 50-frame timer starts (5 frames on internal course 14, where such cells cover most of the course); while it runs the car's three grip words are replaced by 6, 1 and 2 (8, 3 and 8 on that course otherwise) | P061 |
| 3E bounce | 6, 14, 16 | the car is thrown up with vertical speed 23 and its speed set to 256 (4 px per frame); lands and is thrown again while still on such cells | P058 |
| 44 counting | 1, 27, 40 | a counter (ram_count_cell) rises 1 per frame on the cell and is reset after it; no effect on the car was seen | P059 |
| 3D drift | 10, 14, 22, 37 | the car is pushed down the stage by ram_FFD6DA px per frame (a per-course value: 0, 1, 2, 4 or 5) | - |
| 38-3B objects | 9, 36, 38, 41 | touching one of the course's four objects counts up; held long enough it opens and its cells become fall cells | - |

- No collectable items: the surface routines read only the cell codes listed here and none of them gives a car anything or is removed after use. [hypothesis: code_01EA82, code_01ED8C, P057]
- Slow cell (45): on it a car faster than 64 is cut to 64 at once and stays at 64 while it remains on the cell (17 frames, 1 px per frame, in P060), then accelerates normally; the cut requests cue 4F when the car was faster than 128 and is in view. On internal courses 62 to 64 the cell also counts like code 44. [confirmed: P060, code_01EA82, code_01F48E]
- Slippery cell (3C): entering one sets the slip timer (slot 0 ram_low_grip_timer) to 50, counted down 1 per frame; while it runs the movement routine replaces the car's grip words (slot 0 ram_accel, ram_drag, ram_grip, the same slot fields that hold the computer cars' per-race parameters, section Difficulty) with 6, 1 and 2; their exact effect on handling belongs to section Drift and traction. Entering with the timer at 0 requests cue 7B (7C on internal courses numbered 10 or below) when in view. [confirmed: P061, code_01EA82, code_03F834, ram_low_grip_timer]
- Bounce cell (3E): vertical speed 23 (a 77 px hop lasting 45 frames in P058), car speed set to 256 and, except on internal course 45, the heading turned by a random amount of up to about 11 degrees either way; the car is thrown again each time it lands on such a cell; cue 50 (4A on internal course 36) when in view. On internal course 30 the cell instead hands the car's speed and heading to another object (ram_FFD272, ram_FFD284, ram_FFD296). [confirmed: P058, code_01EA82, code_01ECDC]
- Counting cell (44): the counter ram_count_cell went 1 to 9 over the 9 frames the car spent on the cell and back to 0 after it; speed and course were unaffected; no reader of the counter was found. [confirmed: P059, code_01EA82, ram_count_cell]
- Drift cell (3D): the car's height and vertical speed are cleared and it is moved down the stage by the per-course word ram_FFD6DA every frame, a current or conveyor. [hypothesis: code_01EA82, ram_FFD6DA]
- Trigger objects (38-3B): each course has four object records of 8 bytes from ram_FFD426 (position, state, touch counter); a car on an object's cells adds 1 to its counter per frame (cue 53 at the first touch, except on internal course 24), the counter falls 1 every 4 frames, and at 9 the object starts opening (cue 54), stepping its state every 4 frames from 1 to 6; in state 6 its cells act as fall cells. [hypothesis: code_01EA82, code_01ECDC, code_0182BC, ram_FFD426, ram_FFD42A]
- Sound cues found for these events: 4F slow, 7B and 7C slippery, 50 and 4A bounce, 53 and 54 objects (the falls, ramps and laps of the sections above use 6A, 6B, 55, 6D, 86 and 5A); all go through the sound request routine at code_0156B6. [hypothesis: code_0156B6, code_01F48E, code_01ECDC, code_0182BC]
- Trigger objects 0 and 1 (records at ram_FFD426 and ram_FFD42E) are stepped by fn_0182bc, the hook of internal course 1, also called first by fn_018014: a touch counter of 9 requests cue 54, sets the state to 1 and clears the counter; another nonzero counter falls by 1 every 4 frames while the object is drawn shaken by -1 to 2 px in x; the object is drawn in four pieces per state (32 bytes per state, table dat_03BD8C) until state 6, the open state, which is not drawn. [hypothesis: code_0182BC, fn_0182bc, ram_FFD426, ram_FFD42A]
- Course 18 catch (fn_018424): a car whose cell code is 38 starts a 100-frame countdown (ram_FFD260 to ram_FFD266). In a one-player race (rule mode 1) a car caught on that cell in fall state 42 is held off the course at stage (214, 1266) (cars 1-3 in state 38, car 0 in state 8 with its controls cleared) until the countdown ends, then dropped back in driving: state 8, vertical speed 10 (a hop), speed 384 (6 px per frame), movedir 256 and progress word 273 hex. In the other rule modes the first countdown to reach 1 sets every other car on the ground (state below 33) to state 52 and runs the point steps with ram_point_pause_count and ram_scorer_num, and data_018A5C releases and holds the cars. [hypothesis: code_0182BC, fn_018424, data_018A5C, ram_FFD260, ram_FFD716, ram_rule_mode]
- Per-course objects: the hooks of courses 20, 21, 27, 29 and 30 move their own objects in the shared scratch words from ram_FFD426 and test the four cars against them. Course 21: two items move 2 px per frame along y between 416 and 1200 and push cars that touch them. Course 27: two objects orbit (x by a 64-step table, y at twice the rate); a car on the ground under one is thrown up with vertical speed 25, slowed to speed 64 (1 px per frame), sent at movedir 778 and turned by one heading step per frame for 50 frames. Course 30: two shuttles accelerate and brake along y and push a touching car away at speed 448 (7 px per frame). Course 29: eight movers circulate on two-lane loops, stop at fixed lines while a progress-started 23-step cycle holds its stop word, and a moving one throws a car it hits at speed 384 in a random direction, a stopped one turns it half round. [hypothesis: code_01B936, code_01ACFC, fn_01b9fa, fn_01bc64, fn_01afac, fn_01bf7a, ram_FFD272]
- Course 27 changes map bytes during the race: when a car's progress word reaches 495 hex or 22F hex with 3 or with 2 laps left, the byte writer at 0x017E02 writes one of four lists (only car 0 is tested in rule mode 1). Course 62 rewrites bytes every frame from one of two lists chosen by its scenery frame. [hypothesis: fn_01bc64, fn_01ae44, code_01B936, code_01ACFC]
- On courses 22, 24 and 25 each car's height word is set to its speed / 128 every frame outside a point pause, so cars are drawn raised in proportion to speed. [hypothesis: fn_01acfc, code_01ACFC, ram_car_height]
- Trigger objects 2 and 3 are also stepped by a course hook (fn_018014): while a touch counter other than 9 counts down the object is drawn shaken by -1 to 2 px in x; a counter of 9 calls 0x018372, sets the state to 1 and clears the counter, and the state then steps every 4 frames up to 6. The course hooks fn_017cd2, fn_017b36 and fn_0180d0 set the drift push ram_FFD6DA to 1, 2 and 4 on every frame they run. [hypothesis: code_018014, data_017870, ram_FFD436, ram_FFD6DA]
- Trigger object touch detail: a touch counts only while the object is closed (state 0) and ram_FFD750 is clear, once per touching car per frame (cars on the same object add up), even off view; the first-touch cue 53 needs the touching car in view; cells of an open object (state 6) act as fall cells, and cells of an opening one (states 1-5) do nothing. [hypothesis: code_01ECDC, code_01EA82, fn_01ed54, ram_FFD42A, ram_FFD42C, ram_FFD750]
- Bounce cell detail: the random turn is (random byte and 63) - 31 movedir units, -31 to 32 of 1024; it is skipped on internal course 45 and, for cars 0 and 2 only, while ram_FFD750 is set (the copies for cars 1 and 3 lack that test). On internal course 30 a car faster than 150 instead stores speed / 16, movedir and speed in per-car words (ram_FFD272, ram_FFD284, ram_FFD296 for car 0, + 2 per car), and a slower car is not affected at all. [hypothesis: code_01EA82, code_01ED8C, fn_01f23a, ram_FFD750, ram_FFD284, ram_FFD296]
- Per-car copies: cars 1-3 keep their own counting words (ram_FFD2AA to ram_FFD2AE, after ram_count_cell), slip timers (ram_FFD2D4 to ram_FFD2D8) and cell codes (ram_FFD208 to ram_FFD20C), and each event's cue needs that car's own in-view word (ram_FFD1E4 to ram_FFD1E8), so a computer car's ramp, slippery, bounce or slow cue sounds whenever it is in view. [hypothesis: code_01ED8C, ram_FFD2AA, ram_FFD1E4, code_01F48E]
- Courses 20 and 21 catch (the table data_03691A hooks, the course 18 catch with other numbers): a car on cell code 38 starts a 130-frame (course 20) or 90-frame (course 21) countdown; in rule mode 1 a car caught there in state 42 is held at stage (1544, 1812) or (246, 1124) until it ends, then dropped back with vertical speed 10 and speed 384. In the other rule modes a countdown reaching 1 decides the point: cars in state 52 are counted out (state 73, ram_FFD662, ram_FFD666, ram_FFD668) and the car left scores (rule mode 2 and 3 with two or three cars). [hypothesis: fn_018db2, fn_019530, data_018DB2, ram_FFD260, ram_FFD716]
- Counting-cell sink (internal courses 6 and 33): a car whose counting word (ram_count_cell, ram_FFD2AA to ram_FFD2AE) passes 20 is set to the sink state 59 while its state is below 33; at 20 or less the word is cleared once the car leaves cells 44 and 45 hex; every fourth count a car in view leaves a splash (sound 85 hex). So the counting square is a slow sink on these courses. [hypothesis: fn_019cc6, fn_01a01c, data_018DB2, ram_count_cell, ram_FFEAB0]
- Course 34 moving object: cars inside a 100 x 128 px box of it are aboard and move with it; while any car is aboard it waits 50 frames, then drifts right 1 px per frame up to x 1022, and drifts back left to 738 when none is; a car not aboard inside x 595-973, y 176-465 falls (state 32). [hypothesis: fn_01a0a6, data_018DB2, ram_FFD426, ram_FFCF8A]
- Hopper (internal courses 4 and 51 and the kit race, course 66, on its piece-15 square): an object hops 8 px per frame between 16 target x offsets, lands, and at count 12 of its 16-count cycle throws any car within about 22 px (vertical speed 8, speed 200, random movedir, cue 17 hex). The kit race hook also runs one effect by ram_FFEDCF: 1 random sounds and scattered items, 2 drifting objects with a sound, 4 a random palette flash. [hypothesis: fn_01a4c8, fn_01a76c, fn_01a970, data_01A4C8, code_01A968, ram_FFEDCF, ram_FFD4EE]
- Course 18 shuttle (the table data_03680E hook): an object travels along y between 456 and about 1994 in about 503 frames (64-step table dat_03BA3C, 6 px per frame at first, then fewer). It sets off when a car reaches progress word 438 hex while it is above y 1000 (car 3 is not tested) and comes back at progress 85 hex (86 hex too for car 0) while below; each start requests sound 60 hex and writes two byte lists through the writer at 0x017E02. While moving it throws a car in its box at speed 448 (7 px per frame) in a random direction. The hook also runs the course 20 object A, moved to y 2044 or 18 at progress 572 hex and 218 hex; a car touching it is turned half round with speed at least 200, at its ends sent along y (movedir 0 or 512) with sound 60 hex at most once per 10 frames. [hypothesis: fn_01b42a, data_01B42A, ram_FFD436, ram_FFD430, dat_03BA3C, ram_FFD74C]
- Course 47: two objects start at progress 466 hex and 478 hex with the looping sound 69 hex, each moving about 47 px one way and back at 1 px per 4 frames (about 376 frames), the sound stopped at the end; a car within reach of a running one (x difference below 150, y difference 77-149) has its movedir reversed and folded into 128-896 and its speed set to 256. [hypothesis: fn_01c760, data_01C760, code_01C964, ram_FFD426, ram_FFD430]
- Course 48: two objects with a swinging part (offset ram_FFD430 stepped by the 64-word table dat_03B9BC of -4 to 4) push a car in their box back (movedir + 512, speed + 32, vertical speed 4, a small hop); course 49 has animated scenery only (16 items at two places). Both hold a looping sound (4C hex, 68 hex) while any of their items is on view, using ram_FFD74C as the on-view count like courses 62 and 63. [hypothesis: fn_01c9f2, fn_01cc68, code_01C964, ram_FFD74C, dat_03B9BC]
- Course 5 (the table data_03691A hook): a carrier like course 34's: one object moves 2 px per frame between x 640 and 1022 but is drawn and carries cars only within 734-926, so it stands still for about 95 frames at each end; a car in its 98 x 80 px box rides it (ram_FFCF8A to ram_FFCF90 = 2) and a car not aboard inside x 593-879, y 143-237 falls (state 32). Course 60: four animated items with a random flip each frame, and a palette list chosen by how near the view is to four points (only with the view y above 200). [hypothesis: fn_017044, fn_01725e, code_017044, ram_FFCF8A, ram_FFC27A, dat_017402]
- Course 18 point decision outside rule mode 1 (data_0186DA, after a catch countdown reaches 1): rule mode 2: when one of cars 0 and 1 is in state 52 the other scores (only the scorer index is written); rule mode 3: the first of cars 0-2 in state 52 is put out (state 73, ram_FFD662) and the next one in state 52 ends the round with the car left scoring; rule mode 4: cars in state 52 are put out one by one into ram_FFD662, ram_FFD666 and ram_FFD668, the third ending the round. The scorer is placed at stage (224, 2290) with progress word 572 hex; the other cars take state 52 and progress word 671 hex. [hypothesis: data_0186DA, code_0182BC, code_0186A0, ram_FFD662, ram_FFD666, ram_FFD668, ram_scorer_idx]
- Course 26 (the table data_03691A hook, data_016E26): a four-item object (items 53-58 hex, a frame every 4 frames, the four quarters mirrored) drawn at stage (770, 1500) to (802, 1540); a car on the ground with vertical speed below 25 inside x 770-840, y 1510-1580 (car position + 139, + 149), or just right of and below the point ram_FFD442, ram_FFD444, is thrown up (vertical speed 25, speed 64, movedir 778) and spun one heading step per frame for 50 frames while its state is below 32. [hypothesis: fn_016e26, data_016E26, ram_FFD272, ram_FFD426]
- Course 23 (code_017444): three objects at stage (1183, 928), (1535, 896) and (1535, 1120) cycle every 128 frames (64 at rest, 12 changing, 40 in the other state, 12 back; the third 31 frames later), each rewriting a 4 x 3 patch of block-map bytes per stage (rest D2 00 00 D3 on each row, the other state 51 CF CF 50, 22 22 22 22, 5B CC CC 5A) with a matching item list; which state lets cars across is open. [hypothesis: fn_017444, code_017444, dat_01755E, dat_01753A, dat_017552, ram_FF56DB]
- Course 61 (the table data_03680E hook, code_01ABD4): when idle, one frame in 64 starts a burst: twelve pairs of items (52-59 hex, the second 800 px below the first) from stage x 611-783, y 1064 move down 4 px per frame for about 30 frames, spreading by -3 to 3 px per frame in x; the drift push ram_FFD6DA is 2 while a burst runs and 0 otherwise, and sound 19 hex marks a start in view. [hypothesis: fn_01abd4, code_01ABD4, ram_FFD476, ram_FFD6DA, ram_FFD74C, dat_01ACE4]
- Other small hooks of the table data_03691A: courses 22, 24 and 25 (fn_017728) clear the heights of cars 0-3 every frame outside a point pause; course 66, the kit race (fn_017744), re-renders the piece-15 block art every frame into ram_FF900C, which code_017850 sends to VRAM, shifted against the view ((511 - view x) / 2 px across and (224 - view y) / 4 rows down, mod 32); course 14 (fn_01a406) sets the slide bounds ram_FFD6B0 and ram_FFD6B2 to FF00 and 100 hex, the value at which the marks routine does nothing; course 42 (fn_01a414) sets the steering period of cars 0-3 by speed: 3 up to speed 200, 4 up to 400, 5 above. [hypothesis: code_017728, code_01A406, ram_FF900C, ram_FFD6B2, ram_steer_period]

Open questions of this section and what would settle each:

- The drift square's push (no probe yet): settle with a placement probe on a drift square of list course 10, measuring the move per frame against ram_FFD6DA. [hypothesis: ram_FFD6DA, code_01EA82]
- Trigger objects opening into holes: settle with a probe holding a car on an object square of list course 9 for 40 frames and recording the object record and the car's state. [hypothesis: ram_FFD426, code_0182BC, code_01ECDC]
- What the counting square is for on list course 1 (the only reader found is the internal courses 6 and 33 sink of data_018DB2): settle with a read watchpoint on ram_count_cell over a whole race on list course 1. [hypothesis: ram_count_cell, P059]
- The special cases on internal courses 30 (bounce hands the car to another object) and 62-64 (slow squares also count): settle with one run on each course. [hypothesis: code_01ECDC, code_01EA82]
- Which courses run the drift-push hooks fn_017cd2, fn_017b36 and fn_0180d0: settle by locating the course-hook dispatch for each course number. [hypothesis: data_017870, ram_FFD6DA]
- The course 18 catch and release and the per-course objects of courses 20, 21, 27, 29 and 30 (no scenario reaches these courses): settle with one run on each internal course, driving into the objects, with a writer run on the scratch words from ram_FFD426. [hypothesis: fn_018424, data_018A5C, code_01B936, code_01ACFC, ram_FFD426]

Located: code_01EA82 (slot 0 surface routine, every code above), code_01ED8C (slots 1-3), code_01ECDC (object touch,
bounce cue), code_0182BC (object opening, course 18 catch), data_018A5C (course 18 release), code_01ACFC and code_01B936
(course hooks of courses 20-30, 39, 52, 62, 63), data_018DB2, data_01A4C8 and code_01A968 (course hooks of courses 4, 6, 20, 21,
33, 34, 51, 66), data_01B42A, data_01C760, code_01C964 and code_017044 (course hooks of courses 5, 18, 47, 48, 49, 60),
data_0186DA (course 18 point steps), data_016E26, code_017444, code_017728, code_01A406 and code_01ABD4 (course hooks of
courses 14, 22-26, 42, 61, 66), data_03680E and data_03691A (course hook tables), code_03F834 (slip words
applied); RAM ram_low_grip_timer (slip timer), ram_count_cell, ram_FFD6DA, ram_FFD426 and ram_FFD42A (objects, a per-course
scratch area); probes P057, P058, P059, P060, P061.

## Group 4: Collisions

### Car-to-car collisions

Answer: once per race frame, after every car has moved, the game tests the pairs among the four cars in a fixed order,
(0,1), (0,2), (1,2), (0,3), (1,3), (2,3), skipping a pair whose car slot is not in use. A pair goes on to the precise
test only when the cars' positions differ by -23 to 24 px on both axes (the other car's position minus this one's),
their heights above the ground differ by less than about 6 px, and neither car is off the course (falling, sinking or
in a put-back sequence). The precise test checks the four corners of each car's collision area against the other car's
area (section Collision areas). On contact the two cars swap their velocities, each keeping 1/64 of its own, and both
get a fixed shove apart; nothing is decided by chance except the sound. All units below: positions in stage pixels,
speeds in 1/64 px per frame (64 = 1 px per frame, 50 frames per second), directions in 1024 steps per turn (0 up, 256
right, 512 down, 768 left).

In plain words, for a reader who wants to rebuild it: after all four cars have moved in a frame, the game looks at
each pair of cars once, always in the same order. A pair is only examined closely when the cars are within about
24 px of each other along both axes, at nearly the same height (less than about 6 px apart, so a car high in a jump
passes over the other) and both on the course (not falling, sinking or being put back). The close look asks whether
a corner of either car's rectangle (section Collision areas) lies inside the other's. If one does, the two cars trade
their movement: each leaves with almost exactly the velocity the other had, plus a small push of about 0.76 px per
frame away from the other on the side of the touching corner, and never slower than 30 units (about 0.5 px per
frame). There is no weight, no damage and no chance involved, except in which crash sound plays. A computer-driven
car that is hit lets go of its controls for 8 frames (16 in some race setups) and coasts. Cars do not collide during
the start countdown, and the eight-car game has its own copy of the pair test that no recorded run has reached.

| Placement (multi_r1: four-player race, cars on the grid, both facing up) | Result | Probe |
|---|---|---|
| Player 1's car 19 px above player 2's, same x | contact (corner 3): both cars pushed apart at speed 45 | P062 |
| 20 px above | no contact; the quick test passed, the precise test failed | P063 |
| 13 px to the left, 1 px higher | contact | P064 |
| 14 px to the left, 1 px higher | no contact | P065 |
| 10 px to the left at exactly the same height | no contact (see Collision areas) | P066 |
| 19 px above and 12 px off the ground | no contact while it falls; contact at the frame its height is down to 5 or less | P067 |
| 30 px above, moving down at 400 into the standing car | contact on the 2nd frame: the standing car leaves at 439, the mover bounces back at 42 | P068 |
| 19 px above, but in off-course state 33 | not tested for 40 frames | P073 |

- The pair test runs after the cars' movement in the race frame (routine fn_006378, called from the race loop) and covers the six pairs of the four cars in the order (0,1), (0,2), (1,2), (0,3), (1,3), (2,3); a pair is skipped when one of its cars has its in-use word (ram_FFD022 for slot 1, + 2 per slot) at 0, and the whole test is off while ram_FFD750 is set. With the in-use words of slots 2 and 3 cleared only pair (0,1) was tested. [hypothesis: fn_006378, code_00635E, code_0045CE, ram_FFD022, ram_FFD750, P071]
- Quick test: the pair goes to the precise test only when the other car's position minus this car's is -23 to 24 px on each axis (an asymmetric 48 px window), the height difference (this car's minus the other's, ram_car_height per car) is -6 to 5 px, and both cars' state words (`slot.facing_state`) are below 32. Measured: placements outside -23..24 were never tested; heights 5-0, 0-6, 10-5 and 20-26 were tested, 6-0, 7-0, 0-7, 10-4 and 20-27 were not; states 31 and 16 were tested, 32 and 40 not. [confirmed: P071, P063, P067, pair_test_s0, pair_test_sj, ram_car_height, slot.facing_state]
- Precise test: the corners of this car's collision area are tested against the other car's area, then the other car's corners against this one; the first corner found inside (numbered 1-4 for this car's, 5-8 for the other's) is kept in ram_hit_corner and decides the direction of the shove. In 10,507 distinct placements over two states the measured contact, corner number included, was exactly what this test predicts. [confirmed: P062, P064, P071, fn_0068d2, code_0068D2, ram_hit_corner, ram_corner_pos]
- Response: the two cars' motions (direction `slot.movedir` and speed `slot.speed`) are turned into velocity vectors, each car's vector keeps 63/64 and gains 1/64 of the other's, a fixed shove of 48.8 speed units (0.76 px per frame) is added in opposite directions along the axis or diagonal of the touching corner, and the two results are then exchanged, so each car leaves with (almost all of) the other's velocity plus the shove; a speed below 30 is raised to 30. 23,490 of 23,498 measured contacts fit within 3 direction units and 3 speed units (section Bounce and impulse response). [confirmed: P068, P062, P071, fn_0068d2, fn_040d14, fn_040b3c]
- The order of the pairs matters: each pair's result is written back to the cars at once, so in a three-car contact the later pairs start from the earlier pairs' results. [hypothesis: fn_006378, code_00635E]
- Collisions do not run during the race-start countdown: two cars placed on top of each other at frame 10 of `challenge_r1` did not react (one scratch run). [hypothesis: code_0045CE, ram_start_countdown]
- A computer car loses control briefly after a contact: its timer (ram_coast_p2 for slot 1, + 2 per slot) is set to ram_coast_time (8 frames; 16 when ram_FFD754 is set at the race setup), and while it counts down the computer driver's controls are cleared, so the car coasts. Measured: the timer of the car that was hit became 8. [confirmed: P068, ram_coast_p2, ram_coast_time]
- The coasting effect of that timer (no steering or throttle for the computer car) is read from the computer-driver routine only. [hypothesis: code_042012, code_01CE34, ram_FFD754]
- After a contact each car's new direction is also copied to a per-car word (ram_drive_dir, + 2 per slot), but only the pair (0,1) copies both cars' own directions: the pairs (0,2) and (0,3) copy slot 1's direction into the other car's word, and the pairs (1,2), (1,3) and (2,3) copy the first car's direction into both words (a quirk). [hypothesis: code_00635E, ram_drive_dir, ram_FFD11E, ram_FFD120, ram_FFD122]
- The coasting timer is set only for the cars of slots 1-3: a pair with slot 0 sets the other car's timer, a pair of two other slots sets both (ram_coast_p2 to ram_coast_p4 from ram_coast_time), whether or not the contact sound plays. [hypothesis: code_00635E, ram_coast_p2, ram_coast_p3, ram_coast_p4]
- The contact sound is gated by the in-view flag of the pair's first car: slot 0's for the three pairs with slot 0, slot 1's (ram_FFD1E4) for (1,2) and (1,3), slot 2's (ram_FFD1E6) for (2,3). [hypothesis: code_00635E, fn_0068a4, ram_in_view_p1, ram_FFD1E4, ram_FFD1E6]
- Sound: on contact a cue is picked at random from one of two 16-entry lists (data_03BC2C or data_03BC3C, chosen by ram_FFEC0A) and requested only when the first car of the pair is in view (its in-view flag, ram_in_view_p1 for slot 0), the same flag the out-of-view point rule reads. [hypothesis: code_0068D2, data_03BC2C, data_03BC3C, ram_FFEC0A, ram_in_view_p1]
- Out-of-view and put-back: a car being put back after a fall, a sink or a head-to-head point has a state word of 32 or more and is ignored by the pair test, so cars put back side by side do not collide during the reappearing sequence: a car placed 19 px above another (a contact, P062) but in state 33 was not tested at all for 40 frames. [confirmed: P073, P071, slot.facing_state]
- An eight-car version exists: the pair routines slotpair_test (seven entries, 28 pairs from fn_0153b6) apply the same 48 px window and the same response routine, without the height test, and request the sound whether or not the car is in view; they are called from a second race loop that no recorded scenario reached. [hypothesis: slotpair_test, fn_0153b6, code_013BD6, code_004D34]

Open questions of this section and what would settle each:

- Three cars touching in one frame (later pairs start from the earlier pairs' results): settle with a four-player probe placing three cars in contact, with a write tap on the pair record for each pair. [hypothesis: fn_006378, code_00635E]
- No collisions during the start countdown (one scratch run only): settle with the overlapping placement repeated as a controlled probe at frame 10 and after the start. [hypothesis: code_0045CE, ram_start_countdown]
- The computer car coasting after a hit, and what sets the 16-frame setup word: settle with a `challenge_r1` contact logging the computer car's control word over the timer, and a writer run of ram_FFD754 from power-on. [hypothesis: code_042012, code_01CE34, ram_FFD754]
- The direction copies to ram_drive_dir and their quirk, and who reads those words: settle with a read watchpoint on ram_drive_dir to ram_FFD122 over a four-player race with contacts. [hypothesis: code_00635E, ram_drive_dir]
- The contact sound (the in-view gate, the two cue lists chosen by ram_FFEC0A): settle with a four-player contact writer run at the P071 placements logging the sound request, each car once in and once out of view. [hypothesis: code_0068D2, data_03BC2C, data_03BC3C, ram_FFEC0A]
- The eight-car pair test: settle with an eight-car race state, which no recorded scenario reaches. [hypothesis: slotpair_test, code_013BD6, code_004D34]

Located: fn_006378 and pair_test_s0, pair_test_sj in code_00635E (pair order, quick test, write-back), fn_0068d2 in
code_0068D2 (precise test, response, sound), fn_040d14 and fn_040b3c in code_040A18 (direction and speed to a vector
and back), code_042012 (computer-car coasting), code_013BD6 and code_004D34 (eight-car version, not reached); RAM
ram_pairrec, ram_hit_corner (touching corner), ram_corner_pos (corner positions), ram_coast_p2 to ram_coast_time, ram_drive_dir,
ram_FFD750, ram_FFD022, ram_car_height; probes P062-P068, P071, P073.

### Collision areas (what a modern reader would call the hitbox)

Answer: each car's collision area is a rectangle of about 14 x 20 px, long along the car, drawn inside the 32 x 32 px
frame whose top-left corner is the car's position (`slot.x`, `slot.y`), with its centre about 16 px across and
17 px down. It turns with the car's heading (32 headings of 11.25 degrees; a heading and its opposite share one area,
so there are 16 distinct areas). It follows the heading, not the direction the car is sliding in, and it is the same for every vehicle tested.
Contact means a corner of one rectangle lies strictly inside the other, tested on a 2 px grid; because only corners
count, two cars exactly level side by side never touch, and two cars crossing at right angles with their middles
together do not touch either.

In plain words, for a reader who wants to rebuild it: each car is a rectangle about 14 px wide and 20 px long,
centred in its 32 x 32 px sprite square and turned to the way the car faces, in 32 steps of 11.25 degrees (a car and
the same car turned half round use the same rectangle). Two cars touch when a corner of one rectangle lies strictly
inside the other; only the corners are tested, on a 2 px grid, so two cars exactly level side by side, or crossing at
right angles with their middles together, do not touch. The rectangle turns with the way the car faces, not with the
way it is sliding; it has no height (the pair test's 6 px height window stands in for one); and it was the same for
every car measured. The table below gives, for five pairs of facings, how far apart the cars can be and still touch.

Contact distances (the other car's position minus this one's, px; measured in the sweep P071 and the probes; every
tested placement agreed with the corner rule, which gives the full ranges below):

| Headings (this car, other car) | Along x, same y | Along x, y 1 px apart | Along y, same x | Along y, x 1 px apart |
|---|---|---|---|---|
| both facing up (or down) | never | -13 to 13 | -19 to 19, not 0 | -19 to 19, not 0 |
| both facing right (or left) | -19 to 19, not 0 | -19 to 19, not 0 | never | -14 to 14 |
| up and right (crossing) | -16 to 17, not -2 to 3 | -16 to 17, not -2 to 3 | -16 to 17, not -2 to 3 | -16 to 17, not -2 to 3 |
| both at 45 degrees (up-right) | -19 to 19 | -21 to 19 | -21 to 21 | -21 to 18 |
| crossing diagonals (up-right and down-right) | -23 to 23, not -3 to 5 | -23 to 23, not -3 to 3 | -23 to 23, not -5 to 3 | -23 to 23, not -5 to 3 |

- Shape: a rectangle about 14 px wide and 20 px long around the car's centre, turned with the heading: two cars facing up touch along their length up to 19 px apart and side by side up to 13 px apart; facing right the figures swap (19 along x, 14 along y). [confirmed: P062, P063, P064, P065, P071]
- Only the four corners of each rectangle are tested, against the other rectangle with strict edges on a 2 px grid: so cars exactly level side by side (same y facing up, same x facing right) never touch, and crossing cars with their middles within about 3 px do not touch. [confirmed: P066, P071, code_0068D2, data_036CC4, data_036EC4]
- The area follows the car's heading word (16 orientations; the slot's state word `slot.facing_state` carries it, 0-31 for 32 headings, and the heading and the heading 16 steps on give the same area), not its direction of motion: all response trials moved cars sideways or backwards relative to their heading with the area unchanged. [confirmed: t8r_resp_20261013T215159, t8r_resp_20261013T215353, t8r_resp_20261013T215436, P071, slot.facing_state, data_036CC4]
- For crossing diagonal cars the 48 px window of the quick test, not the rectangles, sets the limit: contact up to 23 px one way and 24 px the other. [confirmed: t8a_1d_20261013T214726, t8a_2d_20261013T214736, t8a_m1d_20261013T214928, t8c_cond_20261013T215126, P071]
- Vehicle: the area tables have no vehicle entry; the four-player race cars (multi_r1) and the challenge race 1 cars with a computer car (challenge_r1) gave the same contacts (10,062 and 445 placements). Whether the half-scale Mini Micro course uses the same areas in its stage pixels is not measured. [hypothesis: P071, data_036CC4, data_036EC4]
- Height: the area has no thickness; the quick test's height window (-6 to 5 px) stands in for it (section Car-to-car collisions). [confirmed: P067, P071, ram_car_height]

Open questions of this section and what would settle each:

- The half-scale Mini Micro and pool-table courses: whether the same areas apply in their stage pixels: settle with the P071 placement sweep on one such course. [hypothesis: P071, data_036CC4, data_036EC4]
- Other vehicle types (only the cars of `multi_r1` and `challenge_r1` were swept; the tables have no vehicle entry): settle with the sweep on a course raced with another vehicle type. [hypothesis: P071, data_036CC4, data_036EC4]
- The area record format (a row count, an axis flag, a byte offset and rows of two bounds) could describe shapes other than a rectangle; every tested placement fitted the rectangle: settle by decoding all 16 records with a scratch script and comparing them with the rectangle. [hypothesis: data_036EC4, fn_0068d2]

Located: data_036CC4 (corners per heading), data_036EC4 (area per heading), fn_0068d2 in code_0068D2 (corner test),
pair_test_s0, pair_test_sj (window); RAM ram_corner_pos (corner positions of the tested pair), ram_FFD3A6 (area rows of the
tested pair); probes P062-P067, P071.

### Bounce and impulse response

Answer: cars bounce off each other by swapping velocities (equal weight, almost no energy lost) plus a small fixed
shove apart; they bounce off walls by mirroring their direction of motion in the wall, losing a quarter of their speed
on straight walls. Neither changes the way the car is facing: the car slides off in the new direction while still facing
the old way, and its grip then turns the motion back toward the heading (section Drift and traction). The two use
different routines; they share only the conversion between direction-and-speed and a velocity vector.

In plain words, for a reader who wants to rebuild it: a bump never turns the car. It keeps facing the same way and
is sent sliding in a new direction, and its grip then turns the slide back toward the way it faces. Against another
car the two trade velocities, as two equal balls on a billiard table do, plus the small push apart, so a car that
runs into a standing one hands over its speed and is itself pushed back slowly (at 200 into a standing car: 45
backwards and 245 forwards). Overlapping cars are never moved apart directly; only the push separates them, again
on every frame they still overlap. Against a wall the car moves 1 px at a time; a step into a wall square puts it
3 px back, its direction is mirrored in the wall line, a straight wall takes a quarter of its speed (a diagonal one
takes nothing, read from the code only) and it leaves at no less than 60 units (about 1 px per frame), so a car
held against a wall bounces off it again and again. Speeds are in 1/64 px per frame.

Car against car, first contact (values exactly as the response routine read and wrote them; this car first, other car
second; directions 0 up, 256 right, 512 down, 768 left; "10 frames later" with no input, where the run was clean):

| Contact | Before: this car, other car | Corner | After: this car, other car | 10 frames later |
|---|---|---|---|---|
| head-on along x, 18 px apart | right 100, left 100 | 2 | left 145, right 145 | speeds 112, 115, rolling apart |
| head-on along x | right 200, left 200 | 2 | left 242, right 242 | 209, 212 |
| head-on along x | right 400, left 400 | 2 | left 436, right 436 | - |
| head-on along x | right 600, left 600 | 2 | left 630, right 630 | - |
| head-on along y, other car above | up 100, down 100 | 1 | 458 at 154, 970 at 154 | - |
| head-on along y | up 200, down 200 | 1 | 478 at 247, 990 at 247 | 203, 207 |
| head-on along y | up 397, down 397 | 1 | 492 at 436, 1004 at 436 | 382, 385 |
| head-on along y | up 600, down 600 | 1 | 498 at 632, 1010 at 632 | - |
| rear-end along x, other car ahead | right 400, right 200 | 2 | 254 at 1024 (speed cap), right 445 | 342, 394 |
| rear-end along x | right 600, right 200 | 2 | 254 at 1024 (speed cap), right 642 | - |
| rear-end along x into a standing car | right 200, standing | 2 | left 45, right 245 | 12, 215 |
| rear-end along y | up 400, up 100 | 1 | 118 at 74, 1005 at 447 | - |
| rear-end along y | up 600, up 200 | 1 | 50 at 165, 1010 at 645 | 121, 385 |
| glancing: this car facing and moving right, other facing and moving up, 14 px right and 8 px above | right 200, up 200 | 2 | 985 at 202, 252 at 245 | - |
| glancing, as above | right 400, up 400 | 2 | 1005 at 396, 252 at 442 | - |
| glancing: both facing right, opposite ways, offset 16 px and 10 px | right 400, left 400 | 3 | 789 at 391, 277 at 391 | 353, 353 |
| glancing, as above | right 200, left 200 | 3 | 809 at 200, 297 at 200 | - |
| side: moving right into a standing car facing up, 14 px right | right 100, standing | 2 | left 47, right 147 | - |
| side, as above | right 400, standing | 2 | left 42, right 442 | - |

Car against wall (player car, no input, decelerating 3 per frame before the wall; P072 and P069, P070):

| Approach (direction of motion) | Wall | Speed at the wall | Direction after | Speed after |
|---|---|---|---|---|
| straight up (0) | horizontal (wall direction 256) | 149 | 512 (straight back down) | 112 |
| straight up | horizontal | 376 | 512 | 282 |
| straight up | horizontal | 395 | 512 | 297 |
| 64 (22.5 degrees right of up) | horizontal | 369 | 448 | 277 |
| 129 (45 degrees) | horizontal | 359 | 383 | 270 |
| 131 | horizontal | 96 | 381 | 72 |
| 128 | horizontal | 77 | 384 | 60 (the floor) |
| 985 (left of up) | horizontal | 344 | 551 | 258 |
| 896 (45 degrees left of up) | horizontal | 358 | 640 | 269 |
| 701 (down-left) | vertical (wall direction 0) | 192 | 323 | 144 |

- Car against car, the rule: with each car's velocity as a vector, this car leaves with 63/64 of the other car's velocity plus 1/64 of its own, the other car with 63/64 of this car's plus 1/64 of its own, and each gets a shove of 48.8 speed units (0.76 px per frame) away from the other along the touching corner's direction (corners 2 and 8: along x; 3 and 5: along y; 4 and 6: along x the other way; 1 and 7: diagonally); a resulting speed below 30 is set to 30. Equal weights, no random element; the pair's combined velocity is kept (the two shoves cancel). [confirmed: P068, P062, P071, fn_0068d2]
- The car's heading and grip words are not changed by a car contact or a wall hit, only its direction of motion and speed (no heading or grip word diverged in P068 and P069); a car hit from the side slides away sideways and then turns back to its heading. [confirmed: P068, P069, P071, slot.movedir, slot.speed]
- Quirk: the new direction and speed are rounded through the movement routine's direction smoothing, which can move the direction by 2 steps; for motion exactly along an axis this makes the speed come out of a near-zero division, and both measured rear-ends along x threw the faster car to the speed cap of 1024 (16 px per frame) for that frame (it drove on at about 340 ten frames later). Of 23,498 contacts 8 differed from the plain rule: these 2 kinds plus 7 contacts in which the computer car's direction word was outside 0-1023 (it reads as a different quarter turn). [confirmed: t8r_resp_20261013T215159, t8r_resp_20261013T215353, t8r_resp_20261013T215436, P071, fn_040b3c, code_040A18]
- The car response runs the vector-to-direction conversion on the working slot without loading either contact car into it, so its direction smoothing (a new direction equal to or 1 step from the working slot's old one is moved 2 steps toward the reference word ram_drive_dir_s8, skipped while ram_FFD150 is nonzero) compares with the values left there by the car moved last; the response also leaves the working slot's speed cap ram_top_speed_s8 at 1024. [hypothesis: fn_0068d2, fn_040b3c, code_0068D2, code_040A18, ram_drive_dir_s8, ram_FFD150, ram_top_speed_s8]
- Push-apart: there is no position correction for overlapping cars; only the shove separates them, so cars that keep overlapping are shoved again each frame (the rear-end along x at 400 into 200 touched on 4 frames in a row). [confirmed: P071, P062]
- Car against wall, the rule: while a car moves (in 1 px steps, the wall tested at every second pixel at three or four corners of its outline) a step into a wall cell steps it back 3 px, its direction of motion becomes twice the wall's direction minus its own (a mirror in the wall line), on a horizontal or vertical wall it loses a quarter of its speed, and its speed is then raised to at least 60; the rest of that frame's movement is dropped. [confirmed: P069, P070, P072, code_03F834, ram_FFD696, ram_FFD744]
- On diagonal wall cells (wall direction other than 0 or 256 of 1024) the speed is not reduced, only mirrored. [hypothesis: code_03F834, data_0359DE]
- The wall floor speed is 60 for each car (ram_FFD744 to ram_FFD74A, set at the race setup), so a car that touches a wall slowly is pushed off it at 60 (about 1 px per frame); with accelerate held into a wall the car keeps hitting it and stays pinned (P056). [confirmed: P072, P056, code_01CE34, ram_FFD744, ram_FFD746]
- A wall hit requests sound cue 6C when the car is in view (the moving car's in-view flag). [hypothesis: code_040A04, fn_040a04, ram_FFD1F2]
- Wall versus car: different routines and different moments: walls inside the car's own movement, pixel by pixel, for each car in turn; cars once per frame after all cars have moved; the car rule keeps speed and adds a shove, the wall rule mirrors and takes a quarter. [confirmed: P069, P068, code_03F834, code_0068D2]
- In the air the wall test is skipped while the height is 14 px or more or the car still rises fast (section Ramps and airborne), and two cars whose heights differ by 6 px or more pass each other. [hypothesis: code_03F834, P067]

Open questions of this section and what would settle each:

- Diagonal walls mirror without taking speed: settle with the P072 wall sweep on a diagonal wall square. [hypothesis: code_03F834, data_0359DE]
- The wall cue 6C and its in-view gate: settle with a sound-request tap during a P072 run, once in view and once out of it. [hypothesis: code_040A04, fn_040a04, ram_FFD1F2]
- The car response uses the working slot's leftovers (direction smoothing against the car moved last, speed cap left at 1024): settle with a contact writer run at the P068 setup logging the working slot, repeated with a different car moved last. [hypothesis: fn_0068d2, fn_040b3c, ram_drive_dir_s8, ram_top_speed_s8]
- The outline test fn_040a18 (four points of a per-state table against the course grid) has no located caller; it may be a wall test: settle by locating its callers and with a wall-contact writer run. [hypothesis: fn_040a18, code_040A18]
- The angle search fn_040d5a covers 256 words while its table region data_038704 is 63 words long: settle by checking the region bounds against the searched range (the region pass) and a contact writer run logging the search. [hypothesis: fn_040d5a, data_038704]
- Walls cleared in the air: settle with a ramp jump toward a wall (section Ramps and airborne). [hypothesis: code_03F834, P067]

Located: fn_0068d2 in code_0068D2 (car response), fn_040d14 and fn_040b3c in code_040A18 (vector conversion),
code_03F834 (movement steps, wall test and wall response), fn_040a04 in code_040A04 (wall cue), code_01CE34 (wall
floor set); RAM ram_FFD696 (wall direction of the last hit), ram_FFD73E (wall hit this frame), ram_FFD744 to
ram_FFD74A (wall floor speed per car), ram_top_speed_s8 (speed cap used by the conversion); probes P056, P062, P068, P069,
P070, P071, P072.

## Group 5: Vehicle handling

All units in this group: speed in 1/64 px per frame (64 = 1 px per frame, 50 frames per second), directions of motion
in 1024 steps per turn (0 up, 256 right), headings in 32 steps (11.25 degrees each; heading h faces direction 32 h).
"Frame" is one game frame; the per-frame recorder sometimes sees two game frames' movement at once and none in the
next, so the tables count game frames. Each car carries five handling words, copied into its slot at the race setup
from the course's record: acceleration `A` (ram_accel for the player, + 2 per slot), drag `D` (ram_drag), grip `G`
(ram_grip), top speed (ram_top_speed) and steering period (ram_steer_period). The movement routine works on a copy of the car
in slot 8 (ram_accel_s8, ram_drag_s8, ram_grip_s8, ram_top_speed_s8, ram_steer_period_s8 hold the copied words).

One frame of movement, as read from the movement routine and checked against the recordings (next-frame direction
within 2 steps and speed within 2 units in 117 of 130 single-frame predictions on four vehicles, the rest within 13
steps at catch-up frames; P079, P085, P087, P090):

1. Steering, every `steering period` frames while left or right is held: the heading moves one step, costing `A`/2 speed.
2. The drive direction (a per-car word chasing 32 x heading) turns toward the heading by `10 + (256 - min(speed, 512)/2)/8` direction steps per frame (42 at rest, 16 at speed 416, 10 from 512 up), two or three times that when more than 128 or 256 steps away, and snaps to it from 384 steps.
3. The motion is rebuilt as a vector: `speed - speed/128 - G` along the old direction of motion plus `G - D + speed/128` (at most the speed after drag) along the drive direction; the total is the speed minus `D`, and `G + speed/128` of it turns toward the heading each frame.
4. Accelerate adds `A` along the heading; brake adds `A - A/4` against the heading while the car still moves forwards or its backward speed is at most half the top speed.
5. The vector becomes the new direction of motion and speed, the speed capped at the top speed.

Recipe for one frame in exact integer arithmetic, for a reimplementation. Read from the movement routine and its helpers
only (not yet checked frame by frame against a recording beyond the five steps above); `/` is integer division
rounding down, `>>` a shift, directions wrap at 1024 and headings at 32:

- Order inside one call of car_move: (0) while ram_FFECB0 is set, the control is cleared and replaced by brake when the car moves forwards; (1) slope push and slope turn; (2) the heading is saved (ram_FFD384) and a running low-grip timer counts down, writing acceleration 6, drag 1, grip 2 into the working copy; (3) the drive-direction chase; (4) a side call (fn_04191e); (5) steering; (6) vector build, conversion back (fn_040b3c) and the position step. [hypothesis: car_move, ram_FFECB0, ram_FFD384, ram_low_grip_timer, fn_04191e]
- Steering counter: ram_steer_count_s8 counts up every frame, held buttons or not; a heading step happens only on the frame the count reaches the period exactly, and the count then restarts at 0. On the other frames a held direction only leans the displayed heading (slot.facing_state) one step; a lean or step into a wall is undone (fn_040a18). A step costs `A >> 1` speed, floored at 0; a car at exactly speed 0 after a lean or step with a direction held is set to `4A`. [hypothesis: car_move, ram_steer_count_s8, ram_steer_period_s8, fn_040a18]
- Drive-direction chase: rate `r = 10 + ((256 - (min(speed, 512) >> 1)) >> 3)`; the target is 32 x heading, plus 512 when the motion points more than 352 and less than 672 steps away from it (driving backwards, flag ram_FFD68A). With `d` the distance from the target (0-1023): up to 128 moves `r`, 129-256 moves `2r`, 257-383 moves `3r`, from 384 to 640 snaps to the target, and the mirror ranges on the other side; a move that overshoots snaps. [hypothesis: car_move, ram_drive_dir_s8, ram_FFD68A]
- Grip blend: with `q = speed >> 7` (kept in ram_FFCFB0), the old direction of motion gets `max(0, speed - (q + G))`; the speed then loses `D` (floored at 0); the drive direction gets `G - D + q`, compared unsigned with the speed after drag and clamped to it, so a negative share becomes the whole speed. In the air (ram_FFD150 nonzero) the whole speed stays on the old direction and drag, grip, throttle and brake are skipped. [hypothesis: car_move, ram_grip_s8, ram_drag_s8, ram_FFCFB0, ram_FFD150]
- Throttle and brake: brake (control bit 40) is tested first and, when held, throttle is ignored that frame. Brake pushes `A - (A >> 2)` toward 32 x facing + 512 when half the top speed is at least the speed, or else when the motion lies within 255 steps of the facing (forward); motion 256-769 steps away from the facing gets no push. Throttle (bit 10) pushes `A` toward 32 x facing, the leaned facing, not the stepped heading. [hypothesis: car_move, ram_control_car, ram_accel_s8, ram_top_speed_s8]
- Direction vectors (fn_040d14): one quarter turn of 256 sine-cosine word pairs, the quarter chosen by the top two bits of the direction and the pair rotated and negated for it; each word is multiplied by the speed (16 x 16 into 32 bits) with no rounding, giving two long components. [hypothesis: fn_040d14, car_move]
- Back to direction and speed (fn_040b3c): both components zero gives speed 0 and motion 32 x facing. Otherwise the ratio of the smaller to the larger absolute component is looked up by binary search in an ascending 256-entry table (fn_040d5a) to an angle within the octant, the quarter coming from the signs; the speed is the larger component divided by the table word for that angle (no square root); a new direction within one step of the old motion and not on the drive direction moves 2 further toward the drive direction; the speed is capped at the top speed. [hypothesis: fn_040b3c, fn_040d5a, ram_top_speed_s8]
- Position: speed >> 6 whole pixels per frame, plus one when the rotating 8-frame bit (ram_FFC21A, one bit rotated each unpaused frame, reset at race setup) is set in the row of an 8-bit pattern chosen by speed & 63; each pixel is a separate step along the motion direction (x and y share it by a per-direction pair table), tested against walls, with x and y wrapped to the course size; skipped while ram_FFD6BC is set. [hypothesis: car_move, dat_038904, ram_FFC21A, ram_FFD6BC]

### Acceleration

Answer: the throttle (button B) adds `A` per frame along the heading and drag takes `D`, so on a straight a car gains
`A - D` per frame from its first frame (which gives exactly `A`) until it reaches its top speed: no gears and no
speed-dependent curve. At the race start the number of frames accelerate was held during the countdown decides the
launch: under 50 frames the car starts rolling at that many speed units; 50 or more is a wheelspin start, where for
(held frames - 50) frames the car runs on fixed low values (acceleration 6, drag 1, grip 2), gaining 5 per frame.

Accelerate from rest on an open straight (speed by frames since the throttle was pressed; idle through the start first):

| Frame | Internal course 2 (A 12, D 3, top 416) | Course 1 (A 10, D 3, top 384) | Course 5 (A 8, D 3, top 448) | Course 13 (A 6, D 1, top 364) |
|---|---|---|---|---|
| 1 | 12 | 10 | 8 | 6 |
| 2 | 21 | 17 | 13 | 11 |
| 5 | 48 | 38 | 28 | 26 |
| 10 | 93 | 73 | 53 | 51 |
| 20 | 183 | 143 | 103 | 101 |
| 30 | 273 | 213 | 153 | 151 |
| 40 | 363 | 283 | 203 | 201 |
| 46 | 416 (top, 6.5 px per frame) | 325 | 233 | 231 |
| 55 | 416 | 384 (top, 6 px per frame) | 278 | 276 |
| 73 | 416 | 384 | 368 | 364 (top, 5.7 px per frame) |
| 83 | 416 | 384 | 418, then left the course before its top | 364 |

Race start on internal course 2 with accelerate held through the 90-frame countdown (a wheelspin start of 40 frames):
speed 6 at the first frame, + 5 per frame to 201 at frame 40, then + 9 per frame to the top speed 416 at frame 64.
Held from 30 frames before the start (a rolling start) the car starts at 29 and gains 9 per frame from there.

- The throttle adds the acceleration word `A` along the heading every frame and drag `D` is taken every frame, so a car gains `A - D` per frame in a straight line from rest: 9 on internal course 2 (A 12, D 3), 7 on course 1 (10, 3), 5 on course 5 (8, 3) and 5 on course 13 (6, 1), the first frame giving exactly `A`. [confirmed: P075, P082, P084, P086, code_03F834, ram_accel, ram_drag, slot.speed]
- Pad button B is accelerate: it sets bit 10 of the car's control byte (ram_control_p1 for player 1), which the movement routine reads one frame after the press. [confirmed: P075, P005, ram_control_p1, ram_control_car]
- Launch: the frames accelerate is held during the countdown are counted per car (ram_launch_hold for player 1, + 2 per car); at the start a count under 50 becomes the starting speed (held 30 frames: started at 29), 50 or more starts a timer of count - 50 frames (ram_low_grip_timer) during which the car uses acceleration 6, drag 1 and grip 2 (held 90 frames: 40 frames of + 5 per frame). [confirmed: P074, P078, code_0045CE, ram_launch_hold, ram_low_grip_timer, ram_low_grip_s8]
- A car at rest that steers is kicked to `4A` (48 for A 12) at its first heading step and then slows by drag and the steering cost, so steering on the spot makes it creep forward in bursts (every third frame back to 41-45). [confirmed: P081, P080, code_03F834]
- The `4A` kick also follows a lean frame with no heading step: Right held for one frame from rest (A 12) gave speed 45 that frame (48 less drag 3) with the heading unchanged; holding two lean frames gives no second kick (42 on the second); the kick is once per lean onset. [confirmed: P145, P146, car_move]
- The control byte reads 0 during the countdown even while B is held; only the count moves. [confirmed: P074, P078, ram_control_p1]
- Computer cars get no launch: their launch counts (ram_launch_hold + 2 per car) stay 0 through the countdown, and slots 1-3 start at their own `A` (10, 9, 11 on the time-trial challenge) on the first race frame, then gain +4, +3, +5 per frame; slot 3 starts one frame later. [confirmed: P147, ram_launch_hold, slot.speed]

In plain words, for a reader who wants to rebuild it: holding accelerate adds a fixed amount of speed every frame and
drag takes a smaller fixed amount, so the speed climbs in a straight line until it hits the top speed, with no gears
and no slowing of the gain near the top. On the nimble course-2 set the car gains 9 units a frame and reaches its top
of 6.5 px per frame in 46 frames, just under one second at 50 frames per second; the sluggish course-13 set gains 5 a
frame and needs 73 frames (1.5 s) to reach 5.7 px per frame. At the start, holding accelerate briefly during the
countdown gives a rolling start (held 30 frames: the car starts at 29 units, about half a pixel per frame); holding it
for one second or more spins the wheels, and the car crawls on low values for as long as it was held past that second.

Open questions of this section and what would settle each:

- The launch count's exact step (two up per held frame and one down per frame, net one) and the rounding at count 50: settle with a writer run on ram_launch_hold through a countdown held for exactly 49, 50 and 51 frames. [hypothesis: code_0045CE, ram_launch_hold]
- What a poked computer launch count does: in one run, ram_launch_hold of slot 1 poked to 60 counted down to 27 by the start, then froze, and slot 1 started at 31 (its A 10 + 21); settle with two more poke values. [hypothesis: P147, ram_launch_hold]

Located: code_03F834 (movement: throttle, drag, low-value timer), code_0045CE (launch from the countdown count),
code_040F2A (copy of each car into slot 8 and back), code_01CE34 (handling words from the course record); RAM
ram_accel, ram_drag, ram_launch_hold, ram_low_grip_timer, ram_low_grip_s8, ram_control_p1; probes P074, P075, P078, P082, P084, P086.

### Top speed

Answer: each car's top speed is one word from the course record, a hard cap on the speed after every frame's movement;
it is reached at the steady `A - D` rate and then held exactly. Measured: 416 (6.5 px per frame) on internal course 2,
384 (6 px per frame) on course 1, 364 (5.7 px per frame) on course 13. Across the 42 surveyed courses the word ranges
256-768 (4 to 12 px per frame). Computer cars use the same cap from their own per-race block (section Difficulty).

- The speed is capped at the car's top-speed word when the motion vector is turned back into a speed each frame: the player car levelled at exactly 416 on internal course 2, 384 on course 1 and 364 on course 13, the values of ram_top_speed there. [confirmed: P075, P084, P086, ram_top_speed, ram_top_speed_s8, fn_040b3c]
- Sloped surface cells (a per-cell push direction, ram_FFD216) raise the cap by up to 128 for that frame and add a push to the motion. [hypothesis: code_03F834, ram_FFD216, ram_FFD6BE]
- On a sloped cell (cell code 0, 8, 16 or 24, read as a heading) a moving car that is not steering has its heading turned one step toward the slope's heading every 4, 8, 16 or 32 frames, more often the nearer it already points (every 4 frames within 3 steps, every 32 at 12-20 steps). [hypothesis: code_03F834, ram_FFD216, ram_FFC21C]
- The position moves speed/64 whole pixels per frame plus one more on frames picked by a per-speed bit pattern (speed mod 64) against a rotating frame bit, so fractional speeds average out over frames. [hypothesis: code_03F834, dat_038904, ram_FFC21A]
- Slow cells (code 45) clamp the speed to 64 (1 px per frame) every frame a car is on one. [hypothesis: code_01EA82, code_01ED8C]
- A car contact can throw a car to 1024 for one frame (section Bounce and impulse response); the cap applies again from the next frame. [hypothesis: code_0068D2, ram_top_speed_s8]

In plain words: the top speed is a hard ceiling, one number per course, applied after every frame's movement; nothing
lets a car exceed it on flat ground, and a car at the ceiling stays exactly there while the throttle is held. Measured
ceilings are 6.5 px per frame (325 px per second) on internal course 2, 6 px per frame on course 1 and 5.7 on course
13; the surveyed courses range from 4 to 12 px per frame. Fractions of a pixel are not stored: a per-speed pattern
decides on which of every 8 frames the car moves one extra pixel, so the average comes out right. Slopes are the one
exception, raising the ceiling by up to 2 px per frame for that frame.

Open questions of this section and what would settle each:

- The slope allowance (up to 128 above the top, built 16 per frame nearer the slope's heading): settle with a probe driving down a sloped cell on a course that has one, recording slot.speed against ram_top_speed. [hypothesis: car_move, ram_FFD216]
- The sub-pixel pattern: settle with a 64-frame recording of x and y at a fixed speed of 32 and 96 (expect 4 and 12 px per 8 frames from the pattern). [hypothesis: dat_038904, ram_FFC21A]
- Slow cells clamping to 64: settle with a recording of slot.speed while a car crosses a code-45 cell. [hypothesis: code_01EA82]

Located: code_03F834, fn_040b3c in code_040A18 (cap), code_01CE34 (setup); RAM ram_top_speed, ram_top_speed_s8; probes P075,
P084, P086.

### Braking

Answer: releasing the throttle leaves only drag: the car loses `D` per frame (3 on internal course 2: 416 to 314 in 34
frames). Button A brakes: it pushes against the heading with three quarters of the acceleration, so with drag the car
slows by `3A/4 + D` per frame (12 on internal course 2: from 416 to a stop in 35 frames and 110 px). Held on, the same
push drives the car backwards: reverse builds at `3A/4 - D` per frame (6) and levels at about half the top speed
(211-217 for top 416, 3.3 px per frame), because the push stops while the backward speed is above half the top.

| Frames after release or brake (internal course 2) | Coasting (no input) | Braking (A held) |
|---|---|---|
| 0 | 416 | 416 |
| 2 | 410 | 401 |
| 10 | 386 | 305 |
| 20 | 356 | 185 |
| 34 | 314 | 17 |
| 36 | 308 | 7, now moving backwards |
| 70 | - | 211, reverse levelled (211-217) |

- Release: with no input the speed falls by the drag word `D` per frame (3 on internal course 2: 410 to 314 in 32 frames) and the direction is kept. [confirmed: P076, code_03F834, ram_drag]
- Brake: button A (control bit 40) adds three quarters of `A` against the heading, so the speed falls by `3A/4 + D` per frame (12 on internal course 2, 416 to 17 in 34 frames). [confirmed: P077, ram_control_car, code_03F834]
- Reverse exists: braking on through a stop turns the direction of motion round (direction 512 with heading 0); the speed rises by `3A/4 - D` per frame (6) and levels at 211-217, about half the top speed, because the backward push is applied only while the backward speed is at most half the top speed. [confirmed: P077, code_03F834, ram_top_speed_s8]
- While the flag ram_FFECB0 is set every car's control is replaced by the brake as long as it still moves forwards (a race-end stop). [hypothesis: code_03F834, ram_FFECB0]
- The brake push is `A - A/4` with the quarter rounded down (9 for A 12, 8 for A 10, where `3A/4` would give 7): on internal course 1 (A 10, D 3) braking took 11 per frame (370 to 7 in 33 frames), not 10; and brake held cancels accelerate that frame (course 22, both bits set: -11 = 9 + D 2). [confirmed: P141, P139, P140, car_move, ram_accel_s8, ram_control_car]

In plain words: letting go of the throttle costs only the drag, 3 units a frame on internal course 2, so a car at top
speed loses a quarter of its speed in about 34 frames (0.7 s) and takes nearly three seconds to stop. The brake (button A) pushes backwards with
three quarters of the acceleration on top of the drag: from 6.5 px per frame to a stop in 35 frames (0.7 s) and 110
px. Keep holding it and the car reverses, building backward speed at 6 units a frame to about half the top speed (3.3
px per frame), where the push stops. Pressing brake and accelerate together brakes.

Open questions of this section and what would settle each:

- The dead zone where brake does nothing (motion 256-769 steps from the facing while faster than half the top, for example sliding sideways): settle with a probe braking during a P079-style slide. [hypothesis: car_move]
- What sets ram_FFECB0 (race end or another state): settle with a writer run over the end of a race. [hypothesis: ram_FFECB0]

Located: code_03F834; RAM ram_control_car (control byte of the car being moved), ram_drag; probes P076, P077.

### Steering

Answer: left and right turn the car one heading step (11.25 degrees) every `steering period` frames at any speed: the
period is 3 on most courses (a full circle in 96 frames, 1.9 s), 4 on some (128 frames) and 2 on one (64 frames). Each
step costs `A`/2 speed. Steering turns the heading only; the direction of motion follows through the grip (section
Drift and traction), so at speed the car slides. Between steps the displayed heading word (`slot.facing_state`) may lean one
step into the turn.

| Probe | Speed when steering began | Heading steps in 48 frames of Right | Largest slide angle (heading minus motion) |
|---|---|---|---|
| internal course 2, period 3, grip 30 (P079) | 416 (top) | 16 | 118 steps (41 degrees) |
| internal course 2, throttle released (P080) | 111 | 16 | 42 steps; speed 0 after 20 frames |
| internal course 2, at rest (P081) | 0 | 16 | 12 steps; creeping at 9-45 |
| course 5, period 3, grip 8 (P083) | 253 | 16 | 293 steps (103 degrees) |
| course 1, period 4, grip 20 (P085) | 353 | 12 | 106 steps (37 degrees) |
| course 13, period 2, grip 2 (P087) | 251 | 24 | spun (495 steps); speed 251 to 37 |

- Heading rate: one step of 32 per `steering period` frames (ram_steer_period), whatever the speed: 16 steps in 48 frames at speeds 416, 111 and 0 on internal course 2 (period 3), 12 on course 1 (period 4), 24 on course 13 (period 2). [confirmed: P079, P080, P081, P085, P087, ram_steer_period, ram_steer_period_s8, ram_steer_count_s8]
- Right (control bit 08) turns clockwise (heading + 1), left (bit 04) anticlockwise; there are 32 headings (heading word at slot offset 24, FFD056 for the player). [confirmed: P079, P083, P085, ram_control_car, ram_slottab]
- Each heading step takes `A`/2 from the speed (6 for A 12): at top speed under throttle the car held 391-416 while turning; without throttle it stopped within 20 frames of steering. [confirmed: P079, P080, code_03F834]
- A heading step is refused when the car's collision area at the new heading would touch a wall (the step is undone that frame). [hypothesis: fn_040a18, code_03F834]
- With the word ram_FFEC6A set, an odd heading reached by a lean step snaps back to the even neighbour when the steering is released (16-direction steering, perhaps an option). [hypothesis: code_03F834, ram_FFEC6A]
- The period counter (ram_steer_count_s8) runs every frame, held buttons or not, and a heading step lands on the first held frame where the count reads 0; so the first step comes 0 to `period - 1` frames after the press (period 3: count 0 at the press, step that frame; count 2, next frame; count 1, two frames later), while the displayed heading leans on the press frame itself. [confirmed: P142, P143, P144, car_move, ram_steer_count_s8, ram_steer_period_s8]
- On internal course 42 (period 3, top 768) the heading stepped every 5 frames at 768 and the speed did not drop, against 3 frames on internal course 22 (top 640) and 4 on internal course 8 (period 4); the step interval is not always the period word. [hypothesis: P151, P150, P152, ram_steer_period]

In plain words: steering turns the car's nose a fixed 11.25 degrees every few frames (every 3 frames on most courses,
so a full circle in 1.9 seconds), the same at any speed, and each turn step costs half the acceleration in speed. The
nose turns, not the motion: the direction of travel follows through the grip, so at speed a turn opens a slide. On
the frames between steps the car's picture leans one step into the turn, which is only display. The steering never
slows with speed and has no analogue sensitivity: a direction is either held or not.

Open questions of this section and what would settle each:

- The 5-frame heading steps at speed 768 on internal course 42 (and its car state 33 from the sixth step): settle with a steering probe on course 42 started at speeds 384 and 768, reading ram_steer_count_s8 and slot.facing_state. [hypothesis: P151, ram_steer_count_s8]
- The wall test on a step (fn_040a18): settle with a probe steering against a wall. [hypothesis: fn_040a18]
- Who sets ram_FFEC6A (16-direction steering): settle with a writer run across the options menu. [hypothesis: ram_FFEC6A]

Located: code_03F834 (steering step and cost), fn_040a18 (turn test); RAM ram_steer_period (period), ram_steer_count_s8 (period
counter of the car being moved), ram_slottab (heading word); probes P079, P080, P081, P083, P085, P087.

### Drift and traction

Answer: a car's motion is turned toward its heading by a fixed share of its speed each frame, the grip word `G` plus
speed/128, while the rest keeps going the way it went. At speed the heading turns faster than that, so a turn opens a
slide angle between the way the car faces and the way it moves; when the steering stops the angle closes at a rate set
by the grip: with grip 30 at top speed a 93-step slide (33 degrees) is gone in 26 frames, with grip 8 a 125-step slide
halves in about 13 frames, and with grip 2 the motion barely turns and the car spins. The three words behind traction
are acceleration, drag and grip; the low-grip timer (wheelspin start, slippery cells) replaces them with 6, 1 and 2.

| Frames after the steering stopped | Slide, grip 30, speed 416 (P091) | Slide, grip 8, speed 282-384 (P092) |
|---|---|---|
| 0 | 93 | 125 |
| 4 | 66 | 100 |
| 8 | 43 | 84 |
| 12 | 31 | 66 |
| 16 | 23 | 56 |
| 20 | 12 | 47 |
| 26 | 0 | 27 |
| 34 | 0 | 13 |

- Grip: each frame `G + speed/128` units of the speed are moved from the old direction of motion to the drive direction (which follows the heading) and the rest keeps the old direction; with no surface effect this predicts the next frame's direction within 2 steps and the speed within 2 units in 117 of 130 frames on four vehicles. [confirmed: P079, P085, P087, P090, code_03F834, ram_grip, ram_grip_s8, ram_drive_dir_s8]
- The drive direction (ram_drive_dir for the player, + 2 per slot) turns toward the heading by 10 to 42 steps per frame, faster at low speed (16 per frame at speed 416, measured), so at low speed the motion follows the heading within 2-3 frames and at top speed it lags. [confirmed: P079, P080, ram_drive_dir, ram_FFCF9E]
- Slide decay after a turn: grip 30 at 416 closes a 93-step slide to 0 in 26 frames; grip 8 closes 125 steps to 13 in 34 frames; while steering, the slide reached 118 steps with grip 30, 106 with grip 20, 293 with grip 8 and over 400 (a spin) with grip 2. [confirmed: P091, P092, P079, P083, P085, P087]
- Low-grip timer (ram_low_grip_timer for player 1, + 2 per car): while it runs the car uses acceleration 6, drag 1 and grip 2; poked to 50 during the top-speed turn, the slide reached 326 steps instead of 118 and the speed fell from 416 to 225. [confirmed: P090, ram_low_grip_timer, ram_low_grip_s8]
- Slippery cells (code 3C) start that timer at 50 frames (5 on internal course 14). [hypothesis: code_01EA82, code_01ED8C, ram_low_grip_timer]
- A car contact or a wall hit changes only the direction of motion, so after a bounce the grip turns the motion back toward the heading (seen in every T8 trial). [hypothesis: P068, P069, code_03F834]
- While a car is in the air (height word nonzero) the movement keeps its direction of motion and speed: no drag, grip share, throttle or brake that frame, only the slope push. [hypothesis: code_03F834, ram_FFD150]
- Code 3D cells (listed as drift in the course section) do not change grip: they move the car by a per-course offset each frame, like a current or conveyor. [hypothesis: code_01EA82, ram_FFD6DA]
- Construction-kit courses set the five words from the kit's vehicle options (acceleration 5 plus one option, top speed 200 plus 1.5 times another, steering period 3), and one option value gives the low-grip drag 1 and grip 2. [hypothesis: code_001978, ram_FFEDD0, ram_FFEDD1, ram_FFEDD2, ram_FFEDCF]
- A slide toward the back (motion more than 352 steps from the heading) makes the drive direction chase the reverse of the heading, so a car driving backwards is not pulled round to face its motion. [hypothesis: car_move, ram_FFD68A]

In plain words: every frame the car moves a small, fixed share of its speed (the grip number plus speed/128) from the
way it is going to the way it is facing; the rest keeps going straight. With the course-2 grip of 30 at top speed that
is about 8 percent a frame, so a 33-degree slide is gone in half a second; with grip 8 a slide of 44 degrees halves in
a quarter of a second and takes about 0.7 s to almost close; with grip 2 the car barely follows its nose and spins
when steered. A second, faster helper (the drive direction) follows the nose first, quickly at low speed and lagging
at high speed, and the grip pulls the motion toward it. Drag and grip are the only friction; there is no tyre model,
no weight transfer and no speed-dependent grip besides the speed/128 term.

Open questions of this section and what would settle each:

- Slippery cells starting the low-grip timer at 50 frames: settle with a recording on internal course 14 while a car crosses a code-3C cell. [hypothesis: code_01EA82, ram_low_grip_timer]
- Air time skipping drag and grip: settle with a recording over a jump (height word ram_FFD150 nonzero) showing speed and direction held. [hypothesis: car_move, ram_FFD150]
- The 13 of 130 frames the five-step model missed (all at frames where the recorder caught two game frames at once): settle with a frame-exact recording (one sample per game frame). [hypothesis: P079, P085, P087, P090]
- Code-3D cells as a conveyor: settle with a recording at rest on such a cell. [hypothesis: code_01EA82, ram_FFD6DA]

Located: code_03F834 (grip blend, drive direction, low-grip timer), code_01EA82 and code_01ED8C (surface cells per
car), code_001978 (kit handling); RAM ram_grip, ram_grip_s8, ram_drive_dir, ram_drive_dir_s8, ram_FFCF9E, ram_low_grip_timer; probes
P079, P083, P085, P087, P090, P091, P092.

### Vehicle types

Answer: the game stores handling per course, not per vehicle: each course's record holds the five handling words and
the player car on that course gets them (computer cars then take their own five from the race's block). The 42
surveyed courses use 25 distinct sets: acceleration 6-12, drag 1-4, grip 2-30, top speed 256-768, steering period 2-4.
The same vehicle can handle differently on two courses: the pool-table car has top speed 512 on Pool Slalom (internal
19) and 448 on Ball Chase (internal 18). Which vehicle art a course uses is not yet located.

| Handling set (A, D, G, top, period) | Internal courses | Measured here |
|---|---|---|
| 12, 3, 30, 416, 3 | 2, 41, 43 | acceleration, top, braking, steering, slide (P074-P081, P091) |
| 10, 3, 20, 384, 4 | 1, 65 | acceleration, top, steering (P084, P085) |
| 8, 3, 8, 448, 3 | 5, 12 | acceleration, steering, slide (P082, P083, P092) |
| 6, 1, 2, 364, 2 | 13 | acceleration, top, steering (P086, P087) |
| 12, 2, 6, 640, 3 | 22, 24 | forced throttle, top, steering (P138-P140, P150) |
| 12, 2, 20, 768, 3 | 42 | acceleration, top, steering (P148, P151) |
| 7, 3, 20, 256, 4 | 8 | acceleration, top, steering (P149, P152) |

- Handling is a per-course record of five words (acceleration, drag, grip, top speed, steering period) chosen by the internal course number (ram_FFD672) and copied to all eight slots at the race setup; four handling sets were measured by input probes and behaved as their words predict. [confirmed: P075, P082, P084, P086, code_01CE34, data_04693E, ram_FFD672]
- Survey of 42 internal courses (frame 900 of each list course's race): 25 distinct sets; Pool Slalom (internal 19) 10, 3, 20, 512, 3 and Ball Chase (internal 18) 10, 3, 20, 448, 3, so the pool-table car's top speed depends on the course. [hypothesis: P057, data_04693E]
- Each time-trial course has one fixed vehicle; the course-select toggle changes only a label. [hypothesis: ram_FFEAFA, docs/ops/ops-tools.md]
- On internal courses 22, 24 and 25 the race loop forces accelerate on for every car each frame and clears brake while the car's speed is below 320 (5 px per frame), so those cars always drive and cannot stop or reverse below that speed; this explains the accelerate bit seen without input on course 22 (P088, P089, kept as rejected). Measured on internal course 22: with no input the accelerate bit is set from the start, a wheelspin start of 50 frames at + 5 then + 10 (A - D) to 640; brake held from rest has no effect until 320, then the car hovers at 309-329 (brake frames -11 at 320 or more, + 10 below); brake from 640 falls 11 per frame to 310 in 30 frames, then the same hover. [confirmed: P138, P139, P140, code_0045CE, ram_FFD672, ram_control_p1]
- The three sets not driven before behave as their words predict: internal 42 gains `A` then `A - D` (+10) to 768 and levels there; internal 8 gains 7 then +4 to 256 and levels; internal 22 levels at 640; steering on 22 and 8 steps every period frames (3 and 4). [confirmed: P148, P149, P138, P150, P152, data_04693E]

In plain words, for a reader who wants to rebuild it: there is no per-vehicle handling table. Each course carries five
numbers, and every car racing on it gets them: acceleration (speed gained per frame of throttle), drag (speed lost
every frame), grip (how much of the speed turns toward the way the car faces each frame), top speed and steering
period (frames per heading step). The measured sets run from a sluggish 6, 1, 2, 364, 2 (internal course 13: slow to
build speed, almost no grip, fast steering, so it spins easily) to a nimble 12, 3, 30, 416, 3 (internal course 2:
reaches 6.5 px per frame in under a second, slides only about 40 degrees at most). Computer cars get their own five
numbers per race (section Opponent AI), not the course's. Three courses (internal 22, 24, 25) hold the throttle down for
every car, so the player only steers there and cannot brake below 5 px per frame.

Open questions of this section and what would settle each:

- Which vehicle art each course uses: settle with a writer run of the sprite-set word at the race setup over the 42 surveyed courses. [hypothesis: code_01CE34, data_04693E]
- The forced throttle on internal courses 24 and 25 (measured on 22 only): settle with P138 repeated on those courses. [hypothesis: code_0045CE, ram_FFD672]

Located: code_01CE34 (copy at the race setup), data_04693E (course records); RAM ram_FFD672, ram_top_speed, ram_accel,
ram_drag, ram_grip, ram_steer_period; probes P057, P074-P087, P090-P092.

### Opponent AI

Answer: a computer car is driven through the same controls as a player: each frame the computer driver builds a
control byte for it (accelerate, brake, left, right) and the car then moves by the same handling rules as the
player's car, with its own five handling words. The path comes from a per-course direction map, one byte per 32 x 32 px
block of the stage: the byte under the car's centre names the heading to drive (one of the 32) and may carry a "slow"
flag. The driver steers toward that heading, comparing it with the car's direction of motion (so it corrects slides),
lets off the throttle or brakes on its four per-race speed words, and stops steering when nearly lined up. It does not
look at the other cars or the race order: no catch-up (rubber-banding) was found in the code, and putting the player
far ahead in the race changed nothing in the computer cars' driving. There are no target points or checkpoint
following in the driver: the direction map is the racing line.

The nine per-race words of each computer car (section Difficulty; values of challenge race 1, computer car 1):

| Word (slot 1) | Role | Challenge race 1, car 1 | Halving it (T6) |
|---|---|---|---|
| ram_FFD0E8 | acceleration `A` | 10 | slower start (P039) |
| ram_FFD0FA | drag `D` | 6 | faster (P040) |
| ram_FFD10C | grip `G` | 40 | different path after the first turn (P041) |
| ram_FFD0D6 | top speed | 320 (5 px per frame) | levelled at about 2.4 px per frame (P042) |
| ram_FFD0C4 | steering period | 4 | different path after the first turn (P043) |
| ram_FFD6F0 | above this speed the car considers braking for a turn | 300 | different path (P044) |
| ram_FFD6F8 | braking reference: brake when the steering error exceeds (this - speed)/2 | 384 | different path (P045) |
| ram_FFD700 | speed limit on non-axis headings (throttle off above it) | 288 | stuck near the start (P046) |
| ram_FFD708 | heading error below which it stops steering once on the map heading | 24 | different path (P047) |

- Computer cars are steered by a direction map of one byte per 32 px block (3136 bytes at ram_dir_map on challenge race 1's 56 x 56 block stage, column order as the collision map) read at the car's centre: filling the map with the code for heading 0 turned both moving computer cars to face up within 54 frames and drove them into a wall, while the idle player car was unaffected. [confirmed: P094, dir_map_read, code_042012, ram_dir_map]
- Map code: 1-32 = heading + 1; adding 20 (hex) marks a slow block where the car lets off the throttle above speed 160; with the map filled with heading 8 plus the slow flag, computer car 1 turned to heading 8 and held 155-163. [confirmed: P095, code_042012, ram_map_code]
- The driver writes a pad-like control byte for each computer car (ram_control_p2, ram_control_p3, ram_control_p4 for slots 1-3), the same bits as a pad (10 accelerate, 40 brake, 08 right, 04 left, 01 up): measured values for computer car 1 in challenge race 1: 11 (accelerate), 19 and 15 (accelerate and right or left), 09 and 05 (right or left, throttle off), 49 (brake and right) and 01. [confirmed: P094, P095, P093, ram_control_p2, ram_control_p3]
- Steering choice: the error is the map heading (x 32) minus the car's direction of motion (its heading while airborne), wrapped to -512..512; right when the error is 0 or more, left when negative; once the car's heading equals the map heading and the error is below the straight-ahead word (ram_FFD708), it stops steering. [hypothesis: code_042012, ram_FFD6E4, ram_FFD6EC, ram_FFD708]
- Speed choice: the car accelerates by default; when faster than ram_FFD6F0 and the error exceeds (ram_FFD6F8 - speed)/2 it brakes, and otherwise, still only above ram_FFD6F0, it lets off the throttle when the error has shrunk by more than 10 since the last frame; on a non-axis map heading it lets off above ram_FFD700; when moving backwards relative to its heading it only accelerates (no steering). [hypothesis: code_042012, ram_FFD6F0, ram_FFD6F8, ram_FFD700, ram_FFD24E]
- No rubber-banding: putting player 1 far ahead (laps remaining 1, progress check off) left all computer cars' positions and speeds identical to the control at frames 880-900, apart from single-frame recording offsets; the driver reads only its own car, the map and its nine words. [confirmed: P093, code_042012]
- After a car contact the driver's control byte is cleared while the car's timer (ram_coast_p2 for slot 1) counts down, so the car coasts (section Car-to-car collisions); a car whose map byte is 0 or above 40 (hex) while a per-car flag (ram_FFD208) is set is put into the put-back sequence (state 3B), a recovery for a car off the mapped course. [hypothesis: code_042012, ram_coast_p2, ram_FFD208]
- A finished computer car (laps remaining 0, ram_FFD166 for slot 1) gets an empty control byte and coasts to a stop, and when ram_FFECA0 is set every computer car only brakes. [hypothesis: code_042012, ram_FFD166, ram_FFECA0]
- Only slots 1-3 have computer drivers in this routine (four-car races); the eight-car race path (section Car-to-car collisions) has its own copy of the per-car control bytes. [hypothesis: code_042012, code_013BD6]
- The three driver entries (cpu_drive_p2 for slot 1, cpu_drive_p3 for slot 2, cpu_drive_p4 for slot 3) differ only in the per-car words they use and all call the shared step cpu_steer; a fourth caller of cpu_steer, fn_041f74, may drive slot 0 in the attract or demo race. [hypothesis: cpu_drive_p2, cpu_drive_p3, cpu_drive_p4, cpu_steer, fn_041f74]

In plain words, for a reader who wants to rebuild it: a computer car is a player whose pad is pressed by a small
routine. Each frame the routine looks up the course's direction map in the 32 x 32 px block under the car's centre,
which says "drive toward heading h here" and sometimes "go easy here". It compares that heading with the way the car
is actually moving (not the way it faces, so it corrects its own slides) and presses right when the target is
clockwise or straight ahead, left when it is anticlockwise, and lets go of the steering once it faces the target
heading and is moving within its "straight-ahead" margin (24 direction steps, about 8 degrees, in challenge race 1).
It holds the throttle by default. Above a "careful" speed (300, about 4.7 px per frame) it brakes when the steering
error is larger than half of (its braking reference 384 minus its speed), and otherwise lifts off when the error has
shrunk by more than 10 steps since the last frame (the car is already swinging into line); on a diagonal target heading it lifts off above 288 (4.5 px per frame); in a "go easy" block it
lifts off above 160 (2.5 px per frame). The car then moves by exactly the player's handling rules with its own five
numbers (challenge race 1, car 1: acceleration 10, drag 6, grip 40, top speed 320, steering period 4). It never looks
at the other cars or the race order, so there is no catch-up; after a bump it lets go of everything for 8 frames.

Open questions of this section and what would settle each:

- The steering and speed choices (sign rule, straight-ahead stop, brake and lift-off thresholds) are read from the code; only the map and the slow flag were probed: settle with a P094-style map fill per rule (a target heading 4 steps either side, a slow block, a diagonal) logging the control byte against the predicted one. [hypothesis: code_042012, ram_FFD6F0, ram_FFD6F8, ram_FFD700, ram_FFD708]
- The per-race values of the nine words for every race of each mode (only challenge race 1 recorded): settle with a census of ram_FFD6F0 to ram_FFD70C and the five handling words at frame 900 of every race (section Difficulty). [hypothesis: code_01CE34, ram_FFD6F0]
- The recovery when the map byte is 0 or above 40 (hex) under a set ram_FFD208, and what sets that flag: settle with a writer run of ram_FFD208 and a probe pushing a computer car off the mapped course. [hypothesis: code_042012, ram_FFD208]
- Whether fn_041f74 drives a car in the attract race: settle with an execution tap on fn_041f74 over the `attract` scenario. [hypothesis: fn_041f74, cpu_steer]

Located: code_042012 (computer driver, one entry per computer slot, shared steering and speed logic), dir_map_read in
code_00635E (block map read), code_01CE34 (per-race words); RAM ram_dir_map (direction map), ram_control_p2 to ram_control_p4
(computer control bytes), ram_FFD6F0, ram_FFD6F8, ram_FFD700, ram_FFD708 (+ 2 per car), ram_FFD6E4 (steering error),
ram_FFD24E (last error); probes P039-P047, P093, P094, P095.

### Input and J-Cart four-player

Answer: once per frame, in the vertical-blank routine, the game reads pads 1 and 2 at the standard I/O ports (A10003,
A10005) with the three-button select protocol and turns each into a control byte: 01 Up, 02 Down, 04 Left, 08 Right,
10 B, 20 C, 40 A, 80 Start. Players 3 and 4 come from the J-Cart: if it was detected at power-on, the game writes 0 and
then 1 to the cartridge port 38FFFE, reading a word each time; the low byte carries pad 3 and the high byte pad 4, and
they are folded into control bytes 3 and 4 with the same bits. Control byte n drives car slot n: pad 1 the car in slot
0, pad 2 slot 1, pad 3 slot 2, pad 4 slot 3; in races with computer cars the computer driver overwrites the bytes of
its slots each frame. In a race B accelerates, A brakes and reverses, Left and Right steer; Up, Down and C do nothing to
the car. The other cartridge address, 380001, is not part of the J-Cart: it is the data line of the cartridge's save
memory (EEPROM), used at power-on and when the construction kit saves a course.

| Input held (four-player race, P096-P099) | Word at 38FFFE with 0 written, then with 1 written | Control bytes 2, 3, 4 | Car that responded |
|---|---|---|---|
| none (control) | B3B3, FFFF | 00, 00, 00 | none |
| pad 3 B | B3B3, FFEF | 00, 10, 00 | slot 2 drove off (speed 354) |
| pad 4 A and Right | A3B3, F7FF | 00, 00, 48 | slot 3 reversed and turned (direction 595, speed 154) |
| pad 3 Left and C, pad 4 Up | B2B3, FEDB | 00, 24, 01 | slot 2 turned left on the spot (heading 0 to 20); slot 3 did not move |
| pad 2 B and Left | B3B3, FFFF | 14, 00, 00 | slot 1 drove off turning left (direction 427, speed 340) |

- Pads 1 and 2 are read every frame by pad_read (called from the vertical-blank code) at io_pad1_data and io_pad2_data and stored as control bytes ram_control_p1 (pad 1) and ram_control_p2 (pad 2): pad 1 B gave 10, pad 2 B and Left gave 14. [confirmed: P075, P099, pad_read, code_007790, code_01F96A, ram_control_p1, ram_control_p2, io_pad1_data, io_pad2_data]
- Button map of every control byte: 01 Up, 02 Down, 04 Left, 08 Right, 10 B, 20 C, 40 A, 80 Start (active high); in a race B is accelerate, A brake and reverse, Right and Left steer clockwise and anticlockwise. [confirmed: P096, P097, P098, P099, P077, P079, ram_control_car]
- Up, Down and C are not read by the movement or steering code: pad 4 Up alone left its car on the grid, and pad 3 C with Left only turned its car on the spot, as steering alone does at rest. [confirmed: P098, P081, code_03F834]
- J-Cart detection at power-on (jcart_detect, from the boot code): 38FFFE is written 0 and then 1 and bit 6 of the word read must follow it; the flag ram_jcart_found is then 1 (it was 1 in every four-player run). [confirmed: P100, P096, jcart_detect, code_0002FA, ram_jcart_found]
- J-Cart read every frame when the flag is set (jcart_read, after the pad read): write 0 to 38FFFE and keep the word (ram_jcart_word0), write 1 and keep the word (ram_jcart_word1); low byte = pad 3, high byte = pad 4, buttons active low as on a pad port (with 0 written: Up, Down, A, Start; with 1 written: Up, Down, Left, Right, B, C); decoded into ram_control_p3 (pad 3) and ram_control_p4 (pad 4). The measured words for four input sets are in the table above. [confirmed: P096, P097, P098, P100, jcart_read, code_0419AE, jcart_pad34, ram_jcart_word0, ram_jcart_word1, ram_control_p3, ram_control_p4]
- Pad n drives the car in slot n - 1: each car's control byte is copied into the moving car's working byte (ram_control_car) by the per-slot copy code; pad 3 moved only slot 2, pad 4 only slot 3, pad 2 only slot 1. [confirmed: P096, P097, P099, code_040F2A, ram_control_car]
- In one-player races the computer driver writes the bytes of slots 1-3 after the pads are read, so pads 2-4 have no effect there. [hypothesis: code_042012, code_01F96A]
- The control byte reads 0 during the race-start countdown and the out-of-view reappearing sequence even while the button is held (pad 3 B gave 00 until the sequence ended at frame 236); the countdown still counts the held frames for the launch (section Acceleration). [confirmed: P074, P096, ram_control_p1, ram_launch_hold]
- A four-pad adapter on port 1 (peripheral id 7) is also supported: then all four control bytes come from it; otherwise bytes 3 and 4 are cleared before the J-Cart read. A six-button pad's extra buttons land in a second byte (ram_FFC20A row) that the race does not use. [hypothesis: code_007790, pad_read, ram_FFC20A]
- Four-pad adapter read fn_007ab4: TH held low, each nibble clocked by toggling TR and waiting for TL to follow (up to 1024 polls in all; a timeout ends the read); a header byte, four type nibbles, then two nibbles per pad of type 0 or 1 as its inverted button byte, other types leaving the pad's word clear. Type 1 is read like type 0, two nibbles. [hypothesis: code_007AB4, fn_007ab4, code_007790]
- The vertical-blank interrupt keeps two generations of the control bytes for press detection: before the read it saves pad 1's byte as the last frame left it (ram_FFD67E) and the last frame's fresh copies (ram_FFEC6C to FFEC6F into ram_FFD680, ram_FFD682, ram_FFD684, ram_FFD686); after the pad and J-Cart reads it copies the four fresh control bytes to ram_FFEC6C to FFEC6F, before any routing or computer driver changes them; the pause toggles on Start set in the fresh copy and clear in the saved one. [hypothesis: code_01F96A, code_0068D2, ram_FFEC6C, ram_FFD680, ram_FFD67E]
- Outside the race the screens' frame step (screen_frame) routes the pads into pad 1's control byte by the mode word ram_input_mode: mode 0 lets the first pad with any button held take over, held for 20 frames after its last press (ram_FFD762); modes 2 and 4 do the same over the pads whose word in the pad table at ram_pad1_player is -1 (mode 2) or not -1 (mode 4); modes 1, 3 and 5 copy one fixed pad (ram_pad1_player or ram_input_pad); so on menus any pad can drive pad 1's choices. [hypothesis: code_00A498, input_route_screen, ram_input_mode, ram_input_pad, ram_FFD762]
- During a race the routing is input_route: mode 4 copies each pad's byte to the control byte its pad-table word names (-1 skips), and while ram_FFD750 is set pad 1's byte is replaced by pad ram_FFEAF4's; modes 1 and 5 copy one fixed pad into pad 1's byte. [hypothesis: code_006190, input_route, ram_pad1_player, ram_FFEAF4]
- The pad table ram_pad1_player to ram_pad4_player holds, per pad, the index of the player (control byte) it drives, -1 for an unused pad: one-player Challenge and Head To Head races held 0, -1, -1, -1 and a four-player race 0, 1, 2, 3, unchanged over 200 race frames. [confirmed: P153, P154, P155, t42c_padc_challenge_20261016T124015, t42c_padc_h2h_20261016T124030, t42c_padc_multi_20261016T124032, code_006190, code_00F0C2]
- 380001 is the cartridge EEPROM's data line, not a J-Cart register: it is read (with clocking writes to 300000) only in bursts, at power-on (frames 566-581, about 16,000 reads) and when the construction kit saves a course (frames 3352-3422), and never in 600 frames of a four-player race, while 38FFFE is used every frame in all three runs. [confirmed: P100, t9e_boot_20261013T222226, t9e_kit_20261013T222332, t9e_multi_20261013T222249, code_005426, code_004D34, eeprom_data_in]

In plain words, for a reader who wants to rebuild it: once per frame, at the vertical blank, each of the four pads
becomes one byte with one bit per button (Up, Down, Left, Right, B, C, A, Start). Pads 1 and 2 come from the console's
ports, pads 3 and 4 from the J-Cart's two extra sockets on the cartridge, read through a single address in two halves.
Pad n drives car n, and in races with computer cars the computer driver simply overwrites the bytes of the cars it
drives. In a race only four bits matter: B is the throttle, A the brake (and reverse), Left and Right steer; a press
reaches the car one frame later. The game ignores the pads during the start countdown and while a car is reappearing,
but it does count how long the throttle is held in the countdown for the launch (section Acceleration). Outside the
race a small routing step lets any pad drive the menus.

Open questions of this section and what would settle each:

- The four-pad adapter on port 1 and the six-button pad's second byte: settle with a MAME run with a multitap or six-button pad configured on port 1, logging the four control bytes. [hypothesis: code_007790, pad_read, ram_FFC20A]
- The routing modes (ram_input_mode, the pad table ram_pad1_player to ram_pad4_player, ram_input_pad, ram_FFEAF4) and which screens and race setups use which mode: settle with a writer run of ram_input_mode and ram_pad1_player from power-on through the menus and a two-player race. [hypothesis: input_route, input_route_screen, ram_input_mode, ram_pad1_player, ram_FFEAF4]
- The press-detection copies (ram_FFEC6C to FFEC6F, ram_FFD680 to ram_FFD686) and the pause: settle with a probe pressing Start for one frame in a race and logging both copies and the pause flag. [hypothesis: code_01F96A, ram_FFEC6C, ram_FFD680]
- Pads 2-4 in one-player races: settle with pad 2 B held in `challenge` and the slot 1 control byte logged. [hypothesis: code_042012, code_01F96A]

Located: pad_read in code_007790 (pad read), code_01F96A (vertical-blank input step), jcart_detect (J-Cart detection),
jcart_read and code_0419AE to code_041A5C (J-Cart read and decode), code_040F2A (control byte per car), code_005426 and
code_004D34 (EEPROM access); RAM ram_control_p1 to ram_control_p4, ram_control_car, ram_jcart_found, ram_jcart_word0, ram_jcart_word1; ports
io_pad1_data, io_pad2_data, jcart_pad34 (38FFFE), eeprom_data_in (380001); probes P096-P100.

## Group 6: Data

### How a course fits together (overview for adding Mini Micro levels)

In plain terms there are two kinds of course, and they reach the same race engine by different roads. A course
stored in the cartridge is only a number from 0 to 66. At load the game looks that number up in some thirty lists
(one entry per course in each), unpacks the art, the display blocks, the maps, the checkpoint lists and the
opponents' direction map into fixed places in work RAM, and copies one switch byte, the half-scale flag, from a
67-byte list: 1 means the course is drawn at half scale (Mini Micro), 0 means normal scale. The maps block is the
heart of a course: two words for its width and height in 32 x 32 px blocks, then a display map and a collision map
of one byte per block; the engine needs nothing else to know where the track, the walls and the off-track areas are.
A construction-kit course is instead one 147-byte record: a name, a 16 x 16 map of pieces (two pieces per byte),
four art-variant bytes, then the vehicle, the palette mode, top speed, grip and acceleration. The cartridge's
EEPROM keeps nine such records in 149-byte slots. For a kit race the game takes course number 66 and builds the
same pieces a cartridge course would unpack (the maps, the checkpoint lists and the piece art) from the record by
walking the circuit, so from then on the race runs exactly as on a cartridge course. The difference that matters
for Mini Micro levels: a cartridge course becomes Mini Micro by setting its byte in the flag list (no code change;
proper half-size art is the real work), while the kit race setup writes the flag as 0 itself, so a Mini Micro kit
course needs that one store changed plus half-scale piece art (section Pool-table levels; forcing the flag on a kit
race gave a working but badly drawn half-scale race, P111). Three finished Mini Micro courses (numbers 50, 53 and 54)
are raced only in the eight-car game, reached from Extra Options, Party Play, 8 Player Share (P113, P116). Details of each part are
in the sections below. [hypothesis: P103, P105, P102, P111, P113, ram_maps, ram_kit_course, ram_saved_courses,
ram_half_scale_flag, kit_race_setup, kit_race_maps]

### Level data and loading

Answer: a course is not one record. It is an internal course number (ram_FFD672, 0 to 66) that indexes some thirty
parallel tables in ROM, each holding one entry per course number. Pointer tables lead to Imploder-compressed blocks
(all level graphics, maps, the direction map and the checkpoint lists are compressed); byte tables hold per-course
switches (the half-scale flag among them); a nine-word course record holds the handling and sound numbers. Loading is
one routine, the course setup (code_01CE34 and the helpers it calls), which reads each table at the course number,
unpacks 13 blocks in a fixed order into fixed work-RAM buffers and derives the map pointers and the stage size. It
takes about 67 frames (1.3 s), from frame 714 to 781 of a load from the course select (P103).

What a course is made of (sizes in bytes after unpacking; entry counts from the table sizes; the four measured
courses are list courses 17 Pool Slalom, 41 Ball Chase, 24 Ferry Fiasco and 1, internal 19, 18, 34 and 2):

| Item | Pointer table (67 entries) | Present / distinct | Unpacked to | Layout after unpacking | Four courses |
|---|---|---|---|---|---|
| Level tile art (patterns) | data_045908 | 63 / 19 | decrunch_buf, then VRAM | 32 bytes per 8 x 8 tile | 12,832 / 19,072 / 25,056 / 25,504 (401-797 tiles) |
| Display blocks | data_04611C | 63 / 19 | ram_FFA0AC | 255 or 256 blocks of 4 x 4 tile names (32 bytes each) | 8,160 / 8,160 / 8,192 / 8,192 |
| Maps | data_045DF8 | 61 / 59 | ram_maps | width and height in blocks (2 words), display block map, collision block map (one byte per 32 x 32 px block each) | 9,156 (52 x 88) / 7,044 (44 x 80) / 8,196 (64 x 64) / 4,612 (48 x 48) |
| Collision cell patterns | data_046832 | 65 / 3 | ram_block_patterns | 256 patterns of 4 x 4 cell codes (16 bytes) | 4,096 each (two sets among the four) |
| Opponents' direction map | data_046010 | 41 / 41 | decrunch_buf | width and height, then one byte per block | 4,580 / 3,524 / none / 2,308 |
| Second map layer (optional) | data_045F04 | 10 / 8 | ram_FF1A04 | - | Ferry Fiasco only, 8,196 |
| Checkpoint lists | data_0463BE | 61 / 56 | ram_cp_list_buf | the lists searched by the checkpoint lookup | 1,488 / 1,472 / 1,440 / 736 |
| Vehicle art | data_039128 (16-byte records) | 67 / 19 | decrunch_buf, then VRAM | tile image (size words, 16-colour palette, tile map, tiles) | 5,030 / 7,590 / 7,686 / 7,334 |
| Second tile image | data_045CEC | 54 / 13 | decrunch_buf | tile image | 3,110 / 3,110 / 3,078 / 2,854 |
| Course object art (optional) | data_0457FC | 45 / 16 | decrunch_buf | tile image | 10,598 / 10,598 / 7,078 / 3,526 |
| Trigger objects | data_03633C | 21 / 21 | ram_FFD426 | word list up to an end mark (four 8-byte object records) | uncompressed |
| Course record | data_04693E | 66 / 29 | slot words, ram_FFE682 | nine words (next section) | uncompressed, 18 bytes |

Besides these, two blocks are the same for every course (imp_276 into ram_FF9D2C, 928 bytes; imp_081 into
ram_FF750C, 6,912 bytes) and two sprite-art tile images are common (imp_080, imp_101).

- A course is the internal course number ram_FFD672: during the load each per-course table was read once, at that number's entry (byte tables at the number, pointer tables at 4 times it, the 8-byte start-line and 16-byte vehicle records at 8 and 16 times it), in all four loads. [confirmed: t10dc_pool_20261013T223302, t10dc_bc_20261013T223305, t10dc_ferry_20261013T223308, t10dc_c1_20261013T223310, code_01CE34, ram_FFD672]
- Load sequence: 13 calls of the decompressor per load, always in this order and from the same callers: the fixed block (fn_01d274), level tile art (fn_03ee64, then sent to VRAM by vdp_dma), second tile image (fn_041526), four sprite-art tile images (fn_03f09c common, fn_03f124 vehicle art then a common set, fn_03f106 course object art, all through fn_03f29e), maps (fn_035954) with the optional second layer and the direction map, display blocks (fn_03591a), the second fixed block, collision cell patterns and checkpoint lists (code_01CE34); then the initial draw (fn_03de0a). Nine of the 13 sources depend on the course. [confirmed: P103, t10dc_pool_20261013T223302, t10dc_bc_20261013T223305, t10dc_ferry_20261013T223308, t10dc_c1_20261013T223310, imp_decrunch]
- Level data is compressed: every per-course block named above is an Imploder block of config/regions.retail.tsv (an imp_ region) and decoded in RAM; the uncompressed per-course data are the byte switches, the nine-word course record, the trigger-object lists and small word tables. [confirmed: P103, t10dc_pool_20261013T223302, t10dc_bc_20261013T223305, t10dc_ferry_20261013T223308, config/oracle/decrunch.tsv]
- Maps block layout: a width word and a height word (in 32 px blocks), then the display block map, then the collision block map, each width x height bytes; the decoded size was 4 + 2 x width x height on all four courses, and the routine fn_03f188 then points ram_FFCFE6 at the display map and ram_block_map_ptr at the collision map and sets the stage size to 32 times the block counts. [confirmed: P103, t10w_pool_20261013T224309, t10w_bc_20261013T224315, t10w_ferry_20261013T224320, fn_03f188, ram_FFCFE6, ram_block_map_ptr, ram_maps]
- The tile drawers read the display block map and draw each block from its 32-byte definition at ram_FFA0AC (4 x 4 tile names); block numbers below the per-course byte ram_FFD694 (data_046228, 16 values from 45 to 255) take a different drawing path, and a per-course bit table (pointer ram_FFD698 from data_046C78, 13 distinct) is tested for every block drawn. [hypothesis: code_03DE0A, code_03E8C4, ram_FFA0AC, ram_FFD694, ram_FFD698]
- Opponents' direction map: decoded into decrunch_buf as a width and height word then one byte per block, so the map read by the computer driver starts 4 bytes in (ram_dir_map); its size was 4 + width x height on the three courses that have one. 41 of the 67 numbers have one; on Ferry Fiasco the call finds no block and returns without writing. [confirmed: P103, t10dc_pool_20261013T223302, t10dc_bc_20261013T223305, t10dc_c1_20261013T223310, dir_map_read, ram_dir_map, data_046010]
- Checkpoint lists are unpacked to ram_cp_list_buf and the lookup pointer ram_cp_lists is set to that address; the checkpoint count (176, or 88 when the byte of data_0467EE is set, 39 of 67) and the four ordering limits are written by the same setup at one frame. [confirmed: t10w_pool_20261013T224309, t10w_bc_20261013T224315, t10w_ferry_20261013T224320, code_01CE34, ram_cp_list_buf, ram_cp_count]
- Every per-course word is written once per load by the course setup: the half-scale flag (writer 01CF22), checkpoint count and limits (01CF62-01CF7A), map pointers (03F1B6, 03F1BA), course record pointer and sound numbers (01D0EE-01D106), wrap bytes (01D1F6, 01D1FC), switches ram_FFEC08, ram_FFEC0A, ram_bounce_sw, ram_FFEC6A (01CEB6-01CEDA); the buffers are filled by the decompressor's copy and decode loops. [confirmed: t10w_pool_20261013T224309, t10w_bc_20261013T224315, t10w_ferry_20261013T224320, code_01CE34]
- Trigger objects: when the course's entry of data_03633C is not empty its words are copied to ram_FFD426 up to an end mark (17 words read on Ball Chase, 6 on Ferry Fiasco); 21 course numbers have such a list. [hypothesis: code_01CE34, data_03633C, ram_FFD426, P103]
- The start line (the four car positions' corners and the first checkpoint line) comes from an 8-byte entry of data_0464CA and the initial view position from a 4-byte entry of data_0466E2. [hypothesis: code_01CE34, data_0464CA, data_0466E2]
- Course palettes come from a count-prefixed word list per course (data_046F2C, 33 distinct) copied to the palette table ram_FFC27A; each tile image adds its 16-colour palette to a slot of that table. [hypothesis: fn_03f1cc, code_03F278, ram_FFC27A]
- Sprite art by mode: the common sprite set is one of four records (dat_043E84 rule modes 1-2 and the team game, dat_043E90 time trial, dat_043E9C rule mode 3, dat_043EA8 four players; the eight-car game by ram_FFED36), and the vehicle art is followed by a second record, dat_03911C on the half-scale courses 19, 50, 53 and 54, dat_039110 when the course byte ram_FFEC68 is set, else dat_039104. [hypothesis: fn_03f09c, fn_03f124, code_03F09C, dat_043E84, dat_043E90, dat_043E9C, dat_043EA8, dat_03911C, dat_039110, dat_039104]
- The second tile image (dat_045CEC) brings its own 16 colours for palette line 1 and its name map, written at VRAM E000 hex in rows of 64 cells and a second time from column 24; five of the images keep palette line 0. [hypothesis: fn_041526, code_041526, dat_045CEC, ram_FFC29A, ram_FFCFB0]
- The tile-image loader applies the name flip bits in software: bit 11 mirrors a tile left to right, bit 12 reverses its rows, both do both, before the tiles go to VRAM. [hypothesis: code_03F278, fn_03f3b2, fn_03f460]
- The sprite list (buffer FFCB7C hex) is reset by fn_03f278 (count ram_FFC240 0, pointer ram_FFC242 to the start) and ended by fn_03f286, which clears the link field of the last 8-byte entry (keeps bits 8-11 of its second word), as the VDP sprite table format requires. [hypothesis: fn_03f278, fn_03f286, code_03F278, ram_FFC240, ram_FFC242]

Pool-table course data compared with a normal course's: the record kinds are the same on every course; no record is
specific to pool tables. Between the two pool-table courses (Pool Slalom, Mini Micro, and Ball Chase, normal) only the
half-scale flag, the level tile art, display blocks, maps, direction map, checkpoint lists and vehicle art differ;
they share the second tile image, the course object art (the billiard balls are the likely content) and the collision
cell pattern set.

- Pool Slalom and Ball Chase load the same blocks for the second tile image, the course object art and the collision cell patterns, and different blocks for the other six course-dependent items; Pool Slalom's level tile art is the smallest of the four measured (401 tiles, against 596, 783 and 797). [confirmed: P103, t10dc_pool_20261013T223302, t10dc_bc_20261013T223305, t10dc_ferry_20261013T223308, t10dc_c1_20261013T223310]
- Setting the half-scale flag on a normal course (Ferry Fiasco) gave a working half-scale race: the course drawn at half scale and recognisable but coarser, the car at its normal size; so a further Mini Micro course needs the flag (data) and art made for the half-scale drawing, not new code. [confirmed: P105, ram_half_scale_flag, code_03EA82]
- The half-scale drawers draw a 32 px block as 2 x 2 tiles taken from its 4 x 4 definition (they index the definition by half the scroll position), which is why normal art looks coarser at half scale. [hypothesis: code_03EA82, P105]
- Map cells in half-scale: the collision cell lookup has no half-scale branch, so cells stay 8 x 8 stage px (4 x 4 screen px on Pool Slalom) and blocks 32 stage px (16 screen px); only the drawing and the view work at half scale. [hypothesis: code_0418EA, code_03EA82, ram_half_scale_flag]
- Four course numbers have the half-scale flag: 19 (Pool Slalom) and 50, 53, 54, which appear in neither the time-trial list nor the challenge race records. All three load and race at half scale when set as the course number (50 a pool table, 53 and 54 gardens; section Pool-table levels): three complete Mini Micro courses, raced in the eight-car game (next lines). [hypothesis: data_04637A, data_0452C5, data_04454C, P113]
- Writer census of the course word ram_FFD672 (16 store sites in the listing, no long or indirect store over it): the only list holding 50, 53 or 54 is the 3-byte list dat_0452C2 (exactly 50, 53, 54, the three bytes just before the time-trial list dat_0452C5), stepped by the course select of the eight-car game fn_04239a (store at 0423BE, wrap at 3, skipped when ram_FFD74C is 120 so later rounds keep the course); the time-trial, season, head-to-head, bonus, kit and four-player lists hold none of the three. [hypothesis: fn_04239a, dat_0452C2, data_0452C5, data_04454C, dat_04446C, ram_FFD672, ram_FFD74C]
- The eight-car game is reached by menus: Extra Options, Party Play, 8 Player Share sets the mode word ram_FFE69A to 7 (ram_FFED36 0); its course select shows 1 Pool Problems (50), 2 Tree Trouble (53), 3 Tiny Trees (54), each Right step writing the next of 50, 53, 54 and wrapping to 50; the race has eight small cars, 50 on a pool table, 53 in a garden. [confirmed: P116, t43w_p8_20261014T190418, t43w_p8_20261014T190439, t43w_p8b_20261014T190454, fn_04239a, dat_0452C2, ram_FFD672, ram_FFE69A, code_000D14]
- Mode 7 is set by the Party Play menu code_012688 (store at 0127FC) for its rows 1 to 3 with ram_FFED36 0, 6 and 4; the mode dispatch at 000606 sends mode 7 to code_000D14, which sets ram_FFEC80 to 1 and runs the eight-car race; only row 1 (8 Player Share) was run, so 6 and 4 Player Share using the same select is static reading. [hypothesis: code_012688, code_000D14, ram_FFE69A, ram_FFED36, ram_FFEC80, P116]
- Course writers measured per mode: head-to-head store at 00130E writes 16, four-player single race store at 0014C0 writes 2, challenge race 0 store at 001106 writes 16 from its race record, each once after the boot clears; the bonus race store at 0010A4 writes 55 plus the bonus index (55 in the forced run, a one-red-car time-limited race on wooden planks); none writes 50, 53 or 54. [confirmed: P114, P115, ram_FFD672, code_00102E, code_0012B4, code_00143C]
- For adding Mini Micro levels: the eight-car list is the one place a menu offers Mini Micro courses other than Pool Slalom. Swapping one of its three bytes for another course number (19, or a new course's number) is a one-byte data change; a fourth entry cannot be added in place, because the list sits directly before the time-trial list and the select wraps at the constant 3, so a longer list must move elsewhere with that constant changed (the names need no change, next lines). [hypothesis: dat_0452C2, data_0452C5, fn_04239a, P116]
- The eight-car select takes its course names from the common course name list dat_04548A, indexed by course number: each step stores dat_0452C2[ram_FFEAFA] in ram_FFD672, the preview copies it to ram_FFE800, and the panel's course line (code_00BE02 at 00C254) skips that many length-prefixed entries and copies the name into the text record ram_FFE8C6, with ram_FFEAFA + 1 in front; no select-specific name table exists. Measured: the only readers of the list during the select are the course line's skip and copy loops (pcs 00C26C to 00C28A), reading entry 50, 53, 54 as the select steps; with the first list byte read as 19 the first entry shows 1 Pool Slalom and the line reads entry 19. [confirmed: P161, t45n_varA_20261016T150444, dat_04548A, code_00BE02, ram_FFE800, ram_FFEAFA, ram_FFE8C6]
- The name list dat_04548A holds exactly 67 entries, one per course number 0 to 66 (35, 38 and 40 named OLDTRACK, 55 to 59 3 Wins Bonus!, 66 constmap), names 8 to 15 characters, and ends at 0457FC where data_0457FC starts: no free byte after it. Its other readers (code_009CBA TT rows via dat_0452C5, code_00A6C2 race records, fn_00c84c via ram_FFE800) all index it by course number. [hypothesis: dat_04548A, data_0454A9, data_0457FC, code_009CBA, code_00A6C2, code_00C84C]
- A fourth eight-car entry works once the select's constants change: with the wrap compare at 0423FA read as 4 and the negative-wrap store at 042408 as 3, the select steps 50, 53, 54 and then the fourth byte, which is the first time-trial list byte dat_0452C5[0] (course 2, shown as 4 BBQ Burnoff with its own name), wraps to 50, and Left from the first entry reaches it. So adding an entry needs: the list moved off 0452C2 (it abuts dat_0452C5; the region split data_0452C2 / data_0452C4 moves with it), the lea at 0423AA pointed at the new list, the constants 3 (0423FA) and 2 (042408) raised. [confirmed: P161, t45n_varB_20261016T150451, fn_04239a, dat_0452C2, dat_0452C5]
- An existing course number needs no name work; a new course number needs an entry in dat_04548A (which has no free space, so the list and its four readers would move) plus every per-course table of the capacity lines below. The list number in front of the name is printed in one or two digits (tens counted by repeated subtraction), so the line is correct up to 99 entries; the longest name (15) plus the 4 record bytes fits the text record, which also takes the kit's 16-character names. [hypothesis: code_00BE02, code_00C84C, ram_FFE8C6, dat_04548A]

Open questions (what would settle each): what the per-course draw-bit table (ram_FFD698) and the block threshold (ram_FFD694) mean (one course with the threshold poked, screens compared); whether the start line and initial view tables have the layout claimed (a writer run of the four car positions at a load); the second map layer's role (a dump of ram_FF1A04 on Ferry Fiasco with a reader run in its race).

Capacity and what a new course would need (a plan of what would have to change, not an instruction):

- Number of courses: there is no count byte. Every per-course table is a fixed array of 67 entries packed against the next table (byte tables 67 bytes, pointer tables 268 bytes), so course numbers 0 to 66 are the capacity; number 66 is the construction kit's course, whose maps are built in RAM. [hypothesis: data_045DF8, data_04637A, data_0462AF, code_001978]
- Five course numbers (17, 32, 35, 38 and 40) have no maps, no direction map and no checkpoint lists and are not in the time-trial list or the challenge race records: free entries a new course could fill without moving any table. [hypothesis: data_045DF8, data_0463BE, data_0452C5, data_04454C]
- A new course number would need an entry in every per-course table: tile art, display blocks, maps, collision pattern set, checkpoint lists, direction map (if computer cars race it), vehicle art record, second tile image, object art, trigger list, course record, palette list, start line, initial view, draw-bit table, the byte switches (half-scale flag in data_04637A, 88-checkpoint flag, wrap, block threshold and four others) and a course name; numbers beyond 66 would need every table extended and moved, which means changing the table addresses in the code. [hypothesis: code_01CE34, code_035890, code_03F09C, code_03EE64, code_041526]
- To be selectable a course must also appear in a list: the time-trial list holds 27 entries and the course select wraps at 27 (a constant in the code), and the challenge race records hold 26 entries of 14 bytes. [hypothesis: data_0452C5, code_00143C, data_04454C, code_00102E]

Located: code_01CE34 (course setup), code_035890 (maps, direction map, display blocks), code_03EE64 (tile art),
code_041526 (second tile image), code_03F09C and code_03F278 (sprite art, palettes, fn_03f188 map pointers),
imp_decrunch; tables data_045908, data_04611C, data_045DF8, data_046832, data_046010, data_045F04, data_0463BE,
data_039128, data_045CEC, data_0457FC, data_03633C, data_04693E, data_0464CA, data_0466E2, data_046C78, data_046F2C;
RAM ram_maps, ram_FFA0AC, ram_block_patterns, ram_cp_list_buf, ram_FF1A04, ram_FFCFE6, ram_block_map_ptr, decrunch_buf; probes P103,
P105; runs t10dc_pool_20261013T223302, t10dc_bc_20261013T223305, t10dc_ferry_20261013T223308,
t10dc_c1_20261013T223310, t10w_pool_20261013T224309, t10w_bc_20261013T224315, t10w_ferry_20261013T224320.

### Construction kit and saved tracks

Answer: the kit builds a course from pieces. The player fills a 16 x 16 map with 16 kinds of piece ("blocks" on the
editor screen: the course start, straight and diagonal track pieces, water and others), each piece 128 x 128 stage px;
names the course (16 letters); picks one of 10 vehicles; and sets attributes (speed, grip, acceleration, weather). The
whole course is one 147-byte record in work RAM (ram_kit_course). Saving copies the record into one of nine 149-byte slots
of the cartridge's 2048-byte EEPROM (slots 1 and 2 hold the two preset courses). The password is the same 147 bytes
written as 252 characters, 5 bits per character, with two check characters every 30. For a race the kit's course
becomes internal course 66: the maps and the checkpoint lists are generated in RAM by walking the circuit of pieces,
and the art is assembled from one small graphic block per piece kind. No direction map is built: kit races have no
computer cars.

Menus (screens seen in runs t10kit_20261013T223945, t10ed_20261013T224437, t10kitdc_20261013T224516): kit menu Single
Race, Time Trial, Edit, New, Exit; edit menu Course Name, Course Editor, Vehicle Graphics, Attributes, Test Course,
Course Storage, Main Menu; Course Storage: Save Course, Load Course, Enter Course Password, Display Course Password,
Exit. The editor shows the 16 pieces as a 4 x 4 palette ("A to Edit Map. C to Change Block"); Test Course checks the
layout and reports "Track Is A Legal Circuit Of Length" and a number (62 for preset slot 1). The load picker lists
the course with its vehicle (the "4x4" beside NEW TRACK in T1's run is the vehicle, a four-wheel-drive car) and its
speed, grip, acceleration and weather.

The course record (147 bytes, ram_kit_course to FFEDD2):

| Bytes | Field | Measured |
|---|---|---|
| 0-9 | course name: 16 characters of 5 bits (1-26 letters, 0 space), packed high bit first | decoded to the typed name (P102) |
| 10-137 | the map: 16 x 16 cells, one 4-bit piece code each (two cells per byte) | a new course holds one piece code in all 256 cells; the presets use 15 codes |
| 138-146 | options: art variants (2 bits per piece kind, bytes 138-141; kind 5's picks the art set), vehicle (0-9), weather, top speed, grip, acceleration | a new course: zeros, then 100, 5, 5 |

EEPROM layout (2048 bytes, mirrored byte for byte by the RAM image at ram_eeprom_image):

| Offset | Size | Contents |
|---|---|---|
| 0x000 | 516 | three blocks of 45, 48 and 162 words, each followed by its word sum (game records) |
| 0x204 | 9 x 149 | course slots 1-9: 147 record bytes, the low byte of their byte sum, a zero byte |
| 0x742 | 110 + 74 | two more blocks with word sums (records and statistics) |

- Saving a course to slot 3 changed 138 bytes of the 2048-byte EEPROM, all inside 0x32E-0x3C1, the span of slot 3 when nine 149-byte slots start at 0x204; the slot's 147 bytes equal the RAM record at ram_kit_course, followed by the low byte of their byte sum and a zero byte; the checksum held in all nine slots (slots 4-9 empty, all zero; slots 1 and 2 the presets). [confirmed: P102, ram_kit_course, ram_eeprom_image, eeprom_data_in]
- The RAM image ram_eeprom_image mirrors the whole EEPROM: slot n is copied at ram_saved_courses + 149 x (n - 1) (code_00B25C), and the save routine recomputes the word sums of the three leading blocks and the byte sum of every slot over the image before the whole 2048 bytes are clocked out through the EEPROM data line (300000 written, eeprom_data_in read: 16,387 reads at power-on and a burst of about 70 frames at a save). [hypothesis: code_004D34, code_005426, code_00B25C, ram_saved_courses, P100]
- Reading the EEPROM (fn_0054e4, 2048 bytes from address 0 at power-on): a two-wire serial protocol on 300000 hex (bit 0 data, bit 1 clock) with the data line read at bit 7 of 380001 hex: stop, then start and device byte A0 hex + 2 x address bits 8-10 retried up to 51 times until acknowledged, the address low byte, a repeated start, device byte A1 hex, and a sequential read with an acknowledge before each next byte, then a stop; each acknowledge wait polls up to 499 times. This is the access pattern of a 2 KiB I2C-style serial EEPROM. [hypothesis: code_0054E4, fn_0054e4, code_005426, code_005480]
- The name field is 16 letters of 5 bits: the saved NEW TRACK's first 10 bytes decode to N, E, W, space, T, R, A, C, K and seven spaces; the name editor offers A-Z, space and "!". [confirmed: P102, ram_kit_course]
- The map field is 16 x 16 four-bit piece codes; the kit's race setup scans it for the course start and places the cars there, each cell being 128 px (4 x 4 blocks); the circuit traced from it gives the length word ram_FFED24 (62 for preset slot 1, as shown by Test Course). [hypothesis: code_001978, code_00266E, ram_FFED24, P107]
- Options: the vehicle byte (ram_FFEDCE, 0-9) picks a 16-byte vehicle record from data_03D9FA (10 records, all among the courses' 19 vehicle art blocks); top speed = 200 + 1.5 x ram_FFEDD0, acceleration = 5 + ram_FFEDD2, drag and grip from ram_FFEDD1, steering period 3; weather ram_FFEDCF value 3 forces drag 1 and grip 2 and values 3 and 4 select other palettes. What looked like theme bits of ram_FFEDCB are the art variant of piece kind 5 (bits 4-5; the four variant bytes from ram_FFEDCA hold 2 bits per kind): the kit race setup uses them to pick one of four tile-image records (dat_00260E) before the piece art, so the kind-5 variant chooses an art set for the whole course. [hypothesis: code_001978, kit_race_setup, kit_piece_blocks, data_03D9FA, ram_FFEDCE, ram_FFEDD0, ram_FFEDD1, ram_FFEDD2, ram_FFEDCF, ram_FFEDCB, dat_00260E]
- Password: the encoder (code_010EE2, output ram_FF9D2C) reads the 147-byte record as 1,176 bits and writes one 5-bit value per character (236 characters, the last padded with zeros), adding after every 30 characters, and after the last, two check characters holding the low 10 bits of the sum of those 30 values; the screen shows 252 characters in 8 parts of 32 (part 8: 28), changed with Up and Down. Poking the first map byte to 0 changed exactly characters 17-18 of part 1 and its two check characters, as this rule predicts. [confirmed: P101, code_010EE2, ram_FF9D2C, ram_kit_course]
- Password alphabet: 32 symbols; values 0-25 are shown as the letters A-Z and value 26 as the digit 2 (measured); the part draw shows every value from 26 up as the digit value - 24, so 27-31 are the digits 3-7, and the entry grid lists A-Z, 2 and 3-7. [hypothesis: P101, code_010EE2, ram_FF9D2C]
- Entering a password (Enter Course Password) is the encoder's inverse: the 256 characters start blank; when the player finishes, every part must have no blank among its 30 values (26 in part 8) and its two check characters must equal the low 10 bits of their sum, and the sum of all values must not be 0; then the 236 values are unpacked straight into the first 147 bytes of the course record. A failing part is reported as "There Is An Error In Part X" and the entry resumes at that part, the characters kept. No other check of the record is made. [hypothesis: code_010EE2, ram_FF9D2C, ram_kit_course]
- Kit menu (reached from the main menu code, code_0002FA): Single Race, Time Trial, Edit, New, Exit. Entering it sets the lives word to 2 and the course word to 66 and clears the race number. Left alone, it starts the attract demo after 24 steps of 64 counts of the frame counter without a pad byte, and after only 3 steps once a demo has run. Single Race and Time Trial go back to the main menu when they end; Edit and New stay in the kit menus. [hypothesis: code_010EE2, code_0002FA, ram_FFE776, ram_FFD672, ram_FFD718, ram_FFEBC6, ram_FFECB2, ram_FFC21C, fn_00a38e]
- Kit Single Race: the player count screen offers 2 Player, 3 Player, 4 Player and 4 Player Teams (four players with the team flag); the count is also the rule mode. Each round the player picks a saved course, the kit race runs with a point pause of 701, then the results and the standings screens; rounds repeat until the standings screen returns with its cursor at 0. [hypothesis: code_010EE2, ram_FFE778, ram_rule_mode, ram_FFD68E, ram_point_pause_count, ram_FFE69A]
- Kit Time Trial: 1 to 4 players, kit courses selected (ram_FFED02), then the time trial from its course select; with more than one player the input routing switches to mode 2 and the four driver words are copied to the player records. [hypothesis: code_010EE2, ram_FFED02, fn_00d3b4, ram_FFE778, ram_input_mode]
- Choosing a saved course: the nine slots in turn, wrapping both ways. For a race (Single Race, kit Time Trial) a slot whose circuit check failed cannot be taken; Edit and Load Course take any slot and copy its 147 bytes into the course record. [hypothesis: code_010EE2, code_00BC1A, ram_FFEAFA, ram_FFED00, ram_FFED30, kit_circuit_check, ram_saved_courses]
- New writes the default course: name NEW TRACK, piece 5 in all 256 map cells, art variants, vehicle and weather 0, speed 100, grip 5, acceleration 5. [hypothesis: code_010EE2, ram_kit_course, ram_FFEDCE, ram_FFEDD0]
- Course name editor: a grid of A-Z, "!" and space plus delete and end; at most 16 characters; Start also ends. The name is stored 5 bits per character: space 0, A-Z 1-26, "!" 27. [hypothesis: code_010EE2, ram_FFE8F8, ram_kit_course]
- Attributes: speed (ram_FFEDD0) is shown as its own value in MPH and kept within 50-200, so the top speed formula above spans 275-500; grip (ram_FFEDD1) and acceleration (ram_FFEDD2) are kept within 1-9; the weather (low 3 bits of ram_FFEDCF) within 0-4, shown as Normal, Rainy, Windy, Frosty and Lightning. Left and right step a value by 1 and stop at the ends; none wraps. Vehicle Graphics offers the 10 vehicles in two rows of five. [hypothesis: code_010EE2, ram_FFEDD0, ram_FFEDD1, ram_FFEDD2, ram_FFEDCF, ram_FFEDCE]
- Saving: only a named course can be saved ("You Must Name Course Before Selecting Save"); the save screen lists slots 1-9 and Exit, and a slot with a name asks "Slot Not Empty, Overwrite?" with No preselected. The code checks no slot number, so the two preset slots can be overwritten too. A save copies the 147 bytes into the slot, resets that slot's two time-trial records (race and lap, 12 bytes from ram_FFF5E0 + 12 x slot) to the empty time 4:59.99, voids the stored time-trial block (course and mode words set to 255) and writes the EEPROM. Leaving the edit menu by Main Menu asks "Do You Wish To Save Before Exiting?"; Load Course first asks "Save Current Course?" and, after Yes, loads only if a save was made. [hypothesis: code_010EE2, ram_FFED08, ram_FFF5E0, ram_FFD76C, ram_FFD76E, eeprom_save, code_013BD6]
- The kit's race is internal course 66 (set by the kit setup); its stage was 72 x 72 blocks (2,304 px) and its checkpoint count 176. The kit setup loads no maps, checkpoint lists or direction map from ROM: it unpacks 16 piece-art images (one per piece kind), builds the display blocks from them, builds the maps from the map field, builds the checkpoint lists (176 checkpoints when the circuit has 45 or more pieces, else 88) by walking the circuit, loads one fixed collision cell pattern set (imp_079), and takes the five handling words from the options. No direction-map writer is in the kit code (code_00266E, code_001978). [hypothesis: P107, code_001978, code_00266E, kit_race_setup, ram_FFD672, ram_cp_count, imp_079]
- How the kit checks a circuit (Test Course, and silently before a saved course is raced): the 16 x 16 piece map is unpacked to one byte per square, the check finds the start square (piece 0) and follows the track from it, first upwards, square by square. Pieces 1, 7 and 8 can be crossed going up or down, 2, 7 and 8 going left or right; piece 10 is a straight whose way depends on its art variant (0 and 1 across, 2 and 3 up and down); pieces 3 and 4 are the two diagonal turns (3 turns up into right and left into down, 4 turns up into left and right into down, each also the reverse way); piece 14 is one-way, its art variant giving the direction (0 up, 1 down, 2 right, 3 left), and the track then jumps over any piece 6 squares after it. The circuit is closed when the walk comes back into the start square from below; it is legal at 24 to 88 squares, and that count is the length Test Course shows. A piece that does not connect, leaving the 16 x 16 map or going the wrong way through piece 14 stops the check with a message, and the piece palette reopens with the map cursor on that square. [hypothesis: kit_circuit_check, code_00266E, ram_FFED24, ram_FFEDCA]
- The kit's checkpoints: the same walk then lays checkpoint lines across the track, one on the start square and one to four on each other square, spread so that the numbers run evenly up to 88, or 176 when the circuit has 45 squares or more. Straight squares get lines straight across the track, 32 px apart; diagonal squares get diagonal lines. Each line carries the course progress word: the checkpoint number and the direction of travel in eighths of a turn (0 up, 2 right, 4 down, 6 left, odd values on the diagonals). The lines go into three lists (lines across up-and-down track, across left-and-right track, diagonal), each sorted by position, packed one after the other into ram_cp_list_buf behind two words that say where the second and third lists start; ram_cp_lists points there. [hypothesis: kit_cp_build, ram_cp_list_buf, ram_cp_lists, ram_cp_count, code_00266E]
- Jump records: each piece 14 on the circuit also gets a 14-byte record in a list at ram_FF97DC (two checkpoint numbers, a line across the track just before the piece, the progress word), and a piece 6 after it raises the record's second number to about six past the piece; what reads this list in a race is open (a reader census on a kit race with these pieces would settle it). [hypothesis: kit_cp_build, ram_FF97DC, ram_FFD6D6]
- The editor works on small maps: one 32 px block per square, 18 x 18 blocks with a one-block border (width and height words 18 in the maps header), block n drawn from the art of piece kind n; placing a piece writes it into the course record and into those maps at once. There is only one start (piece 0) and one piece 15: placing either turns the old one into piece 5. Button C on the 4 x 4 piece palette steps that kind's art variant (2 bits per kind, four bytes from ram_FFEDCA) and reloads the art. [hypothesis: kit_edit_maps, ram_maps, ram_FFEDCA, code_00266E]
- The race-size maps (72 x 72 blocks) are built by kit_race_maps, called from the kit race setup after kit_cp_build and kit_piece_blocks (which builds the art and blocks, not maps). Neither code_00266E nor code_001978 writes an opponents' direction map. [hypothesis: code_001978, kit_race_maps, kit_piece_blocks, kit_cp_build, ram_dir_map]
- Kit races have no computer cars, so nothing steers by a direction map: in the Test Course and in kit Single Race 2 Player and 3 Player, cpu_drive_p2, cpu_drive_p3, cpu_drive_p4, cpu_steer, dir_map_read and fn_041f74 ran 0 times (a challenge race control: cpu_steer 368 and the drivers about 200 times in 200 frames). The race-frame driver calls (code_0045CE) run the computer drivers only in rule mode 1 on in-use slots; the Test Course is rule mode 1 with slots 1-3 unused (cars 1-3 parked), kit Single Race sets the rule mode to the player count with only the human slots in use. Filling ram_dir_map with heading 01 every frame (the P094 test) changed nothing in the Test Course. [confirmed: P158, P160, code_0045CE, cpu_drive_p2, cpu_steer, dir_map_read, fn_041f74, ram_rule_mode, ram_dir_map]
- Kit Single Race 4 Player and 4 Player Teams were not run; by the same rule-mode test they have no computer cars either. [hypothesis: P158, code_0045CE, ram_rule_mode]
- In a kit race ram_dir_map is scratch: the setup's writers over decrunch_buf and ram_dir_map (FF0100-FF15FF) are kit_cp_build, the checkpoint-line writers fn_003d70, fn_003ea6, fn_00403e, fn_0041f4, fn_0043aa and fn_004560, and last the piece-art unpacking (imp_decrunch, fn_03544a), so it holds the last unpacked piece-art image; nothing writes it in race frames and nothing reads it. [confirmed: P159, P158, t44wtc_20261016T125716, t44k3w_20261016T125823, t44tc_20261016T125427, kit_cp_build, imp_decrunch, fn_03544a, decrunch_buf, ram_dir_map]
- Kit race maps: 72 x 72 blocks, the 16 x 16 squares of 4 x 4 blocks inside a 4-block border of display block 60 hex with collision code 22 hex (the same as piece 6). A square of kind k shows the blocks 16k to 16k + 15 (piece 15 shows piece 5's); its collision blocks are 0 for kinds 0-5 and 15, 22 hex for kind 6, one 16-byte layout each for kinds 7 and 8, and one of four layouts chosen by the art variant for kinds 9-14. The second map layer holds 50 hex under every square except kinds 6 and 10. A kind-10 square spills its edge blocks (collision 23 hex) into neighbouring squares of kinds 0-7: sideways for variants 0 and 1, up and down for 2 and 3. [hypothesis: kit_race_maps, ram_maps, ram_FF1A04, ram_FF574C, code_001978]
- Kit piece art: each piece kind has a compressed tile image of its own (pointer list dat_03CBD0); the art variant chooses a 16 x 16 tile quarter of it (128 x 128 px) and one of four 16-byte block layouts (dat_03CC10), which builds the kind's 16 blocks from those tiles or repeats a block already built. Tiles are numbered from 1 in VRAM; empty tile-map entries get filler tiles (0 for kinds 6 and 10). Kind 15 takes its quarter from kind 6's variant, and its last block image is also kept in RAM with a copy shifted one pixel (ram_FF9A2C, ram_FF940C). [hypothesis: kit_piece_blocks, code_001978, dat_03CBD0, dat_03CC10, ram_FF9A2C, ram_FF940C]
- Kit race setup values: the half-scale flag 0 and the switches ram_FFEC08, ram_FFEC0A, ram_bounce_sw and ram_FFEC6A 1; collision cell patterns from dat_059E26; with 176 checkpoints the progress limits 14 and 162, with 88 the limits 28 and 148; cars 0-3 in a 2 x 2 group 40 px apart at the first course-start square of the map field (x 160 + 128 x column, y 192 + 128 x row); course record entry 66; the position of a piece-15 square into ram_FFD4EE and ram_FFD4F0 (2560, 2560 without one). [hypothesis: kit_race_setup, code_001978, ram_cp_count, ram_cp_ahead_max, ram_cp_wrap_hi, ram_FFD4EE]
- The half-scale flag store of the kit race setup is the only write of the flag in a kit race (pc 001ADA, value 0, once at the setup); the kind-5 art variant picks the ground art of the whole course (four ground sets, none a pool table). [hypothesis: P111, P112, kit_race_setup, ram_half_scale_flag, ram_FFEDCB]
- Why kit squares draw black at half scale: the black is the backdrop colour (CRAM colour 0 = 0000, VDP register 7 = 00) showing where plane A is transparent, because at half scale the drawer never writes plane B, which holds the kit's ground. With the flag forced to 1 (P111 inputs, Test Course) plane-B VRAM write commands were 0 against 94 at setup and 170 in the race for the base, plane B was left 1888 of 2048 entries tile 0, and 28708 of 31855 black pixels had both planes transparent (base: none). Setting register 7 to red turned 15778 of 18992 black pixels red and changed no other pixel; the 3214 left are opaque black art. [confirmed: P156, P157, ram_half_scale_flag]
- Where the half-scale black falls: the 4-block border of display block 60 hex outside the map field (13664 px, all on tile-0 plane-A entries); inside the field, transparent pixels of nonzero tiles on kinds 2, 6, 9, 10, 12 and 13 and tile-0 entries on kinds 4, 5, 6, 11 and 13. These are pixel counts by square, not a probe of the tiles themselves (whether the half-scale drawer keeps each block's top-left 2 x 2 entries is not probed). [hypothesis: P156, kit_race_maps, kit_piece_blocks]
- EEPROM saves: eeprom_save is called from eight places (code_010EE2 and the season race code fn_00143c among them); before the sums it packs the 16 records of 12 bytes at ram_FFF69E into 5-byte records of the first EEPROM block. After a won head-to-head season race fn_00143c keeps the highest race number per driver, in those records in game type 1 or as the number - 10 in the 6-byte records at ram_FFF75E otherwise, and saves only when one rises. [hypothesis: eeprom_save, fn_00143c, code_00143C, code_004D34, ram_FFF69E, ram_FFF75E, ram_eeprom_image]
- Kit slot preview (the course preview screen with ram_FFECF8 set): the slot's 147 bytes are copied into the course record and checked with kit_circuit_check (result in ram_FFED30); a legal circuit gets its checkpoint lists (kit_cp_build) and its map on the preview, an illegal one the text Illegal Track instead. A name of 16 spaces marks an empty slot (ram_FFEAB2 = 1): Empty as the course line and a message instead of the map. The slot's vehicle byte (+142) picks both the preview picture (dat_03B533) and the vehicle class line (dat_03B53D, the same class texts as the ordinary courses); a non-empty slot also shows the five attribute labels and the slot's values (fn_011af0). [hypothesis: code_00BC1A, code_00B25C, code_00BE02, ram_FFECF8, ram_FFED30, ram_FFEAB2, dat_03B533, dat_03B53D]
- Record structs: the course record is struct kitcourse (map field +10, 128 bytes; art variants +138, 4 bytes; option bytes +142 to +146), typed on ram_kit_course; an EEPROM course slot is struct savedcourse (the 147-byte record, its byte sum at +147, a zero byte at +148), typed on ram_saved_courses, the first of nine. [hypothesis: ram_kit_course, ram_saved_courses, kit_race_setup, eeprom_save, P102]
- Cold-start save check: each of the nine slots is good only when the byte sum of its 147 bytes is nonzero and equals its first sum byte; a bad slot, an all-zero (empty) one included, runs the save header reset fn_0355b6 (which also clears ram_FFEEA6) and is refilled, the first slot with dat_043D12 and the second with dat_043DA6, the others cleared. The full reset fn_03569a fills them the other way round (dat_043DA6 first), so a repaired first or second slot gets the other default course: a likely original slip. [hypothesis: code_0002FA, fn_0355b6, fn_03569a, dat_043D12, dat_043DA6, ram_saved_courses, ram_FFEEA6]

Located: code_001978 (kit race setup kit_race_setup, art kit_piece_blocks, maps kit_race_maps), code_00266E (piece palette, map editor, circuit check
kit_circuit_check, checkpoint lists kit_cp_build), code_010EE2 (kit menu, edit menu, name, vehicle and attribute editors, save and load, password encoder, entry and decoder), code_00B25C (slot copy), code_004D34 (eeprom_save), code_005426 (EEPROM image, checksums,
transfer), code_00143C (season race-number records); RAM ram_kit_course (course record), ram_FFED24 (circuit length), ram_FFEDCB to ram_FFEDD2 (options),
ram_eeprom_image (EEPROM image), ram_saved_courses (slot 1), ram_FF9D2C (password characters); table data_03D9FA (kit vehicles);
port eeprom_data_in; probes P100, P101, P102, P107, P111, P112, P156, P157, P158, P159, P160.

Open questions (what would settle each): what reads the jump records at ram_FF97DC (a reader census on a kit race with
pieces 14 and 6); whether entering a password rebuilds the same record, as the decoder reads (enter a displayed
password and compare ram_kit_course); whether kit 4 Player and 4 Player Teams races have computer cars (an exec tap
on cpu_steer in those races); which tiles of a kit block the half-scale drawer keeps (a tile-level check of the P156
variant); the weather byte's values beyond 3 and 4.

### Vehicle and track tables

Answer: every parameter is per course. The game has no per-vehicle parameter table: the handling words sit in the
course record, and a vehicle is only its art (a vehicle record chosen per course; the Mini Micro course carries its
own small version of the pool-table car). Menus and modes reach courses through lists of course numbers: the
time-trial list, the challenge race records and the bonus races. Course names and class labels are text tables of
their own.

| Table | Region | Entry | Count | Index | Fields (kinds) |
|---|---|---|---|---|---|
| Course record pointers | data_04693E, records in data_046A46 to data_046B20 | 4-byte pointer to a 9-word record | 67 (66 set, 29 distinct records) | course number | acceleration, drag, grip, top speed, steering period, engine sound of slot 0, those of slots 1-3 |
| Vehicle art records | data_039128 | 16 bytes | 67 (19 distinct art blocks) | course number | art block pointer, two longs, a pointer kept in ram_FFD6E0 |
| Kit vehicle records | data_03D9FA | 16 bytes | 10 | kit vehicle byte | as above |
| Byte switches | data_04637A, data_0467EE, data_046336, data_046228, data_04626C, data_0462AF, data_045A14, data_045B22, data_0462F2 | 1 byte | 67 each | course number | half-scale (4 set), 88 checkpoints (39), wrap (50), block threshold (16 values), and five 0/1 switches for ram_FFEC08 (55 set), ram_FFEC0A (57), ram_bounce_sw (66), ram_FFEC6A (58), ram_FFEC68 (14) |
| Start line, initial view | data_0464CA, data_0466E2 | 8 and 4 bytes | 67 | course number | four position words; two position words |
| Time-trial list | data_0452C5 | 1 byte | 27, then 22 more and an end mark | list index FFEAFB | course number |
| Challenge race records | data_04454C | 14 bytes | 26 | race number ram_FFD718 | course number word, pointer to the computer cars' per-race words (offset 10) |
| Course names | data_0454A8, data_0454A9 | length byte + 8-15 characters | 65 | walked in order | text |
| Class labels | data_03AA1A | 4-byte pointer to a length-prefixed string | labels among other menu strings | label number ram_FFE80C | text |

- The course record has nine words: the five handling words (section Vehicle handling) and four sound numbers copied to ram_FFE682 to ram_FFE688; every load read exactly these nine words through the pointer of data_04693E. [confirmed: P103, t10dc_pool_20261013T223302, t10dc_bc_20261013T223305, t10dc_ferry_20261013T223308, t10w_pool_20261013T224309, t10w_bc_20261013T224315, t10w_ferry_20261013T224320, data_04693E, ram_FFE682]
- The vehicle a course is raced with is chosen by its 16-byte vehicle record (data_039128 at 16 times the course number): giving Ball Chase the record's art block of Pool Slalom made the car appear with the small Pool Slalom car art and changed nothing else. [confirmed: P106, data_039128, fn_03f124, ram_FFD6E0]
- 19 distinct vehicle art blocks serve the 67 course numbers; the kit offers 10 of them through its own records; Pool Slalom and Ball Chase use different art blocks for the same white prototype (5,030 against 7,590 bytes). [hypothesis: data_039128, data_03D9FA, P103]
- Handling is not tied to the vehicle: the same white prototype has top speed 512 on Pool Slalom and 448 on Ball Chase (section Vehicle types), and the kit sets the handling from its options whatever vehicle is chosen. [hypothesis: data_04693E, code_001978, P057]
- Time-trial list: 27 course numbers, and the course select wraps its index at 27; the 22 bytes after the list are further course numbers followed by an end mark, which is why poked indices 27-48 show unlisted courses and index 49 or more resets the game (T1). [hypothesis: data_0452C5, code_00143C, code_00C998, P108]
- Challenge races: 26 records of 14 bytes hold a course number and a pointer to the computer cars' nine words per car (section Difficulty); the bonus races use course numbers 55 to 59 (55 plus a counter of 0-4). [hypothesis: data_04454C, code_00102E, code_0012B4, ram_FFD718, ram_FFEC36]
- Course names: 65 length-prefixed strings of 8 to 15 characters, read by walking the strings one by one when the course select shows a course. [hypothesis: P108, data_0454A8, code_00BE02, code_00C84C]
- Class labels (Pro, Midi Mayhem, Turbo, Turbo Pro, Short Spin, Mini Micro) are length-prefixed strings reached through the pointer table data_03AA1A by a label number in ram_FFE80C; the label number is the fourth byte of the course's 4-byte entry of dat_04532E, stored in ram_FFE80C by the course preview setup and printed as the race line of screen kind 4. [hypothesis: P108, data_03AA1A, code_00BE02, code_00BC1A, ram_FFE80C, dat_04532E]
- Course preview tables, one entry per course number: dat_04532E (4 bytes: preview picture number into the pointer table dat_04543A, two bytes kept in ram_FFE808 and ram_FFE80A with no absolute reader found, class label number), dat_045A58 (x and y offset of the preview map and its items), dat_045ADE (largest map move of a marker or outline step, 0 = no limit), dat_045B66 (vehicle class text, such as Open Top or Formula 1, through the pointer table dat_045BAA). [hypothesis: code_00BC1A, code_00B25C, dat_04532E, dat_045A58, dat_045ADE, dat_045B66]

Located: data_04693E (course records), data_039128 (vehicle records), data_03D9FA (kit vehicles), byte tables
data_04637A, data_0467EE, data_046336, data_046228, data_04626C, data_0462AF, data_045A14, data_045B22, data_0462F2;
data_0464CA, data_0466E2; lists data_0452C5, data_04454C; text data_0454A8, data_03AA1A; code code_01CE34,
code_03F09C, code_00143C, code_00C998, code_00102E, code_00BE02; RAM ram_FFD672, ram_FFE682, ram_FFD6E0,
ram_FFD718, ram_FFE80C; probes P103, P106, P108.

Open questions (what would settle each): whether the class label number of dat_04532E matches the shown label on
every course (a capture of the race line on courses of two labels); what ram_FFE808 and ram_FFE80A feed (a reader run
on the course select); what the two longs of a vehicle record hold (a reader run of
the record during a load).

### Sound cues

Answer: the 68000 never plays sound itself. It appends short commands to a mailbox in the sound processor's (Z80's)
RAM: a 256-byte ring at A01E00 with a write index at A01F03. Each command is one command byte and up to three
parameter bytes, written while the 68000 holds the Z80 bus. Game events use one command, "play sound n" (command 04,
then the number, then FF), through one entry routine. The player car's engine sound is started with the same command,
its number taken from the course record (it follows the vehicle), and its pitch is a separate command sent every race
frame with three parameter bytes that follow the car's speed. Menu tunes and jingles are requests from the screens.

| Moment (three course loads, P104) | Requests seen (number in hex) |
|---|---|
| course select: cursor move, confirm | 87, 88 |
| race confirmed (load begins) | music command 0E with FF, then 15 |
| race start | the player car's engine sound: 03 on Pool Slalom and Ball Chase, 00 on Ferry Fiasco (the record's sixth word, P117) |
| race-start countdown | AA, AA, AB, about 30 frames apart (15, 45, 74 frames after the engine sound request) |
| each race frame from the start | engine command 18 with three bytes (one value set while idle, 71 sets in 220 frames of throttle) |
| events (sections Lap detection, Ramps and airborne, Pickups and hazards) | lap 5A, first lap under the target 89, ramp 6A, bump 6B, landing 6D, 55, 86, slow 4F, slippery 7B, 7C, bounce 50, 4A, objects 53, 54 |

- The mailbox: to send a command the 68000 requests the Z80 bus (fn_016de6, z80_busreq), reads the index byte at A01F03, writes the command byte and its parameters into the ring at A01E00 + index (the index wrapping at 256), stores the new index at A01F03 after each part and releases the bus (fn_016dfa); every one of 304-313 commands per run followed this pattern, the only 68000 writes to that part of Z80 RAM. [confirmed: P104, t10snd_pool_20261013T223415, t10snd_bc_20261013T223417, t10snd_ferry_20261013T223420, z80_cmd_ring, z80_cmd_index, fn_015830, code_016DE6]
- Sound requests for game events go through code_0156B6: unless the flag ram_FFEBEA is set or ram_FFEC12 is clear, it sends command 04 with the request number and FF (fn_015766); all seven requests per run in P104 had this form. [confirmed: P104, t10snd_pool_20261013T223415, t10snd_bc_20261013T223417, t10snd_ferry_20261013T223420, code_0156B6, code_0156C2, ram_FFEBEA, ram_FFEC12]
- The engine sound of the player car, not a course tune: the request carrying the sixth word of the course record (ram_FFE682; 3 on Pool Slalom and Ball Chase, 0 on Ferry Fiasco) is sent by fn_00596a, the engine routine of slot 0, in the race's first frame; when slot 0 was forced out of its running condition for 60 frames the routine sent command 0E with that word at once (from 00599C, its stop call), command 18 stopped, and the request 04 00 FF came again from 0059B6 when it was released. A static read of the 66 course records gives 5 values of the word over 19 vehicles, and 65 of 66 courses carry their vehicle's usual value (course 42 differs): the word follows the vehicle. [confirmed: P117, t32var_20261015T145159, fn_00596a, ram_FFE682, data_04693E]
- Race-start countdown: requests AA, AA and AB about 30 frames apart, the last at the start, in all three runs. [confirmed: P104, t10snd_pool_20261013T223415, t10snd_bc_20261013T223417, t10snd_ferry_20261013T223420]
- Engine sound: command 18 with three parameter bytes is sent once per race frame from the race start (fn_015860); its bytes stayed fixed while the car stood and took 71 different values in 220 frames with accelerate held, so they follow the car's speed. [hypothesis: P104, t10snd_ferryB_20261013T223452, fn_015860]
- Command 0E with FF is sent at the start and at the end of every load (silencing before the next tune is the likely meaning). [hypothesis: P104, fn_0157cc]
- The code holds further commands not seen in these runs: 02 (three bytes), 06 (two), 0C (one), 1A (two), and direct writes to two Z80 RAM bytes (fn_0158d0). [hypothesis: code_0156CE, code_015800, code_0158A2, code_0158D0]
- fn_0156ce sends command 0E with each of the four engine sound words ram_FFE682 to ram_FFE688 whose flag (ram_FFE68A to ram_FFE690, in the same order) is set, clearing the flag, then 0E with FF; it also clears ram_FFD74C, the looping-sound flag of the course hooks. This is the 0E with FF seen at the start and end of every load. [hypothesis: code_0156CE, fn_0156ce, fn_0157cc, ram_FFE68A, ram_FFD74C, P104]
- Command 02 with three parameter bytes (the low three bytes of D2, lowest first) is sent by fn_01572e, command 04 with two (D0 then D3) by fn_015766; both hold the Z80 bus around the ring write. [hypothesis: code_0156CE, fn_01572e, fn_015766, fn_015830]
- Engine sounds, tunes and effects share command 04: engine sounds are small numbers (0 and 3 seen), menu tunes and jingles 5 to 15 hex, effects 4A to AB hex; how the Z80 driver tells them apart is open (section Sound driver and music). [hypothesis: P104, P117, z80_driver]
- With accelerate held two more requests, 6C and 83 (and command 0E with 83), appeared near frame 1090 of the throttle run; their event was not identified. [hypothesis: t10snd_ferryB_20261013T223452]
- Screen sound requests through code_0156C2 in the menu flow: 5 at the main menu loop, 14 hex before each race of the tournaments, the multi-player single race and the TT Challenge, 11 hex after each tournament race, 14 hex before each Knockout match, 9 on the game over screen, 7 on the season end screen, 15 hex at power-on before the picture screen and at the start of each TT Challenge race; each follows the stop fn_0156ce. [hypothesis: code_0002FA, code_000D14, code_00A6C2, code_0156C2, fn_0156ce]
- TT Tournaments: sound 14 hex at the series start, before each course and after each run, 15 hex before each run, each after a sound stop. Menu pad steps: 88 hex for Start (a choice), 87 hex for an Up or Down step and for a Left or Right step where the screen allows it (fn_012d74, the reader of the main, game type, multi-player and TT Tournaments screens). [hypothesis: code_043232, code_0129DE, fn_012d74, code_0156C2]
- Engine sounds fn_00596a (each race frame, also in the bonus race): slot 0 runs while in view, outside a point pause and with its facing state below 20 hex; on its first running frame the record word ram_FFE682 is requested (flag ram_FFE68A), on every running frame command 18 carries D0 0 and a value from the speed (speed / 2 + speed / 4, above 100 a random 0-7 and a wobble word of dat_005BAA, plus 6 x height, at most 2FC hex), and when slot 0 stops running the flag is cleared with command 0E and that word. Slots 1-3 (by the rule mode) do the same with ram_FFE684-ram_FFE688 and the flags ram_FFE68C-ram_FFE690, command 6 (D1 0) at the start and command 1A each frame (speed / 4 + speed / 8 + a random 0-3 + height / 2, at most 7F hex). So the record word is requested again whenever slot 0 comes back into view: it is slot 0's running engine sound (P117). [hypothesis: code_00589A, fn_00596a, ram_FFE682, ram_FFE68A, fn_015860, fn_015800, fn_0158a2, P104]
- Direction sounds fn_005650 (each race frame): when no such sound plays, the first car (slot 0, then 1-3 by the rule mode) that is in view, on the ground, above speed 40 and has its drive direction 50 or more from its direction of motion starts a random one of 7E, 7F, 83, 84 hex (dat_005896); it plays until that car's difference falls below 20, it leaves view or the ground or slows to 40, then command 0E with the same number stops it. One such sound at a time. The 83 and command 0E with 83 of the throttle run fit this pair. [hypothesis: code_005638, fn_005650, dat_005896, ram_FFEC02, ram_FFEC06, t10snd_ferryB_20261013T223452]
- Button sounds fn_00589a: while ram_FFEC0A is set, a new press of control bit 5 requests 56 hex for pad 1, 63 hex for pad 2, 4B hex for pad 3 and 7D hex for pad 4, each only while that car is in view and its pad takes part by the rule mode; the same four numbers are course 29's random cues. [hypothesis: code_00589A, ram_FFEC0A, ram_FFD764]
- Course hook sounds: course 18 requests 60 hex at each shuttle start and when a car hits its objects (at most once per 10 frames, ram_FFD74C holding the frame count); courses 47, 48 and 49 hold looping sounds 69, 4C and 68 hex, started through 0x015694 and stopped with command 0E (0x0156AA): course 47's while an object moves, courses 48 and 49 while any of their items is on view. [hypothesis: data_01B42A, data_01C760, code_01C964, fn_0157cc, ram_FFD74C]

Located: code_0156B6 and code_0156C2 (event request entry), fn_015766, fn_0157cc, fn_015830, fn_015860 and the other
command senders in code_0156CE to code_0158D0, code_016DE6 (Z80 bus request and release); Z80 RAM z80_cmd_ring (ring),
z80_cmd_index (index); RAM ram_FFE682 to ram_FFE688 (engine sound numbers of slots 0-3), ram_FFEBEA, ram_FFEC12; probes P104, P117; runs
t10snd_pool_20261013T223415, t10snd_bc_20261013T223417, t10snd_ferry_20261013T223420, t10snd_ferryB_20261013T223452.

Open questions (what would settle each): whether the Z80 driver splits command 04 into tunes and effects by number
(the driver's command table, Group 7); which event sends 6C (a reader run on the throttle run near frame 1090; 83
matches the direction sound of code_005638); what commands 02 and 0C do (a code reading of their callers); why
course 42 carries a different engine sound word from its vehicle's other courses (its record against the vehicle's);
why slot 0 left its running condition near frame 987 of the Ferry Fiasco runs (a reader run of its in-view word).

## Group 7: The rest

### Menus and game modes

Answer: the front end is a chain of full-screen loops, each waiting for a pad choice and returning a number. The main
menu loop (lbl_000556, also where every mode returns) shows the main menu, stores its result in ram_FFE69A and
dispatches on it; each mode then runs its own loop of screens around the race, and the pad, the save chip and the
demo are shared by all of them. Every bullet below is read from the code (hypothesis); the menu paths the oracle
scenarios drive (one player, head-to-head, multi-player, the eight-car game, the kit) agree with them.

In plain words, the menu tree as the code builds it:

| Main menu item (value in ram_FFE69A) | What follows |
|---|---|
| 1 Player (0) | game type menu: Challenge, Head To Head, TT Challenge, League, the four Pro forms, TT Single Race; then the season loop of that type |
| 2, 3, 4 Player (1-3; 3 and 4 only with a J-Cart) | multi-player menu: Single Race, Tournaments (seven named series), TT Single Race, TT Tournaments, and once unlocked a fifth line of bonus courses |
| 4 Player Teams (4, J-Cart) | the multi-player menu with two teams of two |
| Extra Options: Party Play (5) | without a J-Cart Knockout; with one a list: Knockout, 8, 6 or 4 Player Share (value 7, the eight-car game) |
| Extra Options: Player Stats (6), TT Stats (9), Construction Kit (8), Clear Storage (10), Main Menu (11) | record pages, the kit (section Construction kit), wipe the save, back |

A season or series is the same few screens in a fixed order: driver select (and name entry), course preview with its
moving map, line-up, the race, the result, then standings, lives, game over or season end as the mode needs. All
menus step with Up and Down (sound 87 hex), choose with Start (sound 88 hex), and fall into the attract demo after
1536 frame counts without a press (section Attract mode). Results that last (records, driver names, unlocked
courses, kit courses) go to the save chip through eeprom_save.

Hidden and unreachable things found in the menus (details in the bullets): the eight-car game, which offers the
three otherwise unlisted half-scale courses 50, 53 and 54, is reachable only with a J-Cart (Extra Options, Party
Play, 8 Player Share); in the team game the multi-player menu lets the cursor reach an unlabelled third item (TT
Single Race), probably an original slip; eight fixed driver names unlock bonus courses when typed in the name entry;
a pad-held power-on test screen checks the J-Cart and the save chip (section Other findings).

- ram_FFE69A holds the main menu's result, read by the dispatch of the main menu loop; the scripted menu paths of the oracle scenarios set it as the table above says. [hypothesis: ram_FFE69A, code_0002FA, docs/ops/ops-tools.md]
- League season (fn_00c998, reached from the short entry of code_00102E): 16 drivers, 15 drawn at random plus the player's, sit in four-driver groups (slot table ram_FFE780: driver word and points word per slot); the player starts in the bottom group, group 3 in game type 3 (groups 1-3 used) and group 2 otherwise (groups 0-2). A pass is 4 races against the 3 group rivals, on the courses of the group's four 14-byte records in dat_04446C (course word, computer-car pointer at +10, the shape of the challenge records). [hypothesis: code_00C998, ram_FFE780, ram_FFE77E, dat_04446C, ram_FFEB20]
- League points per race: 4, 3, 2 and 1 by finishing order in the player's group; every other group gets a random 1-4 shuffle; each group is then sorted by points, a tie going to the player's driver. [hypothesis: code_00C998, ram_FFE780, fn_00d18e]
- After each pass the last of each group swaps with the first of the next (lower) group and the player's group number follows (ram_FFE77E). When the player tops the top group the season-end routine fn_00af58 runs and the pass count ram_FFEB24 (up to 31) is stored for the driver if smaller than the stored one (12-byte entries of ram_FFF69E in game type 3, 6-byte entries of ram_FFF75E otherwise, saved by eeprom_save); otherwise the best group reached is stored the same way and a yes/no choice (ram_FFE81C) starts another pass or ends the season. [hypothesis: code_00C998, ram_FFE77E, ram_FFEB24, ram_FFE81C, ram_FFF69E, ram_FFF75E]
- Time trial (fn_00d3b4, sets ram_FFD750): phases in ram_FFEAF2 (course select, records screen, race, result, next player); players 1 to ram_FFE778 race in turn (ram_FFEAF4), the result times are ranked for more than one player, and the end screen offers another course or leaving. This supports the time-trial reading of ram_FFD750, which the TT Single Race writer run measured (set by writer 00D3BA, P137). [hypothesis: code_00C998, ram_FFD750, ram_FFEAF2, ram_FFEAF4, ram_FFE778, ram_FFECDE, P137]
- Time-trial course select in fn_00d3b4: the list index runs from 0 to ram_FFEEA6 + 4 (highest race number reached + 4) and wraps both ways; list bytes 55 and 56 are skipped; kit courses (ram_FFED02) are chosen by their own index instead. [hypothesis: code_00C998, ram_FFEAFA, ram_FFEEA6, dat_0452C5]
- Time-trial records: each course has a race record and a lap record (two packed 6-byte records at ram_FFEF5C, ram_FFF5E0 for kit courses), time in the low 14 bits of the first word, 3A97 hex marking an empty record. The records screen choice sets ram_FFEAF8 to 1 (lap) or 3 (race); the other time of the run is voided to 5:00.00, and a clock stopped at 4:59.99 voids both. A smaller time replaces its record and is saved; ram_FFEAF6 holds which records are new (1 race, 2 lap, 3 both). Times are kept with the last hundredths digit made even. [hypothesis: code_00C998, ram_FFEF5C, ram_FFF5E0, ram_FFEAF8, ram_FFEAF6, eeprom_save]
- After a time-trial run 513 words at ram_FFDB78 are copied to ram_FFD774 with the course (ram_FFD76C), the time mode (ram_FFD76E) and the time (ram_FFF7D2), unless the same course and mode are stored with a time not above this run's, both times are void, or the course is 5, 18, 29 or 34. What the block holds is open (a writer run of ram_FFDB78 during a time-trial race would settle it). [hypothesis: code_00C998, ram_FFDB78, ram_FFD774, ram_FFD76C, ram_FFF7D2]
- The 513-word block is a run-length record of pad 1's control byte: code_006286 writes (byte, frames) pairs to ram_FFDB78 (index ram_FFDB76, at most 512 pairs, a run of 255 frames starts a new pair); in a later time trial on the same course and time mode it plays the stored pairs from ram_FFD774 into ram_control_p3, slot 2's control byte, else it takes slot 2 out of the race (ram_FFD024 0). The race setup starts slot 2 as kind 1 on slot 0's place in time trial, so the stored run races beside the player as a replay car. [hypothesis: code_006286, code_01CE34, ram_FFDB78, ram_FFDB76, ram_FFD774, ram_FFD770, ram_control_p3, ram_FFD024, ram_FFD750]
- Replay details (code_006286): a new pair starts when the byte changes or a pair reaches 255 frames, and recording stops after 512 pairs; playback compares the stored course with ram_FFECFA when ram_FFED02 is set (kit courses), else ram_FFD672, and a stored pair byte FF hex holds the replay car on no buttons. [hypothesis: code_006286, fn_006286, fn_0062da, ram_FFD76C, ram_FFED02, ram_FFD773]
- Lives screen (fn_00e59c, after a lost race and from code_000D14): the lives digit shows ram_FFE776 + 1 up to tick 19 (ticks of 8 frames) and ram_FFE776 from tick 20, dipping 8 px at ticks 8-9 and rising back from tick 20; the screen lasts until the tick passes 30, with sound 6. [hypothesis: code_00C998, ram_FFE776, ram_FFE774]
- Standings screen (fn_00dfda): one box per player with the driver, points and race count from the driver records (ram_FFF6A6); with ram_FFEB28 set it shows two player-record words instead and highlights the winner ram_match_winner, in the team game (ram_FFD68E) also the winner + 2. [hypothesis: code_00C998, ram_FFEB28, ram_match_winner, ram_FFD68E, ram_FFF6A6]
- Course preview screen (fn_00b25c before each season race, fn_00b264 inside the course select loops): one loop shows the course's picture, a text panel and a small map of the course; a new Start press leaves with step 0, Left with -1 and Right with +1 (both with sound 87), and the demo leaves when its frame count runs out or any control byte is set. The first call does the full setup, later calls of the same select only reset the palette. [hypothesis: code_00B25C, code_00BC1A, fn_00b264, ram_FFEB16, ram_FFEB08, ram_FFEBEA]
- Preview map: a 96 x 96 pixel bitmap in VRAM tiles from 4220 hex, drawn by the 68000 pixel by pixel (VRAM read, nibble mask, write back) at 1/32 of the course size from the checkpoint lists: the outline grows by one checkpoint line per frame and is redrawn in a loop, the start line (checkpoint 0) is redrawn every frame, and two marker items run round the checkpoints, one a checkpoint every 4 frames and one 3 checkpoints every 16 frames, over a lap of 176 or 88 checkpoints (the kit's own count on the kit course). A move of one map pixel along a checkpoint line is ignored and a move at or above the course's limit is refused, so the markers neither jitter nor jump. Bonus courses 55-59 show no map. [hypothesis: code_00B25C, fn_00b74a, fn_00ba9e, ram_FFECB4, ram_FFECB6, ram_FFECB8, ram_cp_list_buf, dat_045ADE]
- Preview panel, one player: the driver's name followed by S BEST, the game type title and the best result of that type, then LIVES with the lives word + 1. Titles by game type ram_FFEB20: 0 CHALLENGE, 1 HEAD TO HEAD, 2 TT CHALLENGE, 3 LEAGUE, 4 PRO CHALLENGE, 5 PRO HEAD TO HEAD, 6 PRO TT CHALLENGE, 7 PRO LEAGUE. Best result: CHAMPION at 10 (types 0-2) or 15 (types 4-6), NONE when unset, else the number and RACES; in the league types the best group (CHAMPION, PREMIERE, DIVISION n) and the number of SEASONS. With two to four players one line per player instead. [hypothesis: code_00BE02, fn_00c684, ram_FFEB20, ram_FFE778, ram_FFE776, ram_FFEEFA]
- Preview race line by the screen kind ram_FFEBB8: Challenge n (game type 0, races 1-10) or Pro Challenge n (races 11-25 counted from 1), the last one Final Race!; Contest n or Pro Contest n in head-to-head; Div g Race n or Prem Race n in the league; the course's class label for kind 4; TT Race n, Pro TT Race n, Round n or Final otherwise. The course name line alternates with the vehicle class line every 64 frames. [hypothesis: code_00BE02, code_00B25C, ram_FFEBB8, ram_FFD718, ram_FFE77E, ram_FFEBBA, ram_FFEB44, ram_FFC21C]
- Main menu loop (lbl_000556, also where the season loops end): lives reset to 2, the main menu fn_012688, then a dispatch on its result in ram_FFE69A: 0-3 for 1-4 Player (rule mode and player count = value + 1), 4 for 4 Player Teams (rule mode 4 with the team flag ram_FFD68E), and the Extra Options entries 5 Party Play (Knockout), 6 Player Stats, 7 the eight-car game (the 8, 6 and 4 Player Share entries of the J-Cart party list), 8 Construction Kit, 9 TT Stats, 10 Clear Storage, 11 Main Menu. [hypothesis: code_0002FA, code_012688, lbl_000556, ram_FFE69A, ram_rule_mode, ram_FFE778, ram_FFD68E]
- One player: the game type menu fn_012ff6 sets ram_FFEB20 0-8: Challenge and Pro Challenge go to the season at lbl_00104E, Head To Head and Pro Head To Head to code_0012B4, TT Challenge and Pro TT Challenge to the TT Challenge season, League and Pro League to code_00102E (the league season fn_00c998), TT Single Race to the time trial fn_00d3b4. [hypothesis: code_000D14, fn_012ff6, ram_FFEB20, lbl_00104E, code_0012B4, code_00102E]
- Two to four players: the menu fn_013496 offers Single Race, Tournaments, TT Single Race and TT Tournaments; a tournament is one of seven (ram_FFEC64 0-6: Rookie Races, Jets N Jumps, Mighty Mix, Monster Courses, Turbo Cars, Pro Tournament, Mega Comp), each with its own course list run in order and restarted at its end; Mighty Mix picks each race at random from four courses of the 27-course list, the group stepping with the race. [hypothesis: code_0002FA, fn_013496, ram_FFEC64, ram_FFEC62, ram_FFEB3C, ram_FFEAFA, dat_0452C5]
- Tournament series: each race is the course preview, the race, the point pause and the results points; the winner's record gets a win (in 4 Player Teams both records of the winning pair) and the standings follow. The series ends when a record reaches 3 wins (tournaments 0-4), 5 (Pro Tournament) or 7 (Mega Comp); the final order is the records by wins (team game: the winning pair first) on the results screen, then the standings, and the series can be played again. TT Tournaments go to fn_043232 instead. [hypothesis: code_0002FA, ram_FFE74E, ram_FFE754, ram_FFE75A, ram_FFE760, ram_FFE824, ram_FFE6AE, fn_00e746, fn_00dfda, fn_043232]
- Multi-player Single Race: a course select over the 27-course list (fn_0014ac) with race, results and standings, repeated until the player leaves; another menu value selects instead from a list built of the course pairs of dat_0452E0 whose bits are set in ram_FFF698, the bits the season records set, so these courses are unlocked by season progress. [hypothesis: code_0002FA, dat_0452E0, ram_FFF698, ram_FFED0E, ram_FFED1E, fn_001514, code_00143C]
- Both time-trial entries of the menus (TT Single Race for one player and for several) set ram_FFEEA6 to 22 first, so the time-trial course list always reaches its full length (index up to 26) when entered from the menus. [hypothesis: code_000D14, code_0002FA, ram_FFEEA6, fn_00d3b4]
- TT Challenge season (game types 2 and 6): races 1-10 or 11-25; per race the course preview, then a target screen (Beat This Time with the race's target time from dat_040DD0), the race in time-trial mode on race time, and a result screen: Well Done when the race clock (last digit made even) is smaller than the target at the first differing digit, Bad Luck otherwise, a tie included. A beaten target goes to the next race and its record (fn_000fce) and after the last race to the season end; a missed one costs a life (lives screen) and repeats the race, game over below 0 lives. [hypothesis: code_000D14, code_009CBA, fn_009cba, dat_040DD0, ram_FFD640, ram_FFED0A, ram_FFD718, ram_FFE776]
- Eight-car game (main menu value 7): the four-pad screen fn_04239a, the eight-car race, one more win in the winning pad's count ram_FFECA6 to ram_FFECAC (the numbers on the four-pad screen), then the four-pad screen again without its selection loop (ram_FFD74C 120), until it is left by its prompt. [hypothesis: code_000D14, fn_04239a, eight_car_race, ram_FFECA6, ram_FFECAC, ram_FFD74C, ram_match_winner]
- Party Play: the saved name table ram_FFEEFA is set aside for a separate party name table ram_FFEDD3 (outside the save image, emptied at a cold start) while fn_00a6c2 and fn_00a80e run; the player count is the party cursor + 4. [hypothesis: code_000D14, ram_FFEDD3, ram_FFEE33, ram_FFEEFA, fn_00a6c2, fn_00a80e, ram_FFEB42]
- TT Stats: seven pages of six rows, pages 0-4 the 27 courses of the time-trial list by number and name and pages 5-6 the nine kit slots (name or Empty), each row with the 3-lap and 1-lap records, time and six letters; a record time of 4.59.98 shows NO REC. Up and Down change page. [hypothesis: code_009CBA, fn_009e4e, ram_FFEF5C, ram_FFF5E0, dat_0452C5, dat_04548A, dat_03F526]
- Clear Storage: Delete All Records And Construction Courses? with No and Yes; Yes resets the driver records, the name table, both time-trial record lists, the season records and the kit course slots (with the save header) and saves. [hypothesis: code_009CBA, fn_00a2a2, fn_03569a, eeprom_save]
- Main menu fn_012688: with a J-Cart (or the byte ram_irq6_wblock at 7) the list is 1 Player, 2 Player, 3 Player, 4 Player, 4 Player Teams, Extra Options; without one only 1 Player, 2 Player, Extra Options. Extra Options lists Party Play, Player Stats, TT Stats, Construction Kit, Clear Storage, Main Menu (values 5, 6, 9, 8, 10, 11). Without a J-Cart Party Play returns 5 at once; with one it opens a party list: Knockout (5), 8 Player Share, 6 Player Share, 4 Player Share (all 7, with ram_FFED36 0, 6, 4). [hypothesis: code_012688, ram_FFEC9E, ram_FFE69A, ram_FFED36, ram_jcart_found, ram_irq6_wblock, dat_03B26C, dat_03C91A, dat_03A834]
- Main menu idle: a count goes up every 64 frame counts and any pad 1 byte clears it; at 24 (about 1536 frame counts) the demo fn_00a38e starts, the cursor kept in ram_FFEBCA; after a demo the wait is 3 steps until a pad is touched. [hypothesis: code_012688, ram_FFEBC6, ram_FFECB2, ram_FFEBCA, fn_00a38e]
- Driver select fn_00f0c2: each player in turn picks one of 16 drivers (cursor starting at 7); headings Please Select Your Driver for one player, Player n Select Your Driver for several, Red Team Player 1, Blue Team Player 1, Red Team Player 2, Blue Team Player 2 in the team game. Each pick asks Change Name? (No, Yes), the cursor starting on Yes while the driver still has its default name from dat_04440C; Yes opens the name entry. For the next player a faked pad byte moves the cursor off the taken driver to the nearest free one. [hypothesis: code_00F0C2, code_01062E, ram_FFE718, ram_FFE6F2, ram_FFE778, ram_FFE81E, ram_FFD68E, dat_04440C, dat_03B0E0]
- Driver select data: one 6-byte record per player from ram_FFE74C (driver word first), or, in the list mode ram_FFEBAC (Party Play, multi-player TT Single Race, kit and TT Tournaments entries), one word per player from ram_FFE72C; outside the list mode and rule mode 1 the pad that chose stores the player number in its word ram_pad1_player + pad x 2. [hypothesis: code_00F0C2, code_01062E, ram_FFEBAC, ram_FFE74C, ram_FFE72C, ram_pad1_player, ram_input_pad]
- Name entry fn_00fc54: a 6 x 5 grid of A-Z, !, space, delete and end; A, B or C writes the cell's letter while fewer than six are entered, Start or end finishes; a name left all spaces gets its old letters back. [hypothesis: code_00FC54, fn_01005a, ram_FFEEFA, ram_FFEB0C, ram_FFCF88, dat_03B06A]
- Driver select controls: the 16 drivers sit on a ring of rows 48 hex apart that moves 6 per frame; up or down (pad 1 bits 0 and 1, acted on while held once each move ends) steps the cursor and the ring, skipping drivers already taken by earlier players (shown as an empty item); Start alone (pad byte exactly 80 hex, new press) chooses with sound 88 hex. The cursor row blinks briefly after each move. [hypothesis: code_01008C, fn_01012a, fn_0101d4, fn_010276, ram_FFE718, ram_FFE714, ram_FFE6F4, ram_FFE716, ram_FFEAB0]
- Driver select record line: under the driver at the cursor an 8-letter line from the driver's records: one player RACE n for Challenge, Head To Head, TT Challenge and their Pro forms (CHAMP when the value is 10, 15 for the Pro forms), for League (and Pro League) CHAMP, PREM or DIV n in phase 1 and n SEAS in phase 2 of the three-phase cycle; several players n PTS in phase 1 and RACE n in phase 2; nothing for an empty record or TT Single Race. The line takes turns with the driver's name: for one player in Challenge and Head To Head on odd 64-frame counts, otherwise the name in phase 0. A completed record (the same CHAMP test) adds a two-item mark. [hypothesis: code_00F8B0, fn_00f8ca, fn_00fb40, fn_010276, ram_FFF69E, ram_FFF75E, ram_FFEB22, ram_FFEB18, dat_03B022, dat_03B03A]
- New name: once a name is entered (not left blank), the driver's records in ram_FFF69E and ram_FFF75E are reset to empty, and a name equal to one of eight fixed six-letter names sets one bit of ram_FFF698 (the first name bit 7), which unlocks multi-player courses like the season records do; then the save is written. Not with ram_FFECAE set. [hypothesis: code_00F8B0, fn_00fb94, dat_00FC24, ram_FFF698, ram_FFECAE, eeprom_save, fn_013496]
- Idle restart: 10000 frames without a pad 1 byte on the driver select or the name entry jump to the start-up code at 000200 hex (the name entry first restores the old name). [hypothesis: code_00F0C2, code_00FC54, ram_FFEC16]
- Knockout (Party Play): after the player count (4-16, fn_00a6c2) and the driver select in the list mode, the chosen drivers are drawn in random order into a bracket of 16, 8 or 4 slots (more than 8, 5-8, 4 drivers), draw n against draw 15 - n (with 8 slots 7 - n; with 4 slots 0 against 1 and 2 against 3); a driver with an empty partner goes through to the next round. Each round starts with one course select for all its matches; each match is a two-driver race in rule mode 2 and the winner moves on, until the final's winner goes to the season end screen with the title KNOCKOUT. A bracket screen with the names (dots for empty slots so far, question marks later) is shown before each match. [hypothesis: code_00A6C2, fn_00a80e, ram_FFEB42, ram_FFEB44, ram_FFEB4E, ram_FFEB6E, ram_FFEBAA, dat_03C73A, fn_0014ac, fn_00af58]
- Line-up screen fn_00ea9c before a race (tournaments, multi-player single race, seasons, Knockout, kit single race): the race's drivers (the player first and the three opponents in one-player games, else one per player record) get their pictures and slide in one by one, the upper row from the right and the lower from the left, over a background picked by the count (2 to 8); in a team game four palette words are set. Then READY!; after 60 frames a new pad 1 press ends it. [hypothesis: code_00EA9C, fn_00eab0, ram_FFE72C, ram_FFE76A, ram_FFE766, dat_03B106]
- Knockout pair on the line-up screen (ram_FFEBAC set): with routing mode 2 and all four pad words -1, the first driver's name and PRESS A AND START wait for a pad byte of exactly C0 hex, whose pad gets word 0; then the second driver's name and PRESS B AND START wait for exactly 90 hex, whose pad gets word 1, and the screen ends. Read with these prompts the control bits are 6 A, 4 B and 7 Start. [hypothesis: code_00EA9C, ram_FFEBAC, ram_pad1_player, ram_input_pad, dat_03B110, dat_03B126]
- Course preview player line fn_00c558: the driver's six letters, then on the line below WINS and a digit (D6) in a tournament (ram_FFEC64 not FF hex), else PTS and the word +8 of the driver's record without leading zeros. [hypothesis: code_00C558, ram_FFEC64, ram_FFF69E, ram_FFEEFA]
- Player Stats lines fn_00f6c0: NO STAT for a record value at the empty mark (FF hex, 20 hex in the byte records ram_FFF75E), CHAMPION at value 10 (15 in one byte-record case) in the line kind 1, CHAMPION below 1 and PREM DIVISION at 1 in the kind 2, else the number in one or two digits; the two time-trial counts of fn_00f816 match the driver's six letters and driver byte in each record. [hypothesis: code_00F6AE, ram_FFCFA6, ram_FFCFAA, dat_03ACA4, dat_03ACB6, dat_03ACC8, fn_00f816]
- Game over screen fn_00ad2c (lives below 0): Reached Race n: and the course name (n the race number + 1, less 10 in game types above 2), the driver picture and nine letters sliding in from the right; it ends after 1600 ticks of 8 frame counts, or from tick 30 when Start is held. [hypothesis: code_00A6C2, fn_00ad2c, ram_FFD718, ram_FFEB20, dat_03C7BC, dat_04454C, dat_04548A]
- Season end screen fn_00af58: the driver picture, CHAMPION and the game type title letter by letter (CHALLENGE, HEAD TO HEAD, TT CHALLENGE, LEAGUE, the PRO forms, KNOCKOUT in the list mode), with its own palette for the Pro and Knockout titles; a new Start press after tick 40 leaves it with the game type cleared. [hypothesis: code_00A6C2, fn_00af58, ram_FFE82E, ram_FFEB20, ram_FFEBAC, dat_03CACA, dat_03CAB8, dat_03CB0E, dat_03CAFE]
- Player Stats (fn_00f070 then the driver select in its Player Stats view): picking a driver shows its page: RACES for the first row (presumably Challenge), Head To Head and TT Challenge, DIVISION and IN SEASONS for League, the same for the Pro types, and two counts of the driver's time-trial records (fn_00f816, by name and driver); a choice leaves. [hypothesis: code_00F0C2, code_01062E, fn_00f070, ram_FFEC3C, fn_00f816, ram_FFEC42, ram_FFEC44, dat_03AD26, dat_03AD80]
- Game type menu fn_012ff6 (one player): nine lines Challenge, Head To Head, TT Challenge, League, Pro Challenge, Pro Head To Head, Pro TT Challenge, Pro League, TT Single Race; the cursor 0-8 is the game type. The idle wait and demo work as on the main menu (24 steps of 64 frame counts, 3 after a demo), the cursor and player count kept across the demo. [hypothesis: code_012FF6, fn_012ff6, ram_FFEBC6, ram_FFECB2, ram_FFEBCA, ram_FFEBCC, fn_00a38e]
- Multi-player menu fn_013496: a fifth line appears once any bit of ram_FFF698 is set (the season records set them); it is menu value 4, the unlocked course list, and its label depends on the number n of set bits: Specials, Bonus Specials, Super Specials, Overdrive, Free Play, Extra Play, Mega Play, Maximum Play for n = 1 to 8; the list then has 2n courses (ram_FFED0C). In the team game only Single Race and Tournaments are drawn; the item count still grows by one with unlocked courses, so a third, unlabelled item (value 2, TT Single Race) can be reached there, probably an original slip. [hypothesis: code_013496, fn_013496, ram_FFF698, ram_FFED0C, dat_043C26, ram_FFD68E, code_0002FA]
- Menu item pictures: on the main, game type and multi-player menus each item loads its own 16 colours into palette line 3 (ram_FFC2DA) and shows a picture with a small animation: short random-started animations whose counters run down every second frame count while the cursor is on the item (the 1-4 Player and Teams items, Head To Head), a two-hand dial for the time-trial items (32 positions per hand, the fast hand one step per 2 frames, the slow one per 64), falling items inside a window for Challenge and the tournaments, a bobbing picture for the multi-player items. Moving the cursor clears the animation words, so the new item starts afresh. [hypothesis: code_0129DE, code_012FF6, code_0132FC, code_013496, ram_FFC2DA, ram_FFEAB0, ram_FFEA30, fn_012fe0]
- Menu pad reader fn_012d70: a new Up press steps the cursor -1, Down +1, Start chooses; Left and Right give steps 2 and 3 only where a screen sets ram_FFCFAC first, and repeat while held after 40 calls, then every 4. The cursor wraps at both ends. [hypothesis: code_0129DE, fn_012d74, fn_012e90, ram_FFE6A2, ram_FFCFAC, ram_FFEAB0]
- TT Tournaments fn_043232 (multi-player menu, TT Tournaments, one of the seven tournaments): after a driver select in the list mode the series runs course by course from the tournament's list (80 hex a random course, FF back to the start); the laps (1 Lap or 3 Laps, ram_FFEAF8) are chosen once per series. Per course the course preview, then each player in turn (Press A And Start) races in time-trial mode against a time to beat shown in the race: 9:59.99 for player 1, else the best result of the players before. A stopped clock counts as all 9s and the last digit is made even; the results table shows each player's time (To Race before the run) and wins; the smallest time wins the course (a tie to the earlier player) and adds a win to that player's record. The series ends when a record reaches the target of fn_043ac6 (3, 5 or 7 by the tournament), then the standings and an offer to play again. [hypothesis: code_043232, code_0434DA, fn_043232, ram_FFEAF2, ram_FFEAF4, ram_FFECDE, ram_FFEAF8, ram_FFD640, ram_FFD646, ram_FFEB3C, fn_043ac6, fn_043934]

Located: code_00C998 (league season fn_00c998, time trial fn_00d3b4, records screen, standings screen fn_00dfda, lives screen fn_00e59c), code_00B25C, code_00BC1A and code_00BE02 (course preview screen, map and panel), code_0002FA (main menu loop and dispatch, tournament series, multi-player single race), code_000D14 (eight-car game loop, Party Play, game type dispatch, TT Challenge season), code_009CBA (TT Challenge target and result screen, TT Stats, Clear Storage), code_012688 (main menu lists), code_00F0C2 and code_01062E (driver select, Player Stats view), code_00F8B0 and code_01008C (driver name tiles, driver select record line, pad step, rows and sprites, new-name reset), code_010C8E (screen loads), code_00FC54 (name entry), code_00A6C2 (Party Play player count, Knockout, game over and season end screens), code_0129DE, code_012EFC and code_0132FC (main menu item pictures and setup, pad reader, cursor, dial), code_012FF6 (game type menu), code_013496 (multi-player menu), code_043232 and code_0434DA (TT Tournaments); RAM ram_FFE780 (league slots), ram_FFE77E (player's group), ram_FFEAF2 (time-trial phase); table dat_04446C (league races).

Open questions (what would settle each): what the Player Stats numbers count (the indexes of fn_00f6c0 against the driver records; a Player Stats capture); whether the slot-2 car replays the stored run (a time trial with a stored record, slot 2's position logged against the stored run's); what the standings numbers with ram_FFEB28 set are (a writer run of the player records' words +2 and +4); whether the lives screen takes the life before or after it is shown (a lost-race capture of ram_FFE776 around fn_00e59c); whether the unlabelled team-game item 2 really starts a team time trial (a scenario stepping to it).

### Sound driver and music

Answer: all sound and music are made by a separate small program, the sound driver, that runs on the sound
processor (the Z80) and plays the FM sound chip (YM2612) and its sample channel (DAC). At power-on the main processor
copies the driver, 5228 bytes kept in the cartridge, into the sound processor's 8 KB memory and waits for it to report
ready. From then on the driver loops on its own: it watches the mailbox's write index, takes each new command (play
sound n, stop sound n, engine sound values), and fetches its music, effect and sample data straight from the cartridge
through the sound processor's 32 KB window, which it moves to cartridge 020000-02FFFF hex. The second sound chip of the
Mega Drive (PSG) stayed silent in the run measured. In plain words: the game posts numbered requests, the driver does
all the playing, reading its scores and samples from one 62 KB block of the cartridge. Published credits name Tim
Bartlett for music and effects (and a Codemasters/Tim Bartlett sound driver for Micro Machines 2); the driver's own
format has no public description.

- Upload: z80_upload_driver copies 146C hex (5228) bytes from z80_driver into z80_ram from address 0, then polls Z80 byte z80_A01F0B until it is not zero (the driver's ready flag, likely). [hypothesis: z80_upload_driver, z80_driver, z80_A01F0B, z80_ram]
- Command reader: in the Ferry Fiasco run the driver polled the ring index z80_cmd_index from Z80 address 00EE (12754 reads in about 400 frames) and read every command byte of the ring z80_cmd_ring from one place, 00F5 (200 reads for 200 commands sent); each command then has its own parameter reader: 04 at 0C45 and 0C47, 0E at 0DE8, 18 at 0F0B, 0F23 and 0F25. [hypothesis: P118, t32base_20261015T145050, z80_cmd_ring, z80_cmd_index]
- Cartridge data: the driver set its window (bank register 6000h, nine one-bit writes per switch from Z80 1057-106F) 30088 times, always to bank 4 (cartridge 020000-027FFF hex, 22450 reads from 52 places) or bank 5 (028000-02FFFF hex, 269886 reads from 65 places); the reads span 02000A to 02FA85, the whole region sound_data and nothing past its end. So sound_data holds the driver's music, effect and sample data. [hypothesis: P118, t32base_20261015T145050, sound_data]
- Output: 616873 writes to the YM2612 ports, of which 285423 were sample bytes to the DAC (register 2A) from frame 0 on; no write to the PSG port. The frequent switches to bank 5 with its many reads fit samples streamed from the cartridge. [hypothesis: P118, t32base_20261015T145050]
- Which numbers are tunes: the menu flow requests 5 (main menu), 7 (season end), 9 (game over), 11 and 14 hex (after and before races) and 15 hex (power-on, TT Challenge runs), each after a full stop; these are the likely tunes and jingles (section Sound cues). Engine sounds use numbers from the course record (0 to 3 seen), effects lie from 4A to AB hex. [hypothesis: code_0156C2, fn_0156ce, P104, P117]

Located: z80_upload_driver (upload and ready wait), z80_driver (the driver image), z80_ram, z80_cmd_ring and z80_cmd_index
(mailbox), z80_A01F0B (ready byte), sound_data (the driver's cartridge data); probes P118 (Z80 census), P117, P104;
run t32base_20261015T145050.

Open questions (what would settle each): which bytes of sound_data are scores and which are samples (a Z80 read log
split by handler, or a disassembly of the driver from its 0C45 handler); whether the earlier reading of sound_data as
a video DMA source is right or a misattributed Z80 read (a 68000-only read tap on the region); which request numbers
are tunes (a Z80 trace of command 04 by number); what commands 02, 06, 0C and 1A do inside the driver (their handlers
in z80_driver); whether the PSG is used anywhere (a census on a menu and a kit course).

### Attract mode

Answer: there is no separate attract program. When a menu is left alone, the menu's idle count starts the demo step
fn_00a38e, which plays the next of a fixed cycle of 12 steps and returns to the same menu with the cursor kept. Eleven
steps are short demo races (a stored race record, 3 laps, 650 frames, the demo flag ram_FFEBEA set, which also mutes
the engine command); one step is the picture sequence: the title picture, the power-on animation of a car driving
across the screen items, and the credits. A pad press ends any part early.

In plain words: power-on shows the opening picture (fn_01393c) and the power-on animation once (section Other
findings); after that the game sits on the main menu, and 24 steps of 64 frame counts without a press (1536 counts,
about 31 seconds if the count steps once per 50 Hz frame) start a demo; after each demo only 3 such steps pass before the next, until a pad is touched.

- The attract sequence runs without input after the title; who steers slot 0 in a demo race (computer driver or a stored pad record) is open. [hypothesis: cov_attract_20261011T232135, fn_00a38e]
- Demo step fn_00a38e, run when a menu idles (main, game type, multi-player and kit menus: 24 steps of 64 frame counts, then only 3 until a pad byte is seen): a cycle of 12 steps (ram_FFEBEE, list dat_03C9D2), 11 of them demo races and one a picture step. A demo race takes a race record of dat_04454C (course, computer cars, the three opponents, the player's driver replaced by the record's substitute), 3 laps, shows the course preview for 120 frames and then, unless a pad left the preview, races in rule mode 1 for 650 frames with the demo flag ram_FFEBEA set. The picture step shows the picture screen fn_01393c for 151 frames, then fn_0429e2 and fn_0015c0, each skipped once a press has ended the one before. The pad words and routing are saved before and restored after. [hypothesis: code_00A38E, fn_00a38e, ram_FFEBEA, ram_FFEBEC, ram_FFEBEE, ram_FFECB2, dat_03C9D2, dat_04454C, fn_01393c]
- Credits fn_0015c0, the third part of the demo picture step: the heading Credits, then six pages of text records (first records Developed By, Written By, Graphics By, Music By, Play Testing By and Project Management By), each page cleared with seven blank lines and shown for up to 180 frames; any pad 1 bit ends a page's wait, so a held button runs through all six. [hypothesis: code_0015C0, fn_001668, dat_0016DA, dat_0016FE]
- Power-on animation fn_0429e2 (after the picture screen at power-on, and the second part of the demo picture step): 255 frames with no pad exit over a compressed picture. Eleven items (records from ram_FFD426) move in x by per-item step lists (dat_042EC6); from frame 81 a mover goes right 4 px per frame from x 112 to 372 with small hops from the path dat_042DCA, and items 5, 7 and 8 dip 4 px for the one frame it passes them; more items slide in from frames 185 and 193. Its sound step fn_042c72 plays a script (dat_042CE4) of race sound numbers (the direction sounds 7E and 7F, take-off 6A, bump 6B, 53, the pad 1 button sound 56) and sends frames 61-149 the slots 1-3 engine command 1A with 74 hex and a value from the mover's height, so it reads as a car driving across the items; nothing is sent while the demo flag ram_FFEBEA is set. [hypothesis: code_0429E2, fn_0429e2, fn_042c72, dat_042CE4, dat_042DCA, dat_042EC6, ram_FFEBEA]

Located: code_00A38E (demo step fn_00a38e), code_0429E2 (power-on animation fn_0429e2, sound step fn_042c72),
code_0015C0 (credits); RAM ram_FFEBEA (demo flag), ram_FFEBEC (demo frame count), ram_FFEBEE (step); lists
dat_03C9D2 (cycle), dat_04454C (race records); run cov_attract_20261011T232135.

Open questions (what would settle each): who drives slot 0 in a demo race (a demo run logging ram_control_p1 against
the computer-car steering of section Opponent AI); which race records the 11 demo steps take, in order (a demo run
logging ram_FFEBEE and ram_FFD672 over a full cycle, about 12 x 800 frames, beyond one MAME run's 7,500-frame cap, so
two runs from a saved state). Already answered by the code: the demo flag also blocks every event sound request
(code_0156B6, section Sound cues) and the engine command (fn_015860), so a demo race is silent apart from the
screens' own requests.

### Effects (sound effects and visual effects)

Answer: there is no general effect system. A sound effect is one numbered request to the sound processor (section
Sound cues: the event list, and section Sound driver and music: how a request is played). A visual effect is built
from the three things the Mega Drive offers without scaling hardware: extra sprites (the game's "items", drawn by
the overlay item drawer fn_03eea2), palette changes (the palette table ram_FFC27A rewritten, the screen then shown in
other colours), and rewrites of the course's map or tile art during the race. Each effect is a small routine run
every race frame, most of them per-course hooks (section Pickups and hazards) or the construction kit's weather.

In plain words, the effects found so far and where each lives:

| Effect | How it is made | Section, routine |
|---|---|---|
| Tyre marks (likely; laid while a car slides) | up to eight mark items aged in four steps, then removed | this section, fn_009b82 |
| Weather of kit courses: Rainy, Windy, Frosty, Lightning | 1: random sounds and scattered items, tyre marks off; 2: drifting objects with a sound; 3: other palette and low grip; 4: random white palette flash | this section, Construction kit, fn_01a4c8 |
| Splash on the sink courses (internal 6, 33) | an item and sound 85 hex every fourth count while a car sinks | Pickups and hazards |
| Bursts of falling items (course 61), animated scenery (courses 26, 47-49, 60, 62, 63) | items stepped by per-course tables, often with a looping sound | Pickups and hazards |
| Colour by place (course 60) | palette list chosen by how near the view is to four points | Pickups and hazards |
| Course pieces that change (courses 23, 27, 62; kit piece 15) | map bytes or tile art rewritten during the race | Pickups and hazards |
| Shaking objects before they open into holes | object drawn -1 to 2 px off in x | Pickups and hazards |
| Cars drawn higher with speed (courses 22, 24, 25) | height word set from speed each frame | Pickups and hazards |
| Engine, skid (direction) and button sounds | per-frame engine commands and one direction sound at a time | Sound cues |
| Power-on animation | items moved by step lists while a sound script plays | Attract mode |

- A per-call effect routine fn_01b168 (reached only through dispatch tables, no coverage) requests sound 5F when ram_FFC21C is 0 and, every 32 counts, a random one of 5B to 5E; it draws four items 97 at fresh random positions on each call; and it runs a palette flash: every 64 counts two random tests may request sound 0D and start the countdown ram_FFD4EE at 16, after which the palette table ram_FFC27A turns white (15 to 10 except 13, then 5 and 4), takes the list dat_047310 (9 to 6) and returns to the list dat_047352. [hypothesis: code_01B168, fn_01b168, ram_FFD4EE, ram_FFC27A, dat_047310, dat_047352, code_0156B6]
- Marks fn_009b82: the eight 6-byte entries at ram_FFD30C (filled by fn_04191e, which car_move calls past the slide bound ram_FFD6B2) are aged every other frame from 1 to 4 and cleared at 5, and drawn as items 4D-50 hex at their stage position while every car is on the ground (at half scale with halved distances); after the countdown nothing runs in rule mode 4 or with ram_FFD6B2 = 100 hex. [hypothesis: code_009B82, ram_FFD30C, ram_FFD6B2, fn_04191e]
- Kit weather (the course 66 race hook fn_01a4c8 by the low bits of ram_FFEDCF): 1 Rainy runs its own copy of the sounds and scattered items of fn_01b168 with another item and sets the slide bounds ram_FFD6B0, ram_FFD6B2 to FF00 and 100 hex (the value at which the marks routine does nothing); 2 Windy drifting objects with a sound; 4 Lightning a copy of fn_01b168's random palette flash with its own countdown ram_FFD502; 3 Frosty has no hook effect but forces the low-grip drag 1 and grip 2 and another palette at the race setup. fn_01b168 itself has no caller found (reached only through a dispatch table, never covered), so which course, if any, runs it is open. [hypothesis: fn_01a4c8, data_01A4C8, ram_FFEDCF, fn_01b168, ram_FFD502, ram_FFD6B2, code_010EE2]

Located: code_009B82 (marks), code_01B168 (rain-like effect without a known caller), data_01A4C8 (kit weather),
code_03EEA2 (item drawer), the course hooks listed in section Pickups and hazards; RAM ram_FFC27A (palette table),
ram_FFD30C (marks), ram_FFD4EE and ram_FFD502 (flash countdowns).

Open questions (what would settle each): whether the marks are tyre marks left when a car slides (a run on a slippery
square logging ram_FFD30C with the car's slide state); what the kit weathers look like and sound like (a kit race with
ram_FFEDCF set to 1, 2 and 4, snapshots and the Z80 ring tap); which course runs fn_01b168, if any (a dispatch-table
search for 01B168 hex); none of the visual effects above has been measured in a run yet,
except where its section cites a probe.

### Other findings

- Start-up code at 000200 hex (init): the standard Mega Drive set-up (licence write to the TMSS register when the version register reports a revision above 0, 24 VDP registers, VRAM fill, Z80 stub upload, 64 KB work RAM clear, CRAM and VSRAM clear, PSG silenced, Z80 held in reset), skipped when a control port word is already nonzero; both ways end in the power-on code 0002FA hex. The idle restart's jump to 000200 hex therefore normally skips the set-up. [hypothesis: init, init_table, z80_boot_stub, code_0002FA]
- Decompression: imp_decrunch_core decodes Imploder blocks backwards from the end of the packed data to the start of the output, in place when both start at the same address; match lengths 2-5 from short codes, 6-13 from three bits or any length from a whole byte; literal counts and match offsets each take one of three forms (short, middle, far) whose bit widths depend on the length class, the literal tables fixed in ROM (dat_0355A6, dat_0355AA) and the offset tables carried in each block's trailer; it returns -1 only when output and input both end exactly at their starts. [hypothesis: imp_decrunch_core, dat_0355A6, dat_0355AA]
- Power-on order: VDP and RAM init, frame-rate test, sound driver upload, J-Cart detection, random seed ram_FFC23A, the test screens fn_03d682 and fn_03d56a, then the picture screen fn_01393c for 251 frames, or 101 when the save header text is still in RAM (a reset); on a reset with the header present the EEPROM is not read again and the save in RAM, party names included, is kept. [hypothesis: code_0002FA, fn_01393c, ram_eeprom_image, ram_FFEEA2, ram_FFC23A, z80_upload_driver, jcart_detect]
- The game writes ROM address 000000 once, at about frame 595 after power-on, from a writer at 03F32E; its purpose is unknown. [hypothesis: code_03F278, t2w_challenge_20261013T165019, t2w_h2h_20261013T165027, t2w_pool_20261013T165035]
- Power-on test screen fn_03d682: when pad 1's control byte reads FF hex one frame after power-on, a test screen prints TESTING JCART, checks each half of the J-Cart port word with a fixed bit sequence (JCART 1 PASS or FAIL, JCART 2 PASS or FAIL), then TESTING NVR with the EEPROM routine fn_00545e (NVR PASS returns to the boot; any failure hangs on its message). Probably a factory test; a standard pad cannot give FF with Up and Down together. [hypothesis: code_03D682, fn_03d682, fn_03d8a6, fn_00545e, dat_03AFA4, dat_03B012]
- Course hooks: two tables of 67 longs, data_03691A and data_03680E, are indexed by the internal course number ram_FFD672 by two calls from code_0045CE, a nonzero long being jumped to. Batch B015 entries: course 1 fn_0182bc and course 18 fn_018424 (data_03691A); course 20 fn_01b936, 21 fn_01b9fa, 22, 24 and 25 fn_01acfc, 23, 28 and 52 fn_01bf72, 26 and 39 fn_01c6ca, 27 fn_01bc64, 29 fn_01bf7a, 30 fn_01afac, 62 fn_01ae44, 63 fn_01ad2c (data_03680E). The words from ram_FFD426 are scratch reused by each course's hook with its own layout. [hypothesis: data_03691A, data_03680E, ram_FFD672, code_0045CE, code_0182BC, code_01ACFC, code_01B936]
- Courses 62 and 63 play a looping sound (10 hex and A hex) while their animated scenery is on view, started on the first frame anything is on view and stopped with a sound command on the first frame nothing is; course 29 requests, every 8 frames while a stop word is clear, one of four cues (63, 4B, 7D, 56) when a signed random byte is below 60 (188 of 256 values). [hypothesis: fn_01ae44, fn_01ad2c, fn_01bf7a, ram_FFD74C, code_0156B6]
- Overlay item draw fn_03eea2: items are 16-byte records from ram_FFC37C (tile, width and height in tiles, attribute); an item up to 4 x 4 tiles is one sprite, a bigger one is cut into pieces of at most 4 x 4 tiles column by column; D3 bits 0-1 flip it in x and y (pieces reordered) and bit 4 sets the sprite priority bit; an x of exactly 0 is not drawn and x is held at 1E8 hex. Each sprite is appended by fn_03f04e to the list at ram_FFC242 with its link from the count ram_FFC240. [hypothesis: code_03EEA2, fn_03eea2, fn_03f04e, ram_FFC37C, ram_FFC242, ram_FFC240]
- Screen text print fn_0108da: a text record (position, run code, length, letters) becomes a tile stream in ram_FFE830 drawn by fn_010a4e into plane VRAM with the palette line ram_FFE77A and priority by ram_FFE802; with ram_FFE770 = 2 letters are two tiles tall, and the entry 0108B6 hex blinks the text, shown 20 of every 32 counts and blanked otherwise. [hypothesis: code_0108C2, fn_0108da, fn_010926, fn_010a4e, fn_0108e8, ram_FFE770, ram_FFE772, ram_FFC236]
