"""Small battle helpers for the emulator fix scenarios (faintcry, hitsound): make a Pokemon the lead, set a
party Pokemon's current HP, and play one battle turn. Ported (reduced) from the retired emu_guide0107 /
emu_open / emu_sweeps recipes."""
import emu_harness as E

POLL = 4                                   # frames between looks at the screen during a turn
PARTY_LIST = [((5, 197), (224, 208, 184)), ((250, 197), (224, 208, 184)), ((20, 362), (248, 248, 248))]
PARTY_SUBMENU = [((5, 197), (224, 208, 184)), ((20, 362), (56, 144, 224))]
SUBMENU_SHIFT = (128, 108)                 # forced switch: the party Pokemon's submenu, 'shift' button


def lead(h, species, level=100, moves=None, pp=None):
    """Generator Pokemon made the party lead (the old lead moves to its slot)."""
    mon = h.generate_pokemon(species, level=level)
    if moves:
        h.edit_party_mon(h.generated_slot, moves=moves, pp=pp)
    h.swap_party(0, h.generated_slot)
    return mon


def match(h, samples, tol=24):
    """True when every (x, y) -> rgb sample of the screenshot is within tol."""
    img = h.emu.screenshot().convert("RGB")
    return all(max(abs(a - b) for a, b in zip(img.getpixel(xy), rgb)) <= tol for xy, rgb in samples)


def set_party_hp(h, slot, hp):
    """Current HP of a party Pokemon (the harness re-encodes the party extension through the shared codec)."""
    h.edit_party_mon(slot, currentHp=hp)


def replace_fainted(h, nxt):
    """At the forced-switch party list: pick party slot nxt (and confirm its submenu)."""
    h.touch(*E.PARTY_SLOTS[nxt], frames=10, after=60)
    if match(h, PARTY_SUBMENU):
        h.touch(*SUBMENU_SHIFT, frames=10, after=30)


def turn(h, action, max_frames=4000):
    """One command (move slot 0-3) at the battle menu, then B through the messages until the command menu or
    the field is back; our fainted Pokemon are replaced from the party list. Returns 'menu', 'field',
    'no_menu' or 'stuck'."""
    if not h.run_until(lambda h: h.on_screen("battle_menu"), 2000, every=POLL):
        return "no_menu"
    h.touch(*E.BATTLE_BUTTONS["fight"], frames=10, after=40)
    h.touch(*E.MOVE_BUTTONS[action], frames=10, after=0)
    nxt = 2
    for i in range(0, max_frames, POLL):
        h.step(POLL)
        if h.in_field():
            h.step(60)
            return "field"
        if i > 60 and h.on_screen("battle_menu"):
            return "menu"
        if i % 60 == 0 and match(h, PARTY_LIST):
            replace_fainted(h, nxt)
            nxt = nxt % 5 + 1
            continue
        if i % 64 == 60:
            h.press("B", after=0)
    return "stuck"
