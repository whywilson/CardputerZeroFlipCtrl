#include "../main/scaler.hpp"
#include <cassert>
#include <cstdio>
int main(){
 uint8_t src[256*144]{};uint16_t dst[320*170]{};
 render_screen(src,dst,ViewMode::Fit);for(auto v:dst)assert(v==0);
 for(auto &v:src)v=255;render_screen(src,dst,ViewMode::Fit);const auto white=dst[0];for(int i=0;i<302*170;i++)assert(dst[i]==white);
 for(int y=0;y<144;y++)for(int x=0;x<256;x++)src[y*256+x]=x<128?0:255;
 render_screen(src,dst,ViewMode::Native);assert(dst[127]==0&&dst[128]==white);
 render_screen(src,dst,ViewMode::Fit);bool blended=false;for(int x=0;x<302;x++)if(dst[x]!=0&&dst[x]!=white)blended=true;assert(blended);
 render_screen(src,dst,ViewMode::Stretch);assert(dst[0]==0&&dst[319]==white);
 assert(view_width(ViewMode::Stretch)==320&&view_height(ViewMode::Stretch)==170);
 assert(next_view_mode(next_view_mode(next_view_mode(ViewMode::Fit)))==ViewMode::Fit);
 puts("PASS: black/white preservation, exact native pixels, smooth edge interpolation");
}
