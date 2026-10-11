# Two actual Options pages

User request, 2026-10-10: difficulty must be a second actual settings page,
reachable through visible footer arrows beside Confirm and Back. This supersedes
the held-L-only flow and custom-only teardown described in options-handoff.md.

Normal field-menu entry opens page1/2 with all seven native rows. Touch either
footer arrow or press L/R to change pages. Page2/2 contains ITEMS, SHARE and CAP.
The existing held-L entry still opens page2 for compatibility with diagnostics;
it is not required to discover or reach difficulty.

Both pages share one lifetime and one transaction. Native normal choice strings
and their draft values remain allocated while difficulty is visible. The private
difficulty draft also survives page changes. Confirm applies both sets of drafts;
Back or B cancels both. No page change writes the saved Options halfword. The
original native exit commits/cancels ordinary rows, including TEXT SPEED and
preview restoration; narrowed native setters preserve difficulty's owned bits.
Difficulty rendering/input does not execute ordinary setting previews. Returning
to the normal page redraws/previews its retained native choices as normal.

The arrows and labels use the existing game font. No new graphic asset is made.
One native Window(16 bytes) in resident BSS owns a96x24 footer buffer on heap38.
Its BG1 tile range634..669 follows native windows10..633 without overlap and is
below the1024-tile BG limit. Position(8,168) fills unused space left of the native
footer controls. The window is removed at the existing animation-wait hook,
before native window/BG-config destruction; the shared String is freed before
delegating to the original native exit. Native footer sprites7/8 are hidden on
both pages to avoid their baked-in labels overlapping font-based Confirm/Back.
Frame arrows5/6 and the normal outline retain their original behavior.

Source ABI review uses the fully guarded47-fix baseline ARM9 and overlay50:
AddWindowParameterized0201DC3C receives nine native AAPCS arguments; its stored
Window fields and allocation failure are checked before drawing. RemoveWindow
0201DD50 runs before the native BG config is freed. Existing native footer windows
are left(112,168) and right(176,168); Confirm is left and Back right on both pages.
The normal cursor restore021E5944 uses the retained native row index.

Sanitized shipping-C host tests cover touch/button switching, retained drafts,
shared Confirm/Back, conflict rejection, exactly-once cleanup and original codec
checks. A fresh native development probe passed the same flow, but all current
native UI captures and the independent draft/owner/window oracle must pass on the
final candidate. The release gate includes ui.page_navigation and visual review
of both pages and all five difficulty focus states. Prior native results do not
validate this changed resident payload.
