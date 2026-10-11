#include "caps.h"
#include "runtime.h"
#ifdef DG_CAPS_HOST_TEST
#define profile dg_caps_test_profile
#define vars dg_caps_test_vars
#define badge dg_caps_test_badge
#define flag dg_caps_test_flag
#else
#define profile ((uintptr_t (*)(uintptr_t))(uintptr_t)0x0202933Du)
#define vars ((uintptr_t (*)(uintptr_t))(uintptr_t)0x0204F859u)
#define badge ((uint32_t (*)(uintptr_t,uint32_t))(uintptr_t)0x02029429u)
#define flag ((uint32_t (*)(uintptr_t,uint32_t))(uintptr_t)0x0204F865u)
#endif
uint32_t dg_cap_resolve(uint32_t badges,uint32_t erika,uint32_t clair) {
    static const uint8_t ids[16]={0,1,2,3,5,6,4,7,8,9,10,11,13,12,14,15};
    /* Actual gym maxima stay distinct from the effective cap (D-2312).
     * Accumulate only through the earliest unfinished guide-order row:
     * later completed gyms never bypass a gap or raise its cap. */
    static const uint8_t maxima[16]={12,20,25,38,55,65,80,100,80,80,88,80,80,80,85,85};
    uint32_t cap=0;
    if (erika) badges|=1u<<3;
    if (clair) badges|=1u<<15;
    for (uint32_t i=0;i<16;++i) {
        if (maxima[i]>cap) cap=maxima[i];
        if (!(badges&(1u<<ids[i]))) return cap;
    }
    return 100;
}
uint32_t dg_cap_for_save(uintptr_t save) {
    uintptr_t p,v;
    uint32_t badges=0;
    if (!save || dg_runtime_save()!=save) return 0;
    p=profile(save); v=vars(save);
    /* Reader spans: profile badge bytes through +1F; flag1220 through +378.
     * Native getters, not raw guessed save offsets, resolve each predicate. */
    if (!dg_runtime_ram(p,0x20,4) || !dg_runtime_ram(v,0x379,4)) return 0;
    for (uint32_t i=0;i<16;++i) if (badge(p,i)) badges|=1u<<i;
    return dg_cap_resolve(badges,flag(v,1220),flag(v,209));
}
