/* Shipping growth.c with ONLY native primitives mocked. Not ARM/gameplay proof. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "growth.h"
#include "policy.h"
#define BASE 0x02000000u
#define ROOT 0x02280000u
#define SETUP 0x02290000u
#define MON 0x022A0000u
static uint8_t ram[0x400000], saved[0x400000];
static DG_GrowthSnapshot snap;
static uint32_t present, eligible, award, defer, ceiling, gate, resolves, thresholds, natives, snapshots;
static uintptr_t resolved;
static const uint32_t raw[4]={13,26,1,0xABCDEF12};
static void w32(uintptr_t p,uint32_t v){assert(p>=BASE&&p<=BASE+sizeof(ram)-4);memcpy(ram+(p-BASE),&v,4);}
uint8_t dg_growth_test_read8(uintptr_t p){assert(p>=BASE&&p<BASE+sizeof(ram));return ram[p-BASE];}
uint16_t dg_growth_test_read16(uintptr_t p){assert(p>=BASE&&p<=BASE+sizeof(ram)-2);uint16_t v;memcpy(&v,ram+(p-BASE),2);return v;}
uint32_t dg_growth_test_read32(uintptr_t p){assert(p>=BASE&&p<=BASE+sizeof(ram)-4);uint32_t v;memcpy(&v,ram+(p-BASE),4);return v;}
const DG_GrowthSnapshot *dg_growth_snapshot(void){++snapshots;return present?&snap:0;}
uint32_t dg_growth_test_native_share(void){return 7;}
uint32_t dg_growth_test_native_reward_allowed(void){return gate;}
uintptr_t dg_growth_test_native_resolve(uint32_t id){assert(id>=1&&id<=6);++resolves;return resolved;}
uint32_t dg_growth_test_native_threshold(uint32_t species,uint32_t level){assert(species==4&&level==snap.cap_level);++thresholds;return ceiling;}
uint32_t dg_growth_test_native_eligible(uint32_t *amount,uint32_t *deferred,void *mon,const void *record){
 (void)mon;assert(record==raw);assert(snapshots==0&&resolves==0&&thresholds==0);++natives;*amount=award;*deferred=defer;return eligible;
}
static void reset(void){
 memset(ram,0,sizeof ram);snap=(DG_GrowthSnapshot){DG_CAP_ON,12,1,ROOT,1};present=gate=1;eligible=7;award=26;defer=0xDEADBEEF;ceiling=100;resolved=MON;
 w32(0x02255BAC,ROOT);w32(ROOT+0x10,SETUP);w32(MON,4);ram[MON-BASE+0x14]=1;w32(MON+0x18,90);
 natives=resolves=thresholds=snapshots=0;
}
static void check(uintptr_t mon,uint32_t want,uint32_t lookups){
 uint32_t a=0xBAD,b=0xBAD;memcpy(saved,ram,sizeof ram);DG_GrowthSnapshot ss=snap;uint32_t rr[4];memcpy(rr,raw,sizeof rr);
 assert(dg_growth_eligible(&a,&b,(void*)mon,raw)==eligible);assert(natives==1);assert(a==want&&b==defer);
 assert(thresholds==lookups);assert(!memcmp(saved,ram,sizeof ram));assert(!memcmp(&ss,&snap,sizeof snap));assert(!memcmp(rr,raw,sizeof rr));
}
int main(void){
 /* Positive/partial/zero/overlevel and UINT32_MAX: outputs before any consumer. */
 uint32_t currents[]={0,73,74,75,99,100,101,0xFFFFFFFF};
 uint32_t expected[]={26,26,26,25,1,0,0,0};
 for(unsigned i=0;i<8;i++)for(unsigned d=0;d<2;d++){reset();defer=d;w32(MON+0x18,currents[i]);check(MON,expected[i],1);}
 reset();award=0xFFFFFFFF;check(MON,10,1);
 for(unsigned id=0;id<256;id++){reset();ram[MON-BASE+0x14]=id;check(MON,id>=1&&id<=6?10:26,id>=1&&id<=6);assert(resolves==(id>=1&&id<=6));}
 for(unsigned bad=0;bad<17;bad++){
  reset();uintptr_t mon=MON;
  switch(bad){case 0:present=0;break;case 1:snap.epoch=0;break;case 2:snap.allowed=0;break;case 3:snap.flags=8;break;
   case 4:snap.root+=4;break;case 5:w32(0x02255BAC,ROOT+1);snap.root=ROOT+1;break;
   case 6:w32(ROOT+0x10,0);break;case 7:gate=0;break;case 8:snap.flags=0;break;case 9:snap.cap_level=0;break;
   case 10:snap.cap_level=101;break;case 11:mon=MON+1;break;case 12:mon=0xFFFFFFF0;break;case 13:resolved+=4;break;
   case 14:w32(0x02255BAC,0x023FFFFC);snap.root=0x023FFFFC;break;case 15:w32(ROOT+0x10,SETUP+1);break;
   case 16:mon=0x023FFFF0;break;}
  check(mon,26,0);
 }
 reset();eligible=0;check(MON,26,0);assert(!snapshots);
 reset();award=0;check(MON,0,0);assert(!snapshots);
 for(unsigned f=0;f<8;f++){reset();snap.flags=f;assert(dg_growth_share_enabled()==!(f&DG_SHARE_OFF));}
 reset();present=0;assert(dg_growth_share_enabled()==7);reset();gate=0;assert(dg_growth_share_enabled()==7);
 puts("PASS growth shipping wrappers: original-first/nonboolean result/deferred/raw preservation; partial/zero/overlevel/u32; all256 IDs; 17 guard bypasses; share fallback. EV callsite verified separately; no gameplay claim.");
}
